from celery import current_task
from bson import ObjectId
from app.celery_app import celery_app
from app.database import get_documents_collection, get_clauses_collection, get_legal_playbooks_collection
from app.models import Document, Clause, DocumentStatus, RiskLevel
from app.services.document_parser import DocumentParser
from app.services.analysis_service import AnalysisService
from typing import Dict, Any
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='app.tasks.process_document')
def process_document(self, document_id: str) -> Dict[str, Any]:
    """
    Asynchronous task to process uploaded document:
    1. Parse document (PDF/DOCX)
    2. Extract text
    3. Run analysis engine
    4. Update document status
    """
    try:
        # Update task progress
        current_task.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting document processing'})
        
        # Get document from database
        documents_collection = get_documents_collection()
        
        # Validate ObjectId
        try:
            document_obj_id = ObjectId(document_id)
        except:
            raise Exception(f"Invalid document ID format: {document_id}")
        
        document = documents_collection.find_one({"_id": document_obj_id})
        if not document:
            raise Exception(f"Document {document_id} not found")
        
        # Update document status to processing
        documents_collection.update_one(
            {"_id": document_obj_id},
            {
                "$set": {
                    "status": DocumentStatus.PROCESSING,
                    "processing_started_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Starting processing for document {document_id}: {document['original_filename']}")
        
        # Step 1: Parse document and extract text
        current_task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Parsing document'})
        
        parser = DocumentParser()
        extracted_text = parser.extract_text(document['file_path'], document['mime_type'])
        
        if not extracted_text:
            raise Exception("Failed to extract text from document")
        
        # Update document with extracted text length
        documents_collection.update_one(
            {"_id": document_obj_id},
            {"$set": {"extracted_text_length": len(extracted_text)}}
        )
        
        current_task.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Text extracted successfully'})
        
        # Step 2: Run analysis engine
        current_task.update_state(state='PROGRESS', meta={'progress': 40, 'status': 'Running legal analysis'})
        
        analysis_service = AnalysisService()
        analysis_result = analysis_service.analyze_document(extracted_text, document_id)
        
        current_task.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Saving analysis results'})
        
        # Step 3: Save clauses to database
        clauses_collection = get_clauses_collection()
        total_clauses = 0
        
        for clause_data in analysis_result.get('clauses', []):
            clause_doc = {
                "document_id": document_obj_id,
                "text": clause_data['text'],
                "category": clause_data['category'],
                "subcategory": clause_data.get('subcategory'),
                "risk_score": clause_data['risk_score'],
                "risk_level": clause_data['risk_level'],
                "confidence_score": clause_data['confidence_score'],
                "start_position": clause_data.get('start_position'),
                "end_position": clause_data.get('end_position'),
                "page_number": clause_data.get('page_number'),
                "analysis_metadata": clause_data.get('metadata', {}),
                "recommendations": clause_data.get('recommendations'),
                "created_at": datetime.utcnow()
            }
            clauses_collection.insert_one(clause_doc)
            total_clauses += 1
        
        # Update document status
        processing_completed_at = datetime.utcnow()
        documents_collection.update_one(
            {"_id": document_obj_id},
            {
                "$set": {
                    "status": DocumentStatus.COMPLETE,
                    "processing_completed_at": processing_completed_at,
                    "total_clauses_found": total_clauses,
                    "document_metadata": analysis_result.get('metadata', {})
                }
            }
        )
        
        current_task.update_state(
            state='SUCCESS', 
            meta={
                'progress': 100, 
                'status': 'Analysis completed successfully',
                'total_clauses': total_clauses,
                'document_id': document_id
            }
        )
        
        logger.info(f"Document {document_id} processed successfully. Found {total_clauses} clauses.")
        
        return {
            'document_id': document_id,
            'status': 'complete',
            'total_clauses': total_clauses,
            'processing_time': (processing_completed_at - document['processing_started_at']).total_seconds()
        }
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update document status to error
        try:
            documents_collection = get_documents_collection()
            try:
                document_obj_id = ObjectId(document_id)
            except:
                document_obj_id = document_id
            
            documents_collection.update_one(
                {"_id": document_obj_id},
                {
                    "$set": {
                        "status": DocumentStatus.ERROR,
                        "error_message": str(e),
                        "processing_completed_at": datetime.utcnow()
                    }
                }
            )
        except Exception as db_error:
            logger.error(f"Failed to update document status to error: {db_error}")
        
        # Update task state
        current_task.update_state(
            state='FAILURE',
            meta={
                'progress': 0,
                'status': f'Processing failed: {str(e)}',
                'error': str(e)
            }
        )
        
        raise e

@celery_app.task(bind=True, name='app.tasks.analyze_document_with_playbook')
def analyze_document_with_playbook(self, document_id: str, playbook_id: str) -> Dict[str, Any]:
    """
    Asynchronous task to re-analyze document with specific legal playbook
    """
    try:
        current_task.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting playbook analysis'})
        
        # Get document and playbook
        documents_collection = get_documents_collection()
        playbooks_collection = get_legal_playbooks_collection()
        
        # Validate ObjectIds
        try:
            document_obj_id = ObjectId(document_id)
            playbook_obj_id = ObjectId(playbook_id)
        except:
            raise Exception(f"Invalid ID format: document_id={document_id}, playbook_id={playbook_id}")
        
        document = documents_collection.find_one({"_id": document_obj_id})
        if not document:
            raise Exception(f"Document {document_id} not found")
        
        playbook = playbooks_collection.find_one({"_id": playbook_obj_id})
        if not playbook:
            raise Exception(f"Playbook {playbook_id} not found")
        
        # REFINEMENT_HOOK: implement_playbook_comparison_logic
        # This is where we would implement sophisticated playbook-based analysis
        # For now, we'll use the standard analysis engine
        
        current_task.update_state(state='PROGRESS', meta={'progress': 50, 'status': 'Applying playbook rules'})
        
        analysis_service = AnalysisService()
        
        # Parse document again to get text
        parser = DocumentParser()
        extracted_text = parser.extract_text(document['file_path'], document['mime_type'])
        
        # Run analysis with playbook context
        analysis_result = analysis_service.analyze_with_playbook(extracted_text, document_id, playbook_id)
        
        current_task.update_state(state='SUCCESS', meta={'progress': 100, 'status': 'Playbook analysis completed'})
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing document {document_id} with playbook {playbook_id}: {str(e)}")
        current_task.update_state(
            state='FAILURE',
            meta={
                'progress': 0,
                'status': f'Playbook analysis failed: {str(e)}', 
                'error': str(e)
            }
        )
        raise e

@celery_app.task(name='app.tasks.cleanup_old_documents')
def cleanup_old_documents() -> Dict[str, Any]:
    """
    Periodic task to cleanup old documents and analysis results
    """
    try:
        # REFINEMENT_HOOK: implement_document_cleanup_logic
        # This would implement logic to clean up old documents based on retention policies
        logger.info("Document cleanup task executed (stub implementation)")
        return {"status": "success", "cleaned": 0}
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        raise e