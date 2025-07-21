from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class JobPortal(str, Enum):
    LINKEDIN = "linkedin"
    LABORUM = "laborum"
    BNE = "bne"
    TRABAJANDO = "trabajando"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    VIEWED = "viewed"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class WorkMode(str, Enum):
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


# Usuario
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: str = "Santiago, Chile"
    linkedin_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CVData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str  # Título del CV (ej: "CV Comercial", "CV Administrativo")
    personal_info: Dict[str, Any]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[str]
    certifications: List[Dict[str, Any]]
    languages: List[Dict[str, Any]]
    raw_text: str  # Texto completo para IA
    file_path: Optional[str] = None
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Configuración de búsqueda
class SearchFilters(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    keywords: List[str]
    excluded_keywords: List[str] = []
    job_types: List[JobType] = []
    work_modes: List[WorkMode] = []
    locations: List[str] = ["Santiago"]
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    company_size: Optional[List[str]] = None
    industries: List[str] = []
    portals: List[JobPortal] = [JobPortal.LINKEDIN, JobPortal.LABORUM, JobPortal.BNE, JobPortal.TRABAJANDO]
    auto_apply: bool = True
    max_applications_per_day: int = 50
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Trabajo encontrado
class JobPosting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    portal: JobPortal
    external_id: str  # ID del portal externo
    url: str
    title: str
    company: str
    company_url: Optional[str] = None
    location: str
    work_mode: Optional[WorkMode] = None
    job_type: Optional[JobType] = None
    salary: Optional[str] = None
    description: str
    requirements: List[str] = []
    benefits: List[str] = []
    posted_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    keywords_matched: List[str] = []
    match_percentage: Optional[float] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Postulación
class JobApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    job_id: str
    cv_used: str  # ID del CV utilizado
    cover_letter: Optional[str] = None
    custom_message: Optional[str] = None
    portal_data: Dict[str, Any] = {}  # Datos específicos del portal
    status: ApplicationStatus = ApplicationStatus.PENDING
    applied_at: Optional[datetime] = None
    last_update: datetime = Field(default_factory=datetime.utcnow)
    response_received: bool = False
    interview_scheduled: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Estadísticas
class ApplicationStats(BaseModel):
    user_id: str
    date: datetime
    total_jobs_found: int = 0
    total_applications_sent: int = 0
    applications_by_portal: Dict[str, int] = {}
    response_rate: float = 0.0
    interview_rate: float = 0.0
    success_rate: float = 0.0
    top_keywords: List[Dict[str, Any]] = []
    avg_match_percentage: float = 0.0


# Configuración AI
class AIConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    gemini_api_key: Optional[str] = None
    personalization_enabled: bool = True
    auto_cover_letter: bool = True
    auto_form_fill: bool = True
    response_style: str = "professional"  # professional, friendly, formal
    cv_customization_level: str = "medium"  # low, medium, high
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Respuestas para crear
class UserProfileCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: str = "Santiago, Chile"
    linkedin_url: Optional[str] = None


class CVDataCreate(BaseModel):
    title: str
    personal_info: Dict[str, Any]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[str]
    certifications: List[Dict[str, Any]] = []
    languages: List[Dict[str, Any]] = []
    raw_text: str
    is_default: bool = False


class SearchFiltersCreate(BaseModel):
    keywords: List[str]
    excluded_keywords: List[str] = []
    job_types: List[JobType] = []
    work_modes: List[WorkMode] = []
    locations: List[str] = ["Santiago"]
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    industries: List[str] = []
    portals: List[JobPortal] = [JobPortal.LINKEDIN, JobPortal.LABORUM, JobPortal.BNE, JobPortal.TRABAJANDO]
    auto_apply: bool = True
    max_applications_per_day: int = 50


class AIConfigCreate(BaseModel):
    gemini_api_key: Optional[str] = None
    personalization_enabled: bool = True
    auto_cover_letter: bool = True
    auto_form_fill: bool = True
    response_style: str = "professional"
    cv_customization_level: str = "medium"