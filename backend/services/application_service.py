import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import JobApplication, ApplicationStatus, CVData, JobPosting
from services.ai_service import AIService

logger = logging.getLogger(__name__)


class ApplicationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.ai_service = AIService()
    
    async def process_application(self, application_id: str):
        """Procesar una postulación en background"""
        try:
            # Obtener aplicación
            app_doc = await self.db.applications.find_one({"id": application_id})
            if not app_doc:
                logger.error(f"Aplicación {application_id} no encontrada")
                return
            
            application = JobApplication(**app_doc)
            
            # Obtener trabajo y CV
            job_doc = await self.db.jobs.find_one({"id": application.job_id})
            cv_doc = await self.db.cvs.find_one({"id": application.cv_used})
            
            if not job_doc or not cv_doc:
                logger.error(f"Datos faltantes para aplicación {application_id}")
                await self._update_application_status(application_id, ApplicationStatus.REJECTED, "Datos incompletos")
                return
            
            job_posting = JobPosting(**job_doc)
            cv_data = CVData(**cv_doc)
            
            # Generar carta de presentación si no existe
            if not application.cover_letter:
                cover_letter = await self.ai_service.generate_cover_letter(
                    application.user_id, cv_data, job_posting
                )
                application.cover_letter = cover_letter
            
            # Procesar según portal
            success = False
            if job_posting.portal.value == "linkedin":
                success = await self._apply_linkedin(application, job_posting, cv_data)
            elif job_posting.portal.value == "laborum":
                success = await self._apply_laborum(application, job_posting, cv_data)
            elif job_posting.portal.value == "bne":
                success = await self._apply_bne(application, job_posting, cv_data)
            elif job_posting.portal.value == "trabajando":
                success = await self._apply_trabajando(application, job_posting, cv_data)
            
            # Actualizar estado
            if success:
                await self._update_application_status(
                    application_id, 
                    ApplicationStatus.APPLIED, 
                    f"Postulación enviada a {job_posting.company}"
                )
                logger.info(f"Aplicación {application_id} enviada exitosamente")
            else:
                await self._update_application_status(
                    application_id, 
                    ApplicationStatus.REJECTED, 
                    "Error en el envío"
                )
                logger.error(f"Aplicación {application_id} falló")
        
        except Exception as e:
            logger.error(f"Error procesando aplicación {application_id}: {e}")
            await self._update_application_status(application_id, ApplicationStatus.REJECTED, str(e))
    
    async def _update_application_status(self, application_id: str, status: ApplicationStatus, notes: str = ""):
        """Actualizar estado de aplicación"""
        update_data = {
            "status": status.value,
            "last_update": datetime.utcnow(),
            "notes": notes
        }
        
        if status == ApplicationStatus.APPLIED:
            update_data["applied_at"] = datetime.utcnow()
        
        await self.db.applications.update_one(
            {"id": application_id},
            {"$set": update_data}
        )
    
    async def _apply_linkedin(self, application: JobApplication, job: JobPosting, cv: CVData) -> bool:
        """Aplicar a trabajo en LinkedIn"""
        try:
            logger.info(f"Simulando aplicación LinkedIn para: {job.title} en {job.company}")
            
            # TODO: Implementar aplicación real con Selenium
            # Por ahora simular éxito
            await asyncio.sleep(2)  # Simular tiempo de procesamiento
            
            # Marcar como aplicado
            application.portal_data = {
                "method": "linkedin_easy_apply",
                "timestamp": datetime.utcnow().isoformat(),
                "cover_letter_sent": bool(application.cover_letter)
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando LinkedIn: {e}")
            return False
    
    async def _apply_laborum(self, application: JobApplication, job: JobPosting, cv: CVData) -> bool:
        """Aplicar a trabajo en Laborum"""
        try:
            logger.info(f"Simulando aplicación Laborum para: {job.title} en {job.company}")
            
            # TODO: Implementar aplicación real
            await asyncio.sleep(2)
            
            application.portal_data = {
                "method": "laborum_form",
                "timestamp": datetime.utcnow().isoformat(),
                "form_filled": True
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando Laborum: {e}")
            return False
    
    async def _apply_bne(self, application: JobApplication, job: JobPosting, cv: CVData) -> bool:
        """Aplicar a trabajo en BNE"""
        try:
            logger.info(f"Simulando aplicación BNE para: {job.title} en {job.company}")
            
            # TODO: Implementar aplicación real
            await asyncio.sleep(2)
            
            application.portal_data = {
                "method": "bne_portal",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando BNE: {e}")
            return False
    
    async def _apply_trabajando(self, application: JobApplication, job: JobPosting, cv: CVData) -> bool:
        """Aplicar a trabajo en Trabajando.com"""
        try:
            logger.info(f"Simulando aplicación Trabajando.com para: {job.title} en {job.company}")
            
            # TODO: Implementar aplicación real
            await asyncio.sleep(2)
            
            application.portal_data = {
                "method": "trabajando_form",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando Trabajando.com: {e}")
            return False
    
    async def get_application_stats(self, user_id: str, days: int = 30) -> Dict:
        """Obtener estadísticas de aplicaciones"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Contar aplicaciones por estado
        pipeline = [
            {"$match": {"user_id": user_id, "created_at": {"$gte": start_date}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        status_counts = await self.db.applications.aggregate(pipeline).to_list(10)
        
        # Calcular tasas
        total_apps = sum(item["count"] for item in status_counts)
        successful_apps = sum(item["count"] for item in status_counts if item["_id"] in ["interview", "offer"])
        
        return {
            "total_applications": total_apps,
            "success_rate": (successful_apps / total_apps * 100) if total_apps > 0 else 0,
            "status_breakdown": {item["_id"]: item["count"] for item in status_counts}
        }