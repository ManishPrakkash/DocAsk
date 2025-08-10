from celery import current_task
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Document, Clause, DocumentStatus, RiskLevel
from app.services.document_parser import DocumentParser
from app.services.analysis_service import AnalysisService
from typing import Dict, Any
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

def get_db_session():
    """Get database session for Celery tasks"""
    return SessionLocal()

@celery_app.task(bind=True, name='app.tasks.process_document')
def process_document(self, document_id: int) -> Dict[str, Any]:
    """
    Asynchronous task to process uploaded document:
    1. Parse document (PDF/DOCX)
    2. Extract text
    3. Run analysis engine
    4. Update document status
    """
    db = get_db_session()
    
    try:
        # Update task progress
        current_task.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting document processing'})
        
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document {document_id} not found")
        
        # Update document status to processing
        document.status = DocumentStatus.PROCESSING
        document.processing_started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Starting processing for document {document_id}: {document.original_filename}")
        
        # Step 1: Parse document and extract text
        current_task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Parsing document'})
        
        parser = DocumentParser()
        extracted_text = parser.extract_text(document.file_path, document.mime_type)
        
        if not extracted_text:
            raise Exception("Failed to extract text from document")
        
        # Update document with extracted text length
        document.extracted_text_length = len(extracted_text)
        db.commit()
        
        current_task.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Text extracted successfully'})
        
        # Step 2: Run analysis engine
        current_task.update_state(state='PROGRESS', meta={'progress': 40, 'status': 'Running legal analysis'})
        
        analysis_service = AnalysisService()
        analysis_result = analysis_service.analyze_document(extracted_text, document_id)
        
        current_task.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Saving analysis results'})
        
        # Step 3: Save clauses to database
        total_clauses = 0
        for clause_data in analysis_result.get('clauses', []):
            clause = Clause(
                document_id=document_id,
                text=clause_data['text'],
                category=clause_data['category'],
                subcategory=clause_data.get('subcategory'),
                risk_score=clause_data['risk_score'],
                risk_level=RiskLevel(clause_data['risk_level']),
                confidence_score=clause_data['confidence_score'],
                start_position=clause_data.get('start_position'),
                end_position=clause_data.get('end_position'),
                page_number=clause_data.get('page_number'),
                analysis_metadata=clause_data.get('metadata', {}),
                recommendations=clause_data.get('recommendations')
            )
            db.add(clause)
            total_clauses += 1
        
        # Update document status
        document.status = DocumentStatus.COMPLETE
        document.processing_completed_at = datetime.utcnow()
        document.total_clauses_found = total_clauses
        document.document_metadata = analysis_result.get('metadata', {})
        
        db.commit()
        
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
            'processing_time': (document.processing_completed_at - document.processing_started_at).total_seconds()
        }
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update document status to error
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = DocumentStatus.ERROR
                document.error_message = str(e)
                document.processing_completed_at = datetime.utcnow()
                db.commit()
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
        
    finally:
        db.close()

@celery_app.task(bind=True, name='app.tasks.analyze_document_with_playbook')
def analyze_document_with_playbook(self, document_id: int, playbook_id: int) -> Dict[str, Any]:
    """
    Asynchronous task to re-analyze document with specific legal playbook
    """
    db = get_db_session()
    
    try:
        current_task.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Starting playbook analysis'})
        
        # Get document and playbook
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception(f"Document {document_id} not found")
        
        # REFINEMENT_HOOK: implement_playbook_comparison_logic
        # This is where we would implement sophisticated playbook-based analysis
        # For now, we'll use the standard analysis engine
        
        current_task.update_state(state='PROGRESS', meta={'progress': 50, 'status': 'Applying playbook rules'})
        
        analysis_service = AnalysisService()
        
        # Parse document again to get text
        parser = DocumentParser()
        extracted_text = parser.extract_text(document.file_path, document.mime_type)
        
        # Run analysis with playbook context
        analysis_result = analysis_service.analyze_with_playbook(extracted_text, document_id, playbook_id)
        
        current_task.update_state(state='SUCCESS', meta={'progress': 100, 'status': 'Playbook analysis completed'})
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing document {document_id} with playbook {playbook_id}: {str(e)}")
        current_task.update_state(
            state='FAILURE',
            meta={'progress': 0, 'status': f'Playbook analysis failed: {str(e)}', 'error': str(e)}
        )
        raise e
    finally:
        db.close()

@celery_app.task(name='app.tasks.cleanup_old_documents')
def cleanup_old_documents() -> Dict[str, Any]:
    """
    Periodic task to cleanup old documents and analysis results
    """
    db = get_db_session()
    
    try:
        # REFINEMENT_HOOK: implement_document_cleanup_logic
        # This would implement logic to clean up old documents based on retention policies
        logger.info("Document cleanup task executed (stub implementation)")
        return {"status": "success", "cleaned": 0}
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        raise e
    finally:
        db.close()