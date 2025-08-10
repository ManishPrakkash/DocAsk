import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from app.database import get_documents_collection, get_clauses_collection
from app.auth import get_current_user
from app.models import User, Document, DocumentStatus, DocumentCreate
from app.schemas import (
    DocumentResponse, DocumentStatusResponse, UploadResponse, 
    DocumentAnalysisResponse, ClauseResponse, AnalysisResult
)
from app.tasks import process_document
from app.services.document_parser import DocumentParser
import aiofiles
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword"
}

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload legal document for analysis
    
    Accepts PDF and DOCX files up to 10MB
    Triggers asynchronous processing workflow
    Returns 202 Accepted with document ID and job status
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Check MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Get document metadata
        parser = DocumentParser()
        metadata = parser.get_document_metadata(file_path, file.content_type)
        
        # Create document record in MongoDB
        documents_collection = get_documents_collection()
        
        document_doc = {
            "user_id": current_user.id,
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": len(content),
            "mime_type": file.content_type,
            "status": DocumentStatus.PENDING,
            "document_metadata": metadata,
            "total_clauses_found": 0,
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("created_at")
        }
        
        result = await documents_collection.insert_one(document_doc)
        document_id = str(result.inserted_id)
        
        # Trigger async processing
        job = process_document.delay(document_id)
        
        logger.info(f"Document uploaded: {document_id} for user {current_user.email}")
        
        return UploadResponse(
            message="Document uploaded successfully and processing started",
            document_id=document_id,
            status=DocumentStatus.PENDING,
            job_id=job.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed due to server error"
        )

@router.get("/", response_model=List[DocumentResponse])
async def get_user_documents(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all documents for the current user
    
    - **skip**: Number of documents to skip (for pagination)
    - **limit**: Maximum number of documents to return
    """
    try:
        documents_collection = get_documents_collection()
        
        # Query documents for current user
        cursor = documents_collection.find(
            {"user_id": current_user.id}
        ).skip(skip).limit(limit).sort("created_at", -1)
        
        documents = []
        async for doc in cursor:
            documents.append(DocumentResponse(
                id=str(doc["_id"]),
                filename=doc["filename"],
                original_filename=doc["original_filename"],
                status=doc["status"],
                file_size=doc["file_size"],
                created_at=doc["created_at"],
                total_clauses_found=doc["total_clauses_found"],
                processing_completed_at=doc.get("processing_completed_at"),
                error_message=doc.get("error_message")
            ))
        
        return documents
        
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch documents"
        )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific document by ID
    
    - **document_id**: Document ID
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(document_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format"
            )
        
        documents_collection = get_documents_collection()
        
        # Find document
        doc = await documents_collection.find_one({
            "_id": ObjectId(document_id),
            "user_id": current_user.id
        })
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse(
            id=str(doc["_id"]),
            filename=doc["filename"],
            original_filename=doc["original_filename"],
            status=doc["status"],
            file_size=doc["file_size"],
            created_at=doc["created_at"],
            total_clauses_found=doc["total_clauses_found"],
            processing_completed_at=doc.get("processing_completed_at"),
            error_message=doc.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document"
        )

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get document processing status
    
    - **document_id**: Document ID
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(document_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format"
            )
        
        documents_collection = get_documents_collection()
        
        # Find document
        doc = await documents_collection.find_one({
            "_id": ObjectId(document_id),
            "user_id": current_user.id
        })
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Calculate progress based on status
        progress = 0
        if doc["status"] == DocumentStatus.PENDING:
            progress = 0
        elif doc["status"] == DocumentStatus.PROCESSING:
            progress = 50
        elif doc["status"] == DocumentStatus.COMPLETE:
            progress = 100
        elif doc["status"] == DocumentStatus.ERROR:
            progress = 0
        
        return DocumentStatusResponse(
            id=str(doc["_id"]),
            status=doc["status"],
            progress=progress,
            error_message=doc.get("error_message"),
            total_clauses_found=doc["total_clauses_found"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document status {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document status"
        )

@router.get("/{document_id}/analysis", response_model=DocumentAnalysisResponse)
async def get_document_analysis(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get complete document analysis including clauses
    
    - **document_id**: Document ID
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(document_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format"
            )
        
        documents_collection = get_documents_collection()
        clauses_collection = get_clauses_collection()
        
        # Find document
        doc = await documents_collection.find_one({
            "_id": ObjectId(document_id),
            "user_id": current_user.id
        })
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if analysis is complete
        if doc["status"] != DocumentStatus.COMPLETE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document analysis not complete"
            )
        
        # Get clauses for this document
        clauses_cursor = clauses_collection.find({"document_id": ObjectId(document_id)})
        clauses = []
        async for clause in clauses_cursor:
            clauses.append(ClauseResponse(
                id=str(clause["_id"]),
                text=clause["text"],
                category=clause["category"],
                subcategory=clause.get("subcategory"),
                risk_score=clause["risk_score"],
                risk_level=clause["risk_level"],
                confidence_score=clause["confidence_score"],
                start_position=clause.get("start_position"),
                end_position=clause.get("end_position"),
                page_number=clause.get("page_number"),
                recommendations=clause.get("recommendations")
            ))
        
        # Create document response
        document_response = DocumentResponse(
            id=str(doc["_id"]),
            filename=doc["filename"],
            original_filename=doc["original_filename"],
            status=doc["status"],
            file_size=doc["file_size"],
            created_at=doc["created_at"],
            total_clauses_found=doc["total_clauses_found"],
            processing_completed_at=doc.get("processing_completed_at"),
            error_message=doc.get("error_message")
        )
        
        # Calculate analysis summary
        risk_distribution = {}
        category_breakdown = {}
        total_risk_score = 0.0
        
        for clause in clauses:
            # Risk distribution
            risk_level = clause.risk_level
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            # Category breakdown
            category = clause.category
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
            
            # Total risk score
            total_risk_score += clause.risk_score
        
        average_risk_score = total_risk_score / len(clauses) if clauses else 0.0
        
        analysis_summary = AnalysisResult(
            document_id=document_id,
            total_clauses=len(clauses),
            risk_distribution=risk_distribution,
            category_breakdown=category_breakdown,
            recommendations=[c.recommendations for c in clauses if c.recommendations],
            overall_risk_score=average_risk_score,
            analysis_metadata=doc.get("document_metadata", {})
        )
        
        return DocumentAnalysisResponse(
            document=document_response,
            clauses=clauses,
            analysis_summary=analysis_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document analysis {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document analysis"
        )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document and its associated clauses
    
    - **document_id**: Document ID
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(document_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format"
            )
        
        documents_collection = get_documents_collection()
        clauses_collection = get_clauses_collection()
        
        # Find document
        doc = await documents_collection.find_one({
            "_id": ObjectId(document_id),
            "user_id": current_user.id
        })
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete associated clauses
        await clauses_collection.delete_many({"document_id": ObjectId(document_id)})
        
        # Delete document
        await documents_collection.delete_one({"_id": ObjectId(document_id)})
        
        # Delete file from disk
        try:
            if os.path.exists(doc["file_path"]):
                os.remove(doc["file_path"])
        except Exception as e:
            logger.warning(f"Failed to delete file {doc['file_path']}: {e}")
        
        logger.info(f"Document deleted: {document_id} for user {current_user.email}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )