import threading
import time
import uuid
from datetime import datetime
from app.api.agentcore import invoke_agentcore
from app.services.history import QueryHistoryService
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class AsyncQueryProcessor:
    def __init__(self):
        pass
    
    def process_query_async(self, user_id, timestamp, query_data, query_type):
        """Process query asynchronously in background thread"""
        # Get the current app context
        app = current_app._get_current_object()
        
        thread = threading.Thread(
            target=self._process_query_background,
            args=(app, user_id, timestamp, query_data, query_type)
        )
        thread.daemon = True
        thread.start()
        logger.info(f"Started async processing for query {timestamp}")
    
    def _process_query_background(self, app, user_id, timestamp, query_data, query_type):
        """Background processing of query with app context"""
        with app.app_context():
            try:
                logger.info(f"Processing query {timestamp} in background")
                
                # Initialize history service within app context
                history_service = QueryHistoryService()
                
                # Generate session ID for this query
                session_id = str(uuid.uuid4())
                
                # Call AgentCore with session ID
                result = invoke_agentcore(query_data, session_id=session_id)
                
                # Update history with result
                if result and result.get('status') == 'success':
                    history_service.save_query_result(
                        user_id=user_id,
                        timestamp=timestamp,
                        query_type=query_type,
                        query_summary=query_data.get('query', 'Query processed'),
                        result_data=result,
                        result_status='success',
                        result_summary=result.get('report', '')[:200] + '...' if result.get('report') else 'Analysis completed'
                    )
                    logger.info(f"Query {timestamp} completed successfully")
                else:
                    history_service.save_query_result(
                        user_id=user_id,
                        timestamp=timestamp,
                        query_type=query_type,
                        query_summary=query_data.get('query', 'Query processed'),
                        result_data=result or {},
                        result_status='failed',
                        result_summary='Processing failed'
                    )
                    logger.error(f"Query {timestamp} failed")
                    
            except Exception as e:
                logger.error(f"Error processing query {timestamp}: {e}")
                # For certain errors, keep as processing and let it retry
                if "Working outside of request context" in str(e) or "AGENTCORE_RUNTIME_ARN not configured" in str(e):
                    logger.info(f"Temporary error for query {timestamp}, keeping as processing")
                    return
                
                # Only mark as failed for permanent errors
                history_service = QueryHistoryService()
                history_service.save_query_result(
                    user_id=user_id,
                    timestamp=timestamp,
                    query_type=query_type,
                    query_summary=query_data.get('query', 'Query processed'),
                    result_data={'error': str(e)},
                    result_status='failed',
                    result_summary=f'Error: {str(e)}'
                )

# Global instance
async_processor = AsyncQueryProcessor()
