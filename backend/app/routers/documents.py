import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Document, DocumentStatus
from app.schemas import (
    DocumentResponse, DocumentStatusResponse, UploadResponse, 
    DocumentAnalysisResponse, ClauseResponse, AnalysisResult
)
from app.tasks import process_document
from app.services.document_parser import DocumentParser
import aiofiles
import logging

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        
        # Create document record in database
        document = Document(
            user_id=current_user.id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            status=DocumentStatus.PENDING,
            document_metadata=metadata
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Queue asynchronous processing job
        job = process_document.delay(document.id)
        
        logger.info(f"Document uploaded successfully: {document.id} by user {current_user.id}")
        
        return UploadResponse(
            message="Document uploaded successfully and queued for processing",
            document_id=document.id,
            status=DocumentStatus.PENDING,
            job_id=job.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error for user {current_user.id}: {str(e)}")
        # Clean up file if it was created
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )

@router.get("/", response_model=List[DocumentResponse])
async def get_user_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get list of user's documents
    
    - **skip**: Number of documents to skip (pagination)
    - **limit**: Maximum number of documents to return
    """
    try:
        documents = db.query(Document)\
            .filter(Document.user_id == current_user.id)\
            .order_by(Document.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                status=doc.status,
                file_size=doc.file_size,
                created_at=doc.created_at,
                total_clauses_found=doc.total_clauses_found,
                processing_completed_at=doc.processing_completed_at,
                error_message=doc.error_message
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Error fetching documents for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific document details"""
    try:
        document = db.query(Document)\
            .filter(Document.id == document_id, Document.user_id == current_user.id)\
            .first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            status=document.status,
            file_size=document.file_size,
            created_at=document.created_at,
            total_clauses_found=document.total_clauses_found,
            processing_completed_at=document.processing_completed_at,
            error_message=document.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time document processing status
    
    Used for polling document processing progress
    """
    try:
        document = db.query(Document)\
            .filter(Document.id == document_id, Document.user_id == current_user.id)\
            .first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Calculate progress percentage
        progress = 0
        if document.status == DocumentStatus.PENDING:
            progress = 0
        elif document.status == DocumentStatus.PROCESSING:
            progress = 50  # Could be more sophisticated with actual job progress
        elif document.status == DocumentStatus.COMPLETE:
            progress = 100
        elif document.status == DocumentStatus.ERROR:
            progress = 0
        
        return DocumentStatusResponse(
            id=document.id,
            status=document.status,
            progress=progress,
            error_message=document.error_message,
            total_clauses_found=document.total_clauses_found
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching status for document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document status"
        )

@router.get("/{document_id}/analysis", response_model=DocumentAnalysisResponse)
async def get_document_analysis(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete document analysis results
    
    Returns document details, extracted clauses, and analysis summary
    """
    try:
        document = db.query(Document)\
            .filter(Document.id == document_id, Document.user_id == current_user.id)\
            .first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if document.status != DocumentStatus.COMPLETE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document analysis not yet complete"
            )
        
        # Get document clauses
        clauses = [
            ClauseResponse(
                id=clause.id,
                text=clause.text,
                category=clause.category,
                subcategory=clause.subcategory,
                risk_score=clause.risk_score,
                risk_level=clause.risk_level,
                confidence_score=clause.confidence_score,
                start_position=clause.start_position,
                end_position=clause.end_position,
                page_number=clause.page_number,
                recommendations=clause.recommendations
            )
            for clause in document.clauses
        ]
        
        # Generate analysis summary
        risk_distribution = {}
        category_breakdown = {}
        total_risk_score = 0.0
        recommendations = []
        
        for clause in document.clauses:
            # Risk distribution
            risk_level = clause.risk_level.value
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            # Category breakdown
            category = clause.category
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
            
            # Risk score
            total_risk_score += clause.risk_score
            
            # High-risk recommendations
            if clause.risk_level.value in ['critical', 'high'] and clause.recommendations:
                recommendations.append(clause.recommendations)
        
        overall_risk_score = total_risk_score / len(document.clauses) if document.clauses else 0.0
        
        analysis_summary = AnalysisResult(
            document_id=document.id,
            total_clauses=len(document.clauses),
            risk_distribution=risk_distribution,
            category_breakdown=category_breakdown,
            recommendations=recommendations[:10],  # Limit recommendations
            overall_risk_score=overall_risk_score,
            analysis_metadata=document.document_metadata or {}
        )
        
        document_response = DocumentResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            status=document.status,
            file_size=document.file_size,
            created_at=document.created_at,
            total_clauses_found=document.total_clauses_found,
            processing_completed_at=document.processing_completed_at,
            error_message=document.error_message
        )
        
        return DocumentAnalysisResponse(
            document=document_response,
            clauses=clauses,
            analysis_summary=analysis_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis for document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document analysis"
        )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete document and all associated data"""
    try:
        document = db.query(Document)\
            .filter(Document.id == document_id, Document.user_id == current_user.id)\
            .first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete physical file
        if os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception as e:
                logger.warning(f"Failed to delete file {document.file_path}: {str(e)}")
        
        # Delete from database (cascades to clauses)
        db.delete(document)
        db.commit()
        
        logger.info(f"Document {document_id} deleted by user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )