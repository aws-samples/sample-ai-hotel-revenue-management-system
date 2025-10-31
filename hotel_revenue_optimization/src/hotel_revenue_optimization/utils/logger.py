import logging
import time
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class PerformanceLogger:
    """
    Custom logger for tracking performance and operational metrics
    of the Hotel Revenue Optimization system.
    """
    
    def __init__(self, log_to_file: bool = True):
        self.logger = logging.getLogger("HotelRevenueOptimization")
        self.start_times: Dict[str, float] = {}
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.log_to_file = log_to_file
        
        # Create output directory if it doesn't exist
        if self.log_to_file:
            os.makedirs("output/logs", exist_ok=True)
            
            # Create a log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = f"output/logs/performance_{timestamp}.json"
            
            # Initialize the log file with an empty array
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def start_operation(self, operation_id: str, agent_name: str, model_name: str, operation_type: str, details: Optional[Dict[str, Any]] = None):
        """
        Start timing an operation (API call, task execution, etc.)
        
        Args:
            operation_id: Unique identifier for the operation
            agent_name: Name of the agent performing the operation
            model_name: Name of the model being used
            operation_type: Type of operation (e.g., "API_CALL", "TASK_EXECUTION")
            details: Additional details about the operation
        """
        self.start_times[operation_id] = time.time()
        
        # Log the start of the operation
        log_message = f"STARTED: {operation_type} by {agent_name} using {model_name}"
        self.logger.info(log_message)
        
        # Store initial metrics
        self.metrics[operation_id] = {
            "agent": agent_name,
            "model": model_name,
            "operation_type": operation_type,
            "start_time": datetime.now().isoformat(),
            "status": "started",
            "details": details or {}
        }
    
    def end_operation(self, operation_id: str, status: str = "completed", result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """
        End timing an operation and log the results
        
        Args:
            operation_id: Unique identifier for the operation
            status: Status of the operation (completed, failed, etc.)
            result: Result of the operation
            error: Error message if the operation failed
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
        
        # Update metrics
        metrics.update({
            "end_time": datetime.now().isoformat(),
            "duration_seconds": duration,
            "status": status
        })
        
        if result:
            metrics["result"] = result
        
        if error:
            metrics["error"] = error
        
        # Log the completion of the operation
        log_message = f"COMPLETED: {operation_type} by {agent_name} using {model_name} in {duration:.2f}s - Status: {status}"
        
        if status == "completed":
            self.logger.info(log_message)
        else:
            self.logger.error(f"{log_message} - Error: {error}")
        
        # Write to log file if enabled
        if self.log_to_file:
            self._append_to_log_file(metrics)
    
    def log_event(self, event_type: str, agent_name: str, model_name: str, details: Dict[str, Any]):
        """
        Log a general event
        
        Args:
            event_type: Type of event
            agent_name: Name of the agent
            model_name: Name of the model
            details: Event details
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "agent": agent_name,
            "model": model_name,
            "details": details
        }
        
        # Log the event
        self.logger.info(f"EVENT: {event_type} - Agent: {agent_name}, Model: {model_name}")
        
        # Write to log file if enabled
        if self.log_to_file:
            self._append_to_log_file(log_entry)
    
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
performance_logger = PerformanceLogger()
