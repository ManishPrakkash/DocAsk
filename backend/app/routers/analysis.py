from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.database import get_legal_playbooks_collection, get_documents_collection, get_clauses_collection
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
    skip: int = 0,
    limit: int = 100
):
    """
    Get user's legal playbooks
    
    - **skip**: Number of playbooks to skip (pagination)
    - **limit**: Maximum number of playbooks to return
    """
    try:
        collection = get_legal_playbooks_collection()
        
        # Convert user ID to ObjectId for MongoDB query
        user_id = ObjectId(current_user.id)
        
        # Query MongoDB for playbooks
        cursor = collection.find({
            "user_id": user_id,
            "is_active": True
        }).sort("created_at", -1).skip(skip).limit(limit)
        
        playbooks = list(cursor)
        
        return [
            LegalPlaybookResponse(
                id=str(playbook["_id"]),
                name=playbook["name"],
                description=playbook["description"],
                version=playbook["version"],
                is_active=playbook["is_active"],
                created_at=playbook["created_at"]
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
    current_user: User = Depends(get_current_user)
):
    """
    Create a new legal playbook
    
    - **name**: Playbook name
    - **description**: Optional description
    - **rules**: JSON object containing playbook rules and criteria
    """
    try:
        collection = get_legal_playbooks_collection()
        
        # Convert user ID to ObjectId for MongoDB
        user_id = ObjectId(current_user.id)
        
        playbook_doc = {
            "user_id": user_id,
            "name": playbook_data.name,
            "description": playbook_data.description,
            "rules": playbook_data.rules,
            "version": "1.0",
            "is_active": True,
            "created_at": playbook_data.created_at
        }
        
        result = collection.insert_one(playbook_doc)
        playbook_id = result.inserted_id
        
        logger.info(f"Playbook created: {playbook_id} by user {current_user.id}")
        
        return LegalPlaybookResponse(
            id=str(playbook_id),
            name=playbook_data.name,
            description=playbook_data.description,
            version="1.0",
            is_active=True,
            created_at=playbook_data.created_at
        )
        
    except Exception as e:
        logger.error(f"Error creating playbook for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create playbook"
        )

@router.get("/playbooks/{playbook_id}", response_model=LegalPlaybookResponse)
async def get_playbook(
    playbook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific playbook details including rules"""
    try:
        collection = get_legal_playbooks_collection()
        
        # Validate ObjectId
        try:
            playbook_obj_id = ObjectId(playbook_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid playbook ID format"
            )
        
        user_id = ObjectId(current_user.id)
        
        playbook = collection.find_one({
            "_id": playbook_obj_id,
            "user_id": user_id
        })
        
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        return LegalPlaybookResponse(
            id=str(playbook["_id"]),
            name=playbook["name"],
            description=playbook["description"],
            version=playbook["version"],
            is_active=playbook["is_active"],
            created_at=playbook["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching playbook {playbook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve playbook"
        )

@router.post("/analyze", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def analyze_with_playbook(
    analysis_request: AnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze document with specific playbook
    
    - **document_id**: ID of document to analyze
    - **playbook_id**: Optional ID of playbook to use for analysis
    - **analysis_type**: Type of analysis ("comprehensive", "quick", "focused")
    
    Returns job ID for tracking analysis progress
    """
    try:
        documents_collection = get_documents_collection()
        playbooks_collection = get_legal_playbooks_collection()
        
        # Validate document ID
        try:
            document_obj_id = ObjectId(analysis_request.document_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format"
            )
        
        user_id = ObjectId(current_user.id)
        
        # Verify document exists and belongs to user
        document = documents_collection.find_one({
            "_id": document_obj_id,
            "user_id": user_id
        })
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify playbook exists if provided
        if analysis_request.playbook_id:
            try:
                playbook_obj_id = ObjectId(analysis_request.playbook_id)
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid playbook ID format"
                )
            
            playbook = playbooks_collection.find_one({
                "_id": playbook_obj_id,
                "user_id": user_id
            })
            
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
    current_user: User = Depends(get_current_user)
):
    """
    Get user's document analysis statistics
    
    Returns summary statistics across all user's analyzed documents
    """
    try:
        documents_collection = get_documents_collection()
        clauses_collection = get_clauses_collection()
        
        user_id = ObjectId(current_user.id)
        
        # Get document counts by status
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        document_stats = list(documents_collection.aggregate(pipeline))
        
        # Get clause statistics
        pipeline = [
            {"$lookup": {"from": "documents", "localField": "document_id", "foreignField": "_id", "as": "document"}},
            {"$unwind": "$document"},
            {"$match": {"document.user_id": user_id}},
            {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}}
        ]
        clause_stats = list(clauses_collection.aggregate(pipeline))
        
        # Get category breakdown
        pipeline = [
            {"$lookup": {"from": "documents", "localField": "document_id", "foreignField": "_id", "as": "document"}},
            {"$unwind": "$document"},
            {"$match": {"document.user_id": user_id}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        category_stats = list(clauses_collection.aggregate(pipeline))
        
        # Calculate average risk score
        pipeline = [
            {"$lookup": {"from": "documents", "localField": "document_id", "foreignField": "_id", "as": "document"}},
            {"$unwind": "$document"},
            {"$match": {"document.user_id": user_id}},
            {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
        ]
        avg_risk_result = list(clauses_collection.aggregate(pipeline))
        avg_risk = avg_risk_result[0]["avg_risk"] if avg_risk_result else 0.0
        
        # Total documents and clauses
        total_documents = documents_collection.count_documents({"user_id": user_id})
        
        pipeline = [
            {"$lookup": {"from": "documents", "localField": "document_id", "foreignField": "_id", "as": "document"}},
            {"$unwind": "$document"},
            {"$match": {"document.user_id": user_id}},
            {"$count": "total"}
        ]
        total_clauses_result = list(clauses_collection.aggregate(pipeline))
        total_clauses = total_clauses_result[0]["total"] if total_clauses_result else 0
        
        statistics = {
            "summary": {
                "total_documents": total_documents,
                "total_clauses": total_clauses,
                "average_risk_score": round(float(avg_risk), 3)
            },
            "document_status": {
                stat["_id"]: stat["count"] for stat in document_stats
            },
            "risk_distribution": {
                stat["_id"]: stat["count"] for stat in clause_stats
            },
            "category_breakdown": {
                stat["_id"]: stat["count"] for stat in category_stats
            }
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error fetching statistics for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.put("/playbooks/{playbook_id}", response_model=LegalPlaybookResponse)
async def update_playbook(
    playbook_id: str,
    update_data: LegalPlaybookUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update existing playbook"""
    try:
        collection = get_legal_playbooks_collection()
        
        # Validate ObjectId
        try:
            playbook_obj_id = ObjectId(playbook_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid playbook ID format"
            )
        
        user_id = ObjectId(current_user.id)
        
        # Find playbook
        playbook = collection.find_one({
            "_id": playbook_obj_id,
            "user_id": user_id
        })
        
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Prepare update data
        update_fields = {}
        if update_data.name is not None:
            update_fields["name"] = update_data.name
        if update_data.description is not None:
            update_fields["description"] = update_data.description
        if update_data.rules is not None:
            update_fields["rules"] = update_data.rules
            # Increment version when rules change
            current_version = float(playbook["version"])
            update_fields["version"] = str(current_version + 0.1)
        if update_data.is_active is not None:
            update_fields["is_active"] = update_data.is_active
        
        # Update in MongoDB
        result = collection.update_one(
            {"_id": playbook_obj_id},
            {"$set": update_fields}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update playbook"
            )
        
        # Get updated playbook
        updated_playbook = collection.find_one({"_id": playbook_obj_id})
        
        logger.info(f"Playbook updated: {playbook_id} by user {current_user.id}")
        
        return LegalPlaybookResponse(
            id=str(updated_playbook["_id"]),
            name=updated_playbook["name"],
            description=updated_playbook["description"],
            version=updated_playbook["version"],
            is_active=updated_playbook["is_active"],
            created_at=updated_playbook["created_at"]
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
    playbook_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete playbook"""
    try:
        collection = get_legal_playbooks_collection()
        
        # Validate ObjectId
        try:
            playbook_obj_id = ObjectId(playbook_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid playbook ID format"
            )
        
        user_id = ObjectId(current_user.id)
        
        # Find and delete playbook
        result = collection.delete_one({
            "_id": playbook_obj_id,
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        logger.info(f"Playbook deleted: {playbook_id} by user {current_user.id}")
        return {"message": "Playbook deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting playbook {playbook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete playbook"
        )