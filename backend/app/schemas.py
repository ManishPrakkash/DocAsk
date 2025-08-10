from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=50)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Document schemas
class DocumentBase(BaseModel):
    filename: str

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    status: Optional[DocumentStatus] = None
    error_message: Optional[str] = None

class Document(DocumentBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    status: DocumentStatus
    error_message: Optional[str]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    document_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    extracted_text_length: Optional[int]
    total_clauses_found: int = Field(default=0)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    status: DocumentStatus
    file_size: Optional[int]
    created_at: datetime
    total_clauses_found: int
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]

class DocumentStatusResponse(BaseModel):
    id: str
    status: DocumentStatus
    progress: Optional[int] = 0
    error_message: Optional[str]
    total_clauses_found: int

# Clause schemas
class ClauseBase(BaseModel):
    text: str
    category: str
    subcategory: Optional[str]
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    confidence_score: float = Field(ge=0.0, le=1.0)

class ClauseCreate(ClauseBase):
    document_id: PyObjectId
    start_position: Optional[int]
    end_position: Optional[int]
    page_number: Optional[int]
    recommendations: Optional[str]

class Clause(ClauseBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    document_id: PyObjectId
    start_position: Optional[int]
    end_position: Optional[int]
    page_number: Optional[int]
    analysis_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    recommendations: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ClauseResponse(BaseModel):
    id: str
    text: str
    category: str
    subcategory: Optional[str]
    risk_score: float
    risk_level: RiskLevel
    confidence_score: float
    start_position: Optional[int]
    end_position: Optional[int]
    page_number: Optional[int]
    recommendations: Optional[str]

# Legal Playbook schemas
class LegalPlaybookBase(BaseModel):
    name: str
    description: Optional[str]
    rules: Dict[str, Any]

class LegalPlaybookCreate(LegalPlaybookBase):
    pass

class LegalPlaybookUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    rules: Optional[Dict[str, Any]]
    is_active: Optional[bool]

class LegalPlaybook(LegalPlaybookBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    version: str = Field(default="1.0")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class LegalPlaybookResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    version: str
    is_active: bool
    created_at: datetime

# Analysis schemas
class AnalysisRequest(BaseModel):
    document_id: str
    playbook_id: Optional[str] = None
    analysis_type: str = "comprehensive"

class AnalysisResult(BaseModel):
    document_id: str
    total_clauses: int
    risk_distribution: Dict[str, int]
    category_breakdown: Dict[str, int]
    recommendations: List[str]
    overall_risk_score: float
    analysis_metadata: Dict[str, Any]

class DocumentAnalysisResponse(BaseModel):
    document: DocumentResponse
    clauses: List[ClauseResponse]
    analysis_summary: AnalysisResult

# Upload response
class UploadResponse(BaseModel):
    message: str
    document_id: str
    status: DocumentStatus
    job_id: Optional[str]

# Job status
class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

# Analysis statistics
class AnalysisStatistics(BaseModel):
    total_documents: int
    total_clauses: int
    risk_distribution: Dict[str, int]
    category_breakdown: Dict[str, int]
    average_risk_score: float

# Error response
class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class APIError(BaseModel):
    error: str
    message: str
    status_code: int