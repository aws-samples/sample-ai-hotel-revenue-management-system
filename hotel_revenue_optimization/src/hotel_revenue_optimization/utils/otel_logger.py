import logging
import json
import sys
import time
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import traceback

# AWS Distro for OpenTelemetry (ADOT) imports
from aws_otel.genai import configure_opentelemetry
from aws_otel.genai.trace import GenAITracer
from aws_otel.genai.metrics import GenAIMetrics
from aws_otel.genai.resource import GenAIResource
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.semconv.resource import ResourceAttributes

# Configure JSON logging to console
class JsonFormatter(logging.Formatter):
    """JSON log formatter that outputs logs in a structured format"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        
        # Add extra fields from the record
        if hasattr(record, 'event_type'):
            log_data['event_type'] = record.event_type
            
        if hasattr(record, 'agent'):
            log_data['agent'] = record.agent
            
        if hasattr(record, 'model'):
            log_data['model'] = record.model
            
        if hasattr(record, 'task'):
            log_data['task'] = record.task
            
        if hasattr(record, 'crew'):
            log_data['crew'] = record.crew
            
        if hasattr(record, 'duration_seconds'):
            log_data['duration_seconds'] = record.duration_seconds
            
        if hasattr(record, 'status'):
            log_data['status'] = record.status
            
        # Add any other extra attributes
        for key, value in record.__dict__.items():
            if key not in ('args', 'asctime', 'created', 'exc_info', 'exc_text', 
                          'filename', 'funcName', 'id', 'levelname', 'levelno', 
                          'lineno', 'module', 'msecs', 'message', 'msg', 'name', 
                          'pathname', 'process', 'processName', 'relativeCreated', 
                          'stack_info', 'thread', 'threadName', 'event_type', 
                          'agent', 'model', 'task', 'crew', 'duration_seconds', 'status'):
                if not key.startswith('_') and not callable(value):
                    try:
                        # Try to serialize the value to ensure it's JSON-compatible
                        json.dumps({key: value})
                        log_data[key] = value
                    except (TypeError, OverflowError):
                        # If not serializable, convert to string
                        log_data[key] = str(value)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data)

# Configure root logger
logger = logging.getLogger("HotelRevenueOptimization")
logger.setLevel(logging.INFO)

# Create console handler with JSON formatter
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(JsonFormatter())
logger.addHandler(console_handler)

# Initialize AWS Distro for OpenTelemetry (ADOT)
service_name = os.environ.get("OTEL_SERVICE_NAME", "hotel-revenue-optimization")
service_version = os.environ.get("OTEL_SERVICE_VERSION", "1.0.0")

# Configure OpenTelemetry with AWS Distro for GenAI
configure_opentelemetry(
    service_name=service_name,
    service_version=service_version,
    resource_attributes={
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: service_version,
        "application.type": "hotel-revenue-optimization",
        "deployment.environment": os.environ.get("DEPLOYMENT_ENVIRONMENT", "development")
    }
)

# Get the GenAI tracer and metrics
genai_tracer = GenAITracer()
genai_metrics = GenAIMetrics()

class OtelLogger:
    """
    AWS Distro for OpenTelemetry (ADOT) focused logger for GenAI that creates spans and logs to console in JSON format.
    """
    
    def __init__(self):
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self.failed_tasks: List[Dict[str, Any]] = []
        self.spans: Dict[str, Any] = {}
    
    def start_operation(self, 
                       operation_id: str, 
                       agent_name: str, 
                       model_name: str, 
                       operation_type: str, 
                       task_name: Optional[str] = None,
                       crew_name: Optional[str] = "HotelRevenueOptimizationCrew",
                       details: Optional[Dict[str, Any]] = None):
        """
        Start an operation and create an OpenTelemetry span
        
        Args:
            operation_id: Unique identifier for the operation
            agent_name: Name of the agent performing the operation
            model_name: Name of the model being used
            operation_type: Type of operation (e.g., "MODEL_INVOKE", "TASK_EXECUTION")
            task_name: Optional name of the task being executed
            crew_name: Optional name of the crew
            details: Additional details about the operation
        """
        # Create structured log data
        log_data = {
            "event_type": operation_type,
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
            for key, value in details.items():
                log_data[key] = value
        
        # Log the start of the operation at INFO level
        extra = {**log_data}
        logger.info(f"{operation_type} STARTED | Agent: {agent_name} | Model: {model_name} | Task: {task_name or 'N/A'} | Crew: {crew_name}", 
                   extra=extra)
        
        # Create OpenTelemetry span using GenAI tracer
        if operation_type == "MODEL_INVOKE":
            # For model invocations, use the GenAI specific span
            span = genai_tracer.start_span(
                name=f"{operation_type}",
                model=model_name,
                attributes={
                    "agent.name": agent_name,
                    "operation.id": operation_id,
                    "operation.type": operation_type
                }
            )
            
            # Record model invocation metrics
            genai_metrics.record_model_invocation_start(model_name)
        else:
            # For other operations, use regular span
            span = trace.get_tracer(service_name).start_span(
                name=f"{operation_type}",
                kind=trace.SpanKind.INTERNAL
            )
            
            # Add attributes to span
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("model.name", model_name)
            span.set_attribute("operation.id", operation_id)
            span.set_attribute("operation.type", operation_type)
        
        if task_name:
            span.set_attribute("task.name", task_name)
            
        if crew_name:
            span.set_attribute("crew.name", crew_name)
            
        # Add details to span
        if details:
            for key, value in details.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(f"details.{key}", value)
                elif value is None:
                    span.set_attribute(f"details.{key}", "null")
                else:
                    try:
                        # Try to convert to JSON string for complex objects
                        span.set_attribute(f"details.{key}", json.dumps(value))
                    except:
                        # If not serializable, convert to string
                        span.set_attribute(f"details.{key}", str(value))
        
        # Store the span for later use
        self.spans[operation_id] = {
            "span": span,
            "operation_type": operation_type,
            "model_name": model_name,
            "start_time": time.time()
        }
    
    def end_operation(self, 
                     operation_id: str, 
                     status: str = "completed", 
                     result: Optional[Dict[str, Any]] = None, 
                     error: Optional[str] = None,
                     error_details: Optional[Dict[str, Any]] = None):
        """
        End an operation, log the results, and end OpenTelemetry span
        
        Args:
            operation_id: Unique identifier for the operation
            status: Status of the operation (completed, failed, etc.)
            result: Result of the operation
            error: Error message if the operation failed
            error_details: Additional error details
        """
        if operation_id not in self.spans:
            logger.warning(f"Operation {operation_id} was never started")
            return
        
        # Get the span info
        span_info = self.spans[operation_id]
        span = span_info["span"]
        operation_type = span_info["operation_type"]
        model_name = span_info["model_name"]
        start_time = span_info["start_time"]
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get span attributes
        agent_name = span.attributes.get("agent.name", "unknown")
        task_name = span.attributes.get("task.name")
        crew_name = span.attributes.get("crew.name")
        
        # Create structured log data
        log_data = {
            "event_type": operation_type,
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
            for key, value in result.items():
                log_data[f"result_{key}"] = value
                
            # If this is a task result, store it for later use
            if operation_type == "TASK_EXECUTION" and task_name:
                self.task_results[task_name] = {
                    "status": status,
                    "result": result,
                    "agent": agent_name,
                    "duration_seconds": duration
                }
        
        if error:
            log_data["error"] = error
            
            if error_details:
                for key, value in error_details.items():
                    log_data[f"error_detail_{key}"] = value
                
            # If this is a task error, store it for later use
            if operation_type == "TASK_EXECUTION" and task_name:
                self.failed_tasks.append({
                    "task_name": task_name,
                    "agent_name": agent_name,
                    "error": error,
                    "error_details": error_details or {},
                    "duration_seconds": duration
                })
        
        # Log the completion of the operation
        log_message = f"{operation_type} {status.upper()} | Agent: {agent_name} | Model: {model_name} | Duration: {duration:.2f}s"
        
        if task_name:
            log_message += f" | Task: {task_name}"
            
        if crew_name:
            log_message += f" | Crew: {crew_name}"
        
        extra = {**log_data}
        
        if status == "completed":
            logger.info(log_message, extra=extra)
        else:
            error_msg = f" | Error: {error}" if error else ""
            logger.error(f"{log_message}{error_msg}", extra=extra)
        
        # Add result attributes to span
        if result:
            for key, value in result.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(f"result.{key}", value)
                elif value is None:
                    span.set_attribute(f"result.{key}", "null")
                else:
                    try:
                        # Try to convert to JSON string for complex objects
                        span.set_attribute(f"result.{key}", json.dumps(value))
                    except:
                        # If not serializable, convert to string
                        span.set_attribute(f"result.{key}", str(value))
        
        # Set span status based on operation status
        if status == "completed":
            span.set_status(Status(StatusCode.OK))
            
            # Record model invocation success metrics if this is a model invocation
            if operation_type == "MODEL_INVOKE":
                genai_metrics.record_model_invocation_success(
                    model_name=model_name,
                    latency_ms=duration * 1000,  # Convert to milliseconds
                    input_tokens=result.get("estimated_input_tokens", 0) if result else 0,
                    output_tokens=result.get("estimated_output_tokens", 0) if result else 0
                )
        else:
            span.set_status(Status(StatusCode.ERROR, error or "Unknown error"))
            
            # Record model invocation failure metrics if this is a model invocation
            if operation_type == "MODEL_INVOKE":
                genai_metrics.record_model_invocation_failure(
                    model_name=model_name,
                    error_type=error_details.get("error_code", "unknown") if error_details else "unknown",
                    latency_ms=duration * 1000  # Convert to milliseconds
                )
            
            if error:
                span.record_exception(
                    exception=Exception(error),
                    attributes=error_details if error_details else {}
                )
        
        # End the span
        span.end()
        
        # Remove the span from the dictionary
        del self.spans[operation_id]
    
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
        with trace.get_tracer(service_name).start_as_current_span(name=f"EVENT_{event_type}") as span:
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
                elif value is None:
                    span.set_attribute(f"details.{key}", "null")
                else:
                    try:
                        # Try to convert to JSON string for complex objects
                        span.set_attribute(f"details.{key}", json.dumps(value))
                    except:
                        # If not serializable, convert to string
                        span.set_attribute(f"details.{key}", str(value))
            
            # Create structured log data
            log_data = {
                "event_type": event_type,
                "agent": agent_name,
                "model": model_name
            }
            
            if task_name:
                log_data["task"] = task_name
                
            if crew_name:
                log_data["crew"] = crew_name
                
            # Add details to log data
            for key, value in details.items():
                log_data[key] = value
            
            # Log the event at the appropriate level
            log_message = f"EVENT: {event_type} | Agent: {agent_name} | Model: {model_name}"
            
            if task_name:
                log_message += f" | Task: {task_name}"
                
            if crew_name:
                log_message += f" | Crew: {crew_name}"
            
            extra = {**log_data}
            
            if level == "INFO":
                logger.info(log_message, extra=extra)
            elif level == "WARNING":
                logger.warning(log_message, extra=extra)
            elif level == "ERROR":
                logger.error(log_message, extra=extra)
            elif level == "DEBUG":
                logger.debug(log_message, extra=extra)
    
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
        
        # Create a span for the exception
        with trace.get_tracer(service_name).start_as_current_span(name=f"EXCEPTION") as span:
            # Add attributes to span
            span.set_attribute("error.type", exception.__class__.__name__)
            span.set_attribute("error.message", str(exception))
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("model.name", model_name)
            
            if task_name:
                span.set_attribute("task.name", task_name)
                
            if crew_name:
                span.set_attribute("crew.name", crew_name)
                
            # Add details to span
            if details:
                for key, value in details.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"details.{key}", value)
                    elif value is None:
                        span.set_attribute(f"details.{key}", "null")
                    else:
                        try:
                            # Try to convert to JSON string for complex objects
                            span.set_attribute(f"details.{key}", json.dumps(value))
                        except:
                            # If not serializable, convert to string
                            span.set_attribute(f"details.{key}", str(value))
            
            # Set span status
            span.set_status(Status(StatusCode.ERROR, str(exception)))
            
            # Record exception
            span.record_exception(exception)
            
            # Create structured log data
            log_data = {
                "event_type": "EXCEPTION",
                "agent": agent_name,
                "model": model_name,
                "error_type": exception.__class__.__name__,
                "error_message": str(exception),
                "stack_trace": stack_trace
            }
            
            if task_name:
                log_data["task"] = task_name
                
            if crew_name:
                log_data["crew"] = crew_name
                
            # Add details to log data
            if details:
                for key, value in details.items():
                    log_data[key] = value
            
            # Log the exception
            log_message = f"EXCEPTION: {exception.__class__.__name__} | {str(exception)} | Agent: {agent_name} | Model: {model_name}"
            
            if task_name:
                log_message += f" | Task: {task_name}"
                
            if crew_name:
                log_message += f" | Crew: {crew_name}"
            
            extra = {**log_data}
            logger.error(log_message, extra=extra)
    
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

# Create a singleton instance
otel_logger = OtelLogger()
