from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, LegalPlaybook as LegalPlaybookModel
from app.schemas import (
    LegalPlaybookCreate, LegalPlaybookResponse, LegalPlaybookUpdate, LegalPlaybook,
    AnalysisRequest, AnalysisResult
)
from app.tasks import analyze_document_with_playbook
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/playbooks", response_model=List[LegalPlaybookResponse])
async def get_user_playbooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get user's legal playbooks
    
    - **skip**: Number of playbooks to skip (pagination)
    - **limit**: Maximum number of playbooks to return
    """
    try:
        playbooks = db.query(LegalPlaybookModel)\
            .filter(LegalPlaybookModel.user_id == current_user.id)\
            .filter(LegalPlaybookModel.is_active == "true")\
            .order_by(LegalPlaybookModel.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        return [
            LegalPlaybookResponse(
                id=playbook.id,
                name=playbook.name,
                description=playbook.description,
                version=playbook.version,
                is_active=playbook.is_active,
                created_at=playbook.created_at
            )
            for playbook in playbooks
        ]
        
    except Exception as e:
        logger.error(f"Error fetching playbooks for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve playbooks"
        )

@router.post("/playbooks", response_model=LegalPlaybookResponse, status_code=status.HTTP_201_CREATED)
async def create_playbook(
    playbook_data: LegalPlaybookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new legal playbook
    
    - **name**: Playbook name
    - **description**: Optional description
    - **rules**: JSON object containing playbook rules and criteria
    """
    try:
        playbook = LegalPlaybookModel(
            user_id=current_user.id,
            name=playbook_data.name,
            description=playbook_data.description,
            rules=playbook_data.rules,
            version="1.0",
            is_active="true"
        )
        
        db.add(playbook)
        db.commit()
        db.refresh(playbook)
        
        logger.info(f"Playbook created: {playbook.id} by user {current_user.id}")
        
        return LegalPlaybookResponse(
            id=playbook.id,
            name=playbook.name,
            description=playbook.description,
            version=playbook.version,
            is_active=playbook.is_active,
            created_at=playbook.created_at
        )
        
    except Exception as e:
        logger.error(f"Error creating playbook for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create playbook"
        )

@router.get("/playbooks/{playbook_id}", response_model=LegalPlaybookResponse)
async def get_playbook(
    playbook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific playbook details including rules"""
    try:
        playbook = db.query(LegalPlaybook)\
            .filter(LegalPlaybook.id == playbook_id, LegalPlaybook.user_id == current_user.id)\
            .first()
        
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        db.delete(playbook)
        db.commit()
        
        logger.info(f"Playbook deleted: {playbook_id} by user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting playbook {playbook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete playbook"
        )

@router.post("/analyze", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def analyze_with_playbook(
    analysis_request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze document with specific playbook
    
    - **document_id**: ID of document to analyze
    - **playbook_id**: Optional ID of playbook to use for analysis
    - **analysis_type**: Type of analysis ("comprehensive", "quick", "focused")
    
    Returns job ID for tracking analysis progress
    """
    from app.models import Document
    
    try:
        # Verify document exists and belongs to user
        document = db.query(Document)\
            .filter(Document.id == analysis_request.document_id, Document.user_id == current_user.id)\
            .first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify playbook exists if provided
        if analysis_request.playbook_id:
            playbook = db.query(LegalPlaybookModel)\
                .filter(LegalPlaybookModel.id == analysis_request.playbook_id, LegalPlaybookModel.user_id == current_user.id)\
                .first()
            
            if not playbook:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Playbook not found"
                )
        
        # Queue analysis job
        if analysis_request.playbook_id:
            job = analyze_document_with_playbook.delay(
                analysis_request.document_id,
                analysis_request.playbook_id
            )
        else:
            # Use standard analysis
            from app.tasks import process_document
            job = process_document.delay(analysis_request.document_id)
        
        logger.info(f"Analysis job queued: {job.id} for document {analysis_request.document_id}")
        
        return {
            "message": "Analysis job queued successfully",
            "job_id": job.id,
            "document_id": analysis_request.document_id,
            "playbook_id": analysis_request.playbook_id,
            "analysis_type": analysis_request.analysis_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queuing analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue analysis job"
        )

