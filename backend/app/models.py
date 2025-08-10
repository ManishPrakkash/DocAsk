from pydantic import BaseModel, Field, ConfigDict
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

# Base models
class UserBase(BaseModel):
    email: str = Field(..., description="User email address")
    is_active: bool = Field(default=True, description="User account status")

class UserCreate(UserBase):
    password: str = Field(..., description="User password")

class User(UserBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    hashed_password: str = Field(..., description="Hashed user password")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class DocumentBase(BaseModel):
    filename: str = Field(..., description="Document filename")
    original_filename: str = Field(..., description="Original document filename")
    file_path: str = Field(..., description="File storage path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="File MIME type")

class DocumentCreate(DocumentBase):
    user_id: PyObjectId = Field(..., description="User ID who uploaded the document")

class Document(DocumentBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID who uploaded the document")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    processing_started_at: Optional[datetime] = Field(None, description="When processing started")
    processing_completed_at: Optional[datetime] = Field(None, description="When processing completed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    document_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    extracted_text_length: Optional[int] = Field(None, description="Length of extracted text")
    total_clauses_found: int = Field(default=0, description="Total number of clauses found")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ClauseBase(BaseModel):
    text: str = Field(..., description="Clause text content")
    category: str = Field(..., description="Clause category")
    subcategory: Optional[str] = Field(None, description="Clause subcategory")
    risk_score: float = Field(default=0.0, description="Risk score (0.0 to 1.0)")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Risk level")

class ClauseCreate(ClauseBase):
    document_id: PyObjectId = Field(..., description="Document ID this clause belongs to")

class Clause(ClauseBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    document_id: PyObjectId = Field(..., description="Document ID this clause belongs to")
    confidence_score: float = Field(default=0.0, description="Confidence score (0.0 to 1.0)")
    
    # Position information
    start_position: Optional[int] = Field(None, description="Start position in document")
    end_position: Optional[int] = Field(None, description="End position in document")
    page_number: Optional[int] = Field(None, description="Page number")
    
    # Analysis metadata
    analysis_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    recommendations: Optional[str] = Field(None, description="Analysis recommendations")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class LegalPlaybookBase(BaseModel):
    name: str = Field(..., description="Playbook name")
    description: Optional[str] = Field(None, description="Playbook description")
    rules: Dict[str, Any] = Field(..., description="Playbook rules as JSON")

class LegalPlaybookCreate(LegalPlaybookBase):
    user_id: PyObjectId = Field(..., description="User ID who created the playbook")

class LegalPlaybook(LegalPlaybookBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID who created the playbook")
    
    # Metadata
    version: str = Field(default="1.0", description="Playbook version")
    is_active: bool = Field(default=True, description="Playbook status")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class AnalysisJob(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    document_id: PyObjectId = Field(..., description="Document ID to analyze")
    playbook_id: PyObjectId = Field(..., description="Playbook ID to use for analysis")
    user_id: PyObjectId = Field(..., description="User ID who requested analysis")
    
    # Job status
    status: str = Field(default="pending", description="Job status")
    progress: float = Field(default=0.0, description="Progress percentage (0.0 to 1.0)")
    
    # Results
    results: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="When analysis started")
    completed_at: Optional[datetime] = Field(None, description="When analysis completed")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class TokenData(BaseModel):
    email: Optional[str] = None