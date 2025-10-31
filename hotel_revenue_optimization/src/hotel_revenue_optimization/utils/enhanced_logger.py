import logging
import time
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import traceback

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.semconv.resource import ResourceAttributes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize OpenTelemetry
resource = Resource(attributes={
    ResourceAttributes.SERVICE_NAME: "hotel-revenue-optimization",
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer("hotel_revenue_optimization")

# Configure OTLP exporter if endpoint is provided
otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
if otlp_endpoint:
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

class EnhancedLogger:
    """
    Enhanced logger for tracking performance and operational metrics
    of the Hotel Revenue Optimization system with OpenTelemetry integration.
    """
    
    def __init__(self, log_to_file: bool = True):
        self.logger = logging.getLogger("HotelRevenueOptimization")
        self.start_times: Dict[str, float] = {}
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.log_to_file = log_to_file
        self.spans: Dict[str, Any] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self.failed_tasks: List[Dict[str, Any]] = []
        
        # Create output directory if it doesn't exist
        if self.log_to_file:
            os.makedirs("output/logs", exist_ok=True)
            
            # Create a log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = f"output/logs/performance_{timestamp}.json"
            
            # Initialize the log file with an empty array
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def start_operation(self, 
                        operation_id: str, 
                        agent_name: str, 
                        model_name: str, 
                        operation_type: str, 
                        task_name: Optional[str] = None,
                        crew_name: Optional[str] = "HotelRevenueOptimizationCrew",
                        details: Optional[Dict[str, Any]] = None):
        """
        Start timing an operation (API call, task execution, etc.) and create OpenTelemetry span
        
        Args:
            operation_id: Unique identifier for the operation
            agent_name: Name of the agent performing the operation
            model_name: Name of the model being used
            operation_type: Type of operation (e.g., "API_CALL", "TASK_EXECUTION")
            task_name: Optional name of the task being executed
            crew_name: Optional name of the crew
            details: Additional details about the operation
        """
        self.start_times[operation_id] = time.time()
        
        # Create structured log data
        log_data = {
            "event": operation_type,
            "status": "started",
            "agent": agent_name,
            "model": model_name,
            "operation_id": operation_id
        }
        
        if task_name:
            log_data["task"] = task_name
            
        if crew_name:
            log_data["crew"] = crew_name
            
        if details:
            log_data["details"] = details
        
        # Log the start of the operation at INFO level
        self.logger.info(f"{operation_type} STARTED | Agent: {agent_name} | Model: {model_name} | Task: {task_name or 'N/A'} | Crew: {crew_name}", extra=log_data)
        
        # Store initial metrics
        self.metrics[operation_id] = {
            "agent": agent_name,
            "model": model_name,
            "operation_type": operation_type,
            "task": task_name,
            "crew": crew_name,
            "start_time": datetime.now().isoformat(),
            "status": "started",
            "details": details or {}
        }
        
        # Create OpenTelemetry span
        span = tracer.start_span(
            name=f"{operation_type}",
            kind=trace.SpanKind.INTERNAL
        )
        
        # Add attributes to span
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("model.name", model_name)
        span.set_attribute("operation.id", operation_id)
        
        if task_name:
            span.set_attribute("task.name", task_name)
            
        if crew_name:
            span.set_attribute("crew.name", crew_name)
            
        if details:
            for key, value in details.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(f"details.{key}", value)
        
        # Store the span for later use
        self.spans[operation_id] = span
    
    def end_operation(self, 
                     operation_id: str, 
                     status: str = "completed", 
                     result: Optional[Dict[str, Any]] = None, 
                     error: Optional[str] = None,
                     error_details: Optional[Dict[str, Any]] = None):
        """
        End timing an operation, log the results, and end OpenTelemetry span
        
        Args:
            operation_id: Unique identifier for the operation
            status: Status of the operation (completed, failed, etc.)
            result: Result of the operation
            error: Error message if the operation failed
            error_details: Additional error details
        """
        if operation_id not in self.start_times:
            self.logger.warning(f"Operation {operation_id} was never started")
            return
        
        # Calculate duration
        duration = time.time() - self.start_times[operation_id]
        
        # Get the operation details
        metrics = self.metrics.get(operation_id, {})
        agent_name = metrics.get("agent", "unknown")
        model_name = metrics.get("model", "unknown")
        operation_type = metrics.get("operation_type", "unknown")
        task_name = metrics.get("task", "unknown")
        crew_name = metrics.get("crew", "unknown")
        
        # Update metrics
        metrics.update({
            "end_time": datetime.now().isoformat(),
            "duration_seconds": duration,
            "status": status
        })
        
        if result:
            metrics["result"] = result
            
            # If this is a task result, store it for later use
            if operation_type == "TASK_EXECUTION" and task_name:
                self.task_results[task_name] = {
                    "status": status,
                    "result": result,
                    "agent": agent_name,
                    "duration_seconds": duration
                }
        
        if error:
            metrics["error"] = error
            
            if error_details:
                metrics["error_details"] = error_details
                
            # If this is a task error, store it for later use
            if operation_type == "TASK_EXECUTION" and task_name:
                self.failed_tasks.append({
                    "task_name": task_name,
                    "agent_name": agent_name,
                    "error": error,
                    "error_details": error_details or {},
                    "duration_seconds": duration
                })
        
        # Create structured log data
        log_data = {
            "event": operation_type,
            "status": status,
            "agent": agent_name,
            "model": model_name,
            "operation_id": operation_id,
            "duration_seconds": duration
        }
        
        if task_name:
            log_data["task"] = task_name
            
        if crew_name:
            log_data["crew"] = crew_name
            
        if result:
            log_data["result"] = result
            
        if error:
            log_data["error"] = error
            
            if error_details:
                log_data["error_details"] = error_details
        
        # Log the completion of the operation
        log_message = f"{operation_type} {status.upper()} | Agent: {agent_name} | Model: {model_name} | Task: {task_name or 'N/A'} | Crew: {crew_name} | Duration: {duration:.2f}s"
        
        if status == "completed":
            self.logger.info(log_message, extra=log_data)
        else:
            error_msg = f" | Error: {error}" if error else ""
            self.logger.error(f"{log_message}{error_msg}", extra=log_data)
        
        # End OpenTelemetry span
        if operation_id in self.spans:
            span = self.spans[operation_id]
            
            # Add result attributes to span
            if result:
                for key, value in result.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"result.{key}", value)
            
            # Set span status based on operation status
            if status == "completed":
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR, error or "Unknown error"))
                
                if error:
                    span.record_exception(
                        exception=Exception(error),
                        attributes=error_details if error_details else {}
                    )
            
            # End the span
            span.end()
            
            # Remove the span from the dictionary
            del self.spans[operation_id]
        
        # Write to log file if enabled
        if self.log_to_file:
            self._append_to_log_file(metrics)
    
    def log_event(self, 
                 event_type: str, 
                 agent_name: str, 
                 model_name: str, 
                 details: Dict[str, Any],
                 task_name: Optional[str] = None,
                 crew_name: Optional[str] = "HotelRevenueOptimizationCrew",
                 level: str = "INFO"):
        """
        Log a general event with OpenTelemetry span
        
        Args:
            event_type: Type of event
            agent_name: Name of the agent
            model_name: Name of the model
            details: Event details
            task_name: Optional name of the task
            crew_name: Optional name of the crew
            level: Log level (INFO, WARNING, ERROR, DEBUG)
        """
        # Create a span for the event
        with tracer.start_as_current_span(name=f"EVENT_{event_type}") as span:
            # Add attributes to span
            span.set_attribute("event.type", event_type)
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("model.name", model_name)
            
            if task_name:
                span.set_attribute("task.name", task_name)
                
            if crew_name:
                span.set_attribute("crew.name", crew_name)
                
            # Add details to span
            for key, value in details.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(f"details.{key}", value)
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "agent": agent_name,
                "model": model_name,
                "details": details
            }
            
            if task_name:
                log_entry["task"] = task_name
                
            if crew_name:
                log_entry["crew"] = crew_name
            
            # Create structured log data
            log_data = {
                "event": event_type,
                "agent": agent_name,
                "model": model_name
            }
            
            if task_name:
                log_data["task"] = task_name
                
            if crew_name:
                log_data["crew"] = crew_name
                
            log_data.update(details)
            
            # Log the event at the appropriate level
            log_message = f"EVENT: {event_type} | Agent: {agent_name} | Model: {model_name}"
            
            if task_name:
                log_message += f" | Task: {task_name}"
                
            if crew_name:
                log_message += f" | Crew: {crew_name}"
            
            if level == "INFO":
                self.logger.info(log_message, extra=log_data)
            elif level == "WARNING":
                self.logger.warning(log_message, extra=log_data)
            elif level == "ERROR":
                self.logger.error(log_message, extra=log_data)
            elif level == "DEBUG":
                self.logger.debug(log_message, extra=log_data)
            
            # Write to log file if enabled
            if self.log_to_file:
                self._append_to_log_file(log_entry)
    
    def log_exception(self, 
                     exception: Exception, 
                     agent_name: str = "system", 
                     model_name: str = "none",
                     task_name: Optional[str] = None,
                     crew_name: Optional[str] = "HotelRevenueOptimizationCrew",
                     details: Optional[Dict[str, Any]] = None):
        """
        Log an exception with stack trace and OpenTelemetry span
        
        Args:
            exception: The exception to log
            agent_name: Name of the agent
            model_name: Name of the model
            task_name: Optional name of the task
            crew_name: Optional name of the crew
            details: Additional details
        """
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        # Create event details
        event_details = {
            "error_type": exception.__class__.__name__,
            "error_message": str(exception),
            "stack_trace": stack_trace
        }
        
        if details:
            event_details.update(details)
        
        # Log the exception
        self.log_event(
            event_type="EXCEPTION",
            agent_name=agent_name,
            model_name=model_name,
            task_name=task_name,
            crew_name=crew_name,
            details=event_details,
            level="ERROR"
        )
    
    def get_task_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the results of all completed tasks
        
        Returns:
            Dictionary of task results
        """
        return self.task_results
    
    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """
        Get the list of failed tasks
        
        Returns:
            List of failed tasks
        """
        return self.failed_tasks
    
    def prepare_response_with_partial_results(self) -> Dict[str, Any]:
        """
        Prepare a response with partial results for tasks that completed successfully
        and placeholders for tasks that failed
        
        Returns:
            Response dictionary with partial results
        """
        response = {
            "status": "partial_success" if self.failed_tasks else "success",
            "completed_tasks": list(self.task_results.keys()),
            "failed_tasks": [task["task_name"] for task in self.failed_tasks],
            "results": {}
        }
        
        # Add completed task results
        for task_name, task_result in self.task_results.items():
            response["results"][task_name] = task_result.get("result", {})
        
        # Add placeholders for failed tasks
        for task in self.failed_tasks:
            task_name = task["task_name"]
            response["results"][task_name] = {
                "placeholder": f"Task {task_name} failed to complete",
                "error": task["error"],
                "error_details": task["error_details"]
            }
        
        return response
    
    def _append_to_log_file(self, log_entry: Dict[str, Any]):
        """Append a log entry to the JSON log file"""
        try:
            # Read existing logs
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Append new log
            logs.append(log_entry)
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")

# Create a singleton instance
enhanced_logger = EnhancedLogger()