@router.get("/job/{job_id}/status")
async def get_analysis_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of analysis job
    
    - **job_id**: Celery job ID returned from analysis request
    
    Returns current job status and progress
    """
    try:
        from app.celery_app import celery_app
        
        # Get job result
        job_result = celery_app.AsyncResult(job_id)
        
        if job_result.state == 'PENDING':
            response = {
                'job_id': job_id,
                'state': job_result.state,
                'progress': 0,
                'status': 'Job is waiting to be processed'
            }
        elif job_result.state == 'PROGRESS':
            response = {
                'job_id': job_id,
                'state': job_result.state,
                'progress': job_result.info.get('progress', 0),
                'status': job_result.info.get('status', 'Processing...')
            }
        elif job_result.state == 'SUCCESS':
            response = {
                'job_id': job_id,
                'state': job_result.state,
                'progress': 100,
                'status': 'Analysis completed successfully',
                'result': job_result.result
            }
        else:  # FAILURE or other states
            response = {
                'job_id': job_id,
                'state': job_result.state,
                'progress': 0,
                'status': 'Analysis failed',
                'error': str(job_result.info) if job_result.info else 'Unknown error'
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking job status {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check job status"
        )

@router.get("/statistics", response_model=dict)
async def get_analysis_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's document analysis statistics
    
    Returns summary statistics across all user's analyzed documents
    """
    from app.models import Document, Clause
    from sqlalchemy import func
    
    try:
        # Get document counts by status
        document_stats = db.query(
            Document.status,
            func.count(Document.id)
        ).filter(Document.user_id == current_user.id)\
         .group_by(Document.status)\
         .all()
        
        # Get clause statistics
        clause_stats = db.query(
            Clause.risk_level,
            func.count(Clause.id)
        ).join(Document)\
         .filter(Document.user_id == current_user.id)\
         .group_by(Clause.risk_level)\
         .all()
        
        # Get category breakdown
        category_stats = db.query(
            Clause.category,
            func.count(Clause.id)
        ).join(Document)\
         .filter(Document.user_id == current_user.id)\
         .group_by(Clause.category)\
         .all()
        
        # Calculate average risk score
        avg_risk = db.query(
            func.avg(Clause.risk_score)
        ).join(Document)\
         .filter(Document.user_id == current_user.id)\
         .scalar() or 0.0
        
        # Total documents and clauses
        total_documents = db.query(func.count(Document.id))\
            .filter(Document.user_id == current_user.id)\
            .scalar()
        
        total_clauses = db.query(func.count(Clause.id))\
            .join(Document)\
            .filter(Document.user_id == current_user.id)\
            .scalar()
        
        statistics = {
            "summary": {
                "total_documents": total_documents,
                "total_clauses": total_clauses,
                "average_risk_score": round(float(avg_risk), 3)
            },
            "document_status": {
                status.value: count for status, count in document_stats
            },
            "risk_distribution": {
                risk_level.value: count for risk_level, count in clause_stats
            },
            "category_breakdown": {
                category: count for category, count in category_stats
            }
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error fetching statistics for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playbook not found"
        )
        
        return playbook
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching playbook {playbook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve playbook"
        )

@router.put("/playbooks/{playbook_id}", response_model=LegalPlaybookResponse)
async def update_playbook(
    playbook_id: int,
    update_data: LegalPlaybookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update existing playbook"""
    try:
        playbook = db.query(LegalPlaybook)\
            .filter(LegalPlaybook.id == playbook_id, LegalPlaybook.user_id == current_user.id)\
            .first()
        
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Update fields if provided
        if update_data.name is not None:
            playbook.name = update_data.name
        if update_data.description is not None:
            playbook.description = update_data.description
        if update_data.rules is not None:
            playbook.rules = update_data.rules
            # Increment version when rules change
            current_version = float(playbook.version)
            playbook.version = str(current_version + 0.1)
        if update_data.is_active is not None:
            playbook.is_active = update_data.is_active
        
        db.commit()
        db.refresh(playbook)
        
        logger.info(f"Playbook updated: {playbook.id} by user {current_user.id}")
        
        return LegalPlaybookResponse(
            id=playbook.id,
            name=playbook.name,
            description=playbook.description,
            version=playbook.version,
            is_active=playbook.is_active,
            created_at=playbook.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating playbook {playbook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update playbook"
        )

@router.delete("/playbooks/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook(
    playbook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete playbook"""
    try:
        playbook = db.query(LegalPlaybook)\
            .filter(LegalPlaybook.id == playbook_id, LegalPlaybook.user_id == current_user.id)\
            .first()
        
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
            
        db.delete(playbook)
        db.commit()
        return {"message": "Playbook deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting playbook {playbook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete playbook"
        )