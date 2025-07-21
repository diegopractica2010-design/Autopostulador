from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
import aiofiles
from datetime import datetime, timedelta
import json

# Importar modelos
from models import (
    UserProfile, UserProfileCreate,
    CVData, CVDataCreate,
    SearchFilters, SearchFiltersCreate,
    JobPosting, JobApplication, ApplicationStats,
    AIConfig, AIConfigCreate,
    JobPortal, ApplicationStatus
)

# Importar servicios
from services.scraper_service import ScraperService
from services.ai_service import AIService
from services.application_service import ApplicationService


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Autopostulador Laboral Chile", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Servicios
scraper_service = ScraperService()
ai_service = AIService()
application_service = ApplicationService(db)


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ====================== USUARIO ======================
@api_router.post("/user", response_model=UserProfile)
async def create_user(user_data: UserProfileCreate):
    """Crear perfil de usuario"""
    user = UserProfile(**user_data.dict())
    result = await db.users.insert_one(user.dict())
    return user


@api_router.get("/user/{user_id}", response_model=UserProfile)
async def get_user(user_id: str):
    """Obtener perfil de usuario"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserProfile(**user)


@api_router.put("/user/{user_id}", response_model=UserProfile)
async def update_user(user_id: str, user_data: UserProfileCreate):
    """Actualizar perfil de usuario"""
    updated_data = user_data.dict()
    updated_data["updated_at"] = datetime.utcnow()
    
    result = await db.users.update_one(
        {"id": user_id}, 
        {"$set": updated_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    updated_user = await db.users.find_one({"id": user_id})
    return UserProfile(**updated_user)


# ====================== CV ======================
@api_router.post("/user/{user_id}/cv", response_model=CVData)
async def create_cv(user_id: str, cv_data: CVDataCreate):
    """Crear CV para usuario"""
    cv = CVData(**cv_data.dict(), user_id=user_id)
    
    # Si es el CV por defecto, desmarcar otros CVs
    if cv.is_default:
        await db.cvs.update_many(
            {"user_id": user_id}, 
            {"$set": {"is_default": False}}
        )
    
    await db.cvs.insert_one(cv.dict())
    return cv


@api_router.get("/user/{user_id}/cvs", response_model=List[CVData])
async def get_user_cvs(user_id: str):
    """Obtener todos los CVs del usuario"""
    cvs = await db.cvs.find({"user_id": user_id}).to_list(100)
    return [CVData(**cv) for cv in cvs]


@api_router.get("/cv/{cv_id}", response_model=CVData)
async def get_cv(cv_id: str):
    """Obtener CV específico"""
    cv = await db.cvs.find_one({"id": cv_id})
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    return CVData(**cv)


@api_router.put("/cv/{cv_id}", response_model=CVData)
async def update_cv(cv_id: str, cv_data: CVDataCreate):
    """Actualizar CV"""
    updated_data = cv_data.dict()
    updated_data["updated_at"] = datetime.utcnow()
    
    result = await db.cvs.update_one(
        {"id": cv_id}, 
        {"$set": updated_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    
    updated_cv = await db.cvs.find_one({"id": cv_id})
    return CVData(**updated_cv)


@api_router.delete("/cv/{cv_id}")
async def delete_cv(cv_id: str):
    """Eliminar CV"""
    result = await db.cvs.delete_one({"id": cv_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="CV no encontrado")
    return {"message": "CV eliminado exitosamente"}


# ====================== FILTROS DE BÚSQUEDA ======================
@api_router.post("/user/{user_id}/search-filters", response_model=SearchFilters)
async def create_search_filters(user_id: str, filters_data: SearchFiltersCreate):
    """Crear filtros de búsqueda"""
    filters = SearchFilters(**filters_data.dict(), user_id=user_id)
    await db.search_filters.insert_one(filters.dict())
    return filters


@api_router.get("/user/{user_id}/search-filters", response_model=List[SearchFilters])
async def get_user_search_filters(user_id: str):
    """Obtener filtros de búsqueda del usuario"""
    filters = await db.search_filters.find({"user_id": user_id}).to_list(100)
    return [SearchFilters(**f) for f in filters]


@api_router.put("/search-filters/{filter_id}", response_model=SearchFilters)
async def update_search_filters(filter_id: str, filters_data: SearchFiltersCreate):
    """Actualizar filtros de búsqueda"""
    updated_data = filters_data.dict()
    updated_data["updated_at"] = datetime.utcnow()
    
    result = await db.search_filters.update_one(
        {"id": filter_id}, 
        {"$set": updated_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Filtros no encontrados")
    
    updated_filters = await db.search_filters.find_one({"id": filter_id})
    return SearchFilters(**updated_filters)


# ====================== TRABAJOS ======================
@api_router.get("/user/{user_id}/jobs", response_model=List[JobPosting])
async def get_user_jobs(
    user_id: str,
    portal: Optional[JobPortal] = None,
    limit: int = 50,
    skip: int = 0
):
    """Obtener trabajos encontrados para el usuario"""
    query = {}
    if portal:
        query["portal"] = portal
    
    jobs = await db.jobs.find(query).skip(skip).limit(limit).to_list(limit)
    return [JobPosting(**job) for job in jobs]


@api_router.get("/job/{job_id}", response_model=JobPosting)
async def get_job(job_id: str):
    """Obtener trabajo específico"""
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return JobPosting(**job)


# ====================== POSTULACIONES ======================
@api_router.get("/user/{user_id}/applications", response_model=List[JobApplication])
async def get_user_applications(
    user_id: str,
    status: Optional[ApplicationStatus] = None,
    limit: int = 100,
    skip: int = 0
):
    """Obtener postulaciones del usuario"""
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    
    applications = await db.applications.find(query).skip(skip).limit(limit).to_list(limit)
    return [JobApplication(**app) for app in applications]


@api_router.post("/user/{user_id}/apply/{job_id}")
async def apply_to_job(
    user_id: str, 
    job_id: str,
    background_tasks: BackgroundTasks,
    cv_id: Optional[str] = None,
    custom_message: Optional[str] = None
):
    """Postular a un trabajo específico"""
    # Verificar que el trabajo existe
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    # Usar CV por defecto si no se especifica
    if not cv_id:
        cv = await db.cvs.find_one({"user_id": user_id, "is_default": True})
        if not cv:
            raise HTTPException(status_code=400, detail="No hay CV por defecto configurado")
        cv_id = cv["id"]
    
    # Crear postulación
    application = JobApplication(
        user_id=user_id,
        job_id=job_id,
        cv_used=cv_id,
        custom_message=custom_message,
        status=ApplicationStatus.PENDING
    )
    
    await db.applications.insert_one(application.dict())
    
    # Procesar postulación en background
    background_tasks.add_task(
        application_service.process_application,
        application.id
    )
    
    return {"message": "Postulación iniciada", "application_id": application.id}


# ====================== BÚSQUEDA AUTOMÁTICA ======================
@api_router.post("/user/{user_id}/start-search")
async def start_automatic_search(user_id: str, background_tasks: BackgroundTasks):
    """Iniciar búsqueda automática de trabajos"""
    # Verificar que el usuario tiene filtros activos
    active_filters = await db.search_filters.find_one({
        "user_id": user_id, 
        "is_active": True
    })
    
    if not active_filters:
        raise HTTPException(
            status_code=400, 
            detail="No hay filtros de búsqueda activos configurados"
        )
    
    # Iniciar búsqueda en background
    background_tasks.add_task(
        scraper_service.search_and_apply,
        user_id
    )
    
    return {"message": "Búsqueda automática iniciada"}


@api_router.post("/user/{user_id}/stop-search")
async def stop_automatic_search(user_id: str):
    """Detener búsqueda automática"""
    # Desactivar todos los filtros del usuario
    await db.search_filters.update_many(
        {"user_id": user_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Búsqueda automática detenida"}


# ====================== CONFIGURACIÓN IA ======================
@api_router.post("/user/{user_id}/ai-config", response_model=AIConfig)
async def create_ai_config(user_id: str, config_data: AIConfigCreate):
    """Configurar IA para el usuario"""
    config = AIConfig(**config_data.dict(), user_id=user_id)
    
    # Eliminar configuración anterior si existe
    await db.ai_config.delete_many({"user_id": user_id})
    
    await db.ai_config.insert_one(config.dict())
    
    # Actualizar servicio AI con nueva configuración
    if config.gemini_api_key:
        ai_service.update_config(user_id, config.dict())
    
    return config


@api_router.get("/user/{user_id}/ai-config", response_model=AIConfig)
async def get_ai_config(user_id: str):
    """Obtener configuración IA del usuario"""
    config = await db.ai_config.find_one({"user_id": user_id})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración IA no encontrada")
    return AIConfig(**config)


# ====================== ESTADÍSTICAS ======================
@api_router.get("/user/{user_id}/stats")
async def get_user_stats(user_id: str, days: int = 30):
    """Obtener estadísticas del usuario"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Estadísticas básicas
    total_applications = await db.applications.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": start_date}
    })
    
    total_jobs_found = await db.jobs.count_documents({
        "scraped_at": {"$gte": start_date}
    })
    
    # Aplicaciones por estado
    pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": start_date}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_stats = await db.applications.aggregate(pipeline).to_list(10)
    
    # Aplicaciones por portal
    portal_pipeline = [
        {"$lookup": {
            "from": "jobs",
            "localField": "job_id",
            "foreignField": "id",
            "as": "job_info"
        }},
        {"$unwind": "$job_info"},
        {"$match": {"user_id": user_id, "created_at": {"$gte": start_date}}},
        {"$group": {"_id": "$job_info.portal", "count": {"$sum": 1}}}
    ]
    portal_stats = await db.applications.aggregate(portal_pipeline).to_list(10)
    
    return {
        "period_days": days,
        "total_applications": total_applications,
        "total_jobs_found": total_jobs_found,
        "applications_by_status": {item["_id"]: item["count"] for item in status_stats},
        "applications_by_portal": {item["_id"]: item["count"] for item in portal_stats},
        "success_rate": 0.0 if total_applications == 0 else len([s for s in status_stats if s["_id"] in ["interview", "offer"]]) / total_applications * 100
    }


# ====================== HEALTH CHECK ======================
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }


@api_router.get("/")
async def root():
    return {"message": "Autopostulador Laboral Chile API - ¡Sistema funcionando!"}


# Include router
app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()