from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

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
    id: int
    is_active: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
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
    id: int
    user_id: int
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    status: DocumentStatus
    error_message: Optional[str]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    document_metadata: Optional[Dict[str, Any]]
    extracted_text_length: Optional[int]
    total_clauses_found: int
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    status: DocumentStatus
    file_size: Optional[int]
    created_at: datetime
    total_clauses_found: int
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]

class DocumentStatusResponse(BaseModel):
    id: int
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
    document_id: int
    start_position: Optional[int]
    end_position: Optional[int]
    page_number: Optional[int]
    recommendations: Optional[str]

class Clause(ClauseBase):
    id: int
    document_id: int
    start_position: Optional[int]
    end_position: Optional[int]
    page_number: Optional[int]
    analysis_metadata: Optional[Dict[str, Any]]
    recommendations: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClauseResponse(BaseModel):
    id: int
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
    is_active: Optional[str]

class LegalPlaybook(LegalPlaybookBase):
    id: int
    user_id: int
    version: str
    is_active: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LegalPlaybookResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    version: str
    is_active: str
    created_at: datetime

# Analysis schemas
class AnalysisRequest(BaseModel):
    document_id: int
    playbook_id: Optional[int] = None
    analysis_type: str = "comprehensive"

class AnalysisResult(BaseModel):
    document_id: int
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
    document_id: int
    status: DocumentStatus
    job_id: Optional[str]

# Error response
class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str]
    timestamp: datetimefrom pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

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
    id: int
    is_active: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
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
    id: int
    user_id: int
    original_filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    status: DocumentStatus
    error_message: Optional[str]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    document_metadata: Optional[Dict[str, Any]]
    extracted_text_length: Optional[int]
    total_clauses_found: int
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    status: DocumentStatus
    file_size: Optional[int]
    created_at: datetime
    total_clauses_found: int
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]

class DocumentStatusResponse(BaseModel):
    id: int
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
    document_id: int
    start_position: Optional[int]
    end_position: Optional[int]
    page_number: Optional[int]
    recommendations: Optional[str]

class Clause(ClauseBase):
    id: int
    document_id: int
    start_position: Optional[int]
    end_position: Optional[int]
    page_number: Optional[int]
    analysis_metadata: Optional[Dict[str, Any]]
    recommendations: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClauseResponse(BaseModel):
    id: int
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
    is_active: Optional[str]

class LegalPlaybook(LegalPlaybookBase):
    id: int
    user_id: int
    version: str
    is_active: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LegalPlaybookResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    version: str
    is_active: str
    created_at: datetime

# Analysis schemas
class AnalysisRequest(BaseModel):
    document_id: int
    playbook_id: Optional[int] = None
    analysis_type: str = "comprehensive"

class AnalysisResult(BaseModel):
    document_id: int
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
    document_id: int
    status: DocumentStatus
    job_id: Optional[str]

# Error response
class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str]
    timestamp: datetime