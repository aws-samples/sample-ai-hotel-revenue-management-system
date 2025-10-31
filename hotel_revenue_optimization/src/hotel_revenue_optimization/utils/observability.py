"""
Enhanced observability configuration for Hotel Revenue Optimization System.
This module provides logging and Prometheus metrics for AMP integration.
"""

import os
import logging
import json
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional

# Import Prometheus metrics
try:
    from .prometheus_metrics import metrics
    PROMETHEUS_ENABLED = True
except ImportError:
    PROMETHEUS_ENABLED = False
    print("Prometheus metrics not available - install prometheus-client")

# Configure basic logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create a logger
logger = logging.getLogger("HotelRevenueOptimization")

class ObservabilityTracker:
    """
    Enhanced observability with Prometheus metrics for AMP integration.
    """
    
    def __init__(self):
        self.logger = logger
        self.task_results = {}
        self.failed_tasks = {}
        self.model_calls = {}  # Track model call times
        self.start_time = time.time()

        # Initialize session tracking
        if PROMETHEUS_ENABLED:
            metrics.increment_active_sessions()
            self._start_memory_monitoring()

    def _start_memory_monitoring(self):
        """Start periodic memory monitoring for Prometheus metrics"""
        def monitor_memory():
            while True:
                try:
                    process = psutil.Process()
                    memory_bytes = process.memory_info().rss
                    metrics.update_memory_usage(memory_bytes)
                    # Intentional: Periodic monitoring interval for Prometheus metrics (30s)
                    time.sleep(30)  # nosemgrep: arbitrary-sleep
                except Exception as e:
                    self.logger.error(f"Memory monitoring error: {e}")
                    # Intentional: Error retry backoff to prevent tight error loops (60s)
                    time.sleep(60)  # nosemgrep: arbitrary-sleep

        import threading
        memory_thread = threading.Thread(target=monitor_memory, daemon=True)
        memory_thread.start()
        
    def log_event(self, event_type: str, agent_name: str, model_name: str, details: Dict[str, Any] = None, **kwargs):
        """Log an event with structured data and Prometheus metrics"""
        if details is None:
            details = {}
            
        # Track model call latencies
        if model_name != "none":
            if model_name not in self.model_calls:
                self.model_calls[model_name] = []
            
            # Record model call timing if available
            if "latency" in details:
                self.model_calls[model_name].append(details["latency"])
            elif "duration_seconds" in details:
                self.model_calls[model_name].append(details["duration_seconds"])
            
        # Track task completion and failures
        if "task_name" in kwargs:
            task_name = kwargs["task_name"]
            
            # Track task start
            if event_type == "TASK_INIT":
                self.task_results[task_name] = {
                    "agent": agent_name,
                    "model": model_name,
                    "start_time": time.time(),
                    "status": "running"
                }
            
            # Track task completion
            elif event_type in ["TASK_COMPLETE", "OPTIMIZED_CREW_COMPLETE"]:
                if task_name in self.task_results:
                    end_time = time.time()
                    start_time = self.task_results[task_name]["start_time"]
                    duration = end_time - start_time
                    
                    self.task_results[task_name].update({
                        "status": "completed",
                        "end_time": end_time,
                        "duration_seconds": duration,
                        "result": details.get("result", {})
                    })
            
            # Track task failures
            elif event_type in ["TASK_FAILED", "TASK_ERROR"]:
                self.failed_tasks[task_name] = {
                    "agent": agent_name,
                    "model": model_name,
                    "error": details.get("error", "Unknown error"),
                    "timestamp": time.time()
                }
        
        # For ping logs, use DEBUG level
        if event_type.lower() == "ping" or "health" in event_type.lower():
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
            
        # Create a readable message
        message = f"{event_type} | Agent: {agent_name} | Model: {model_name}"
        
        # Add important details to the message
        if "task_name" in kwargs:
            message += f" | Task: {kwargs['task_name']}"
        if "crew_name" in kwargs:
            message += f" | Crew: {kwargs['crew_name']}"
        
        # Add any important details from the details dict
        important_keys = ["run_id", "status", "duration_seconds"]
        for key in important_keys:
            if key in details:
                message += f" | {key}: {details[key]}"
        
        # Log at the appropriate level
        self.logger.log(log_level, message)
        
        # Record Prometheus metrics
        if PROMETHEUS_ENABLED:
            # Record model calls
            if model_name != "none":
                metrics.record_model_call(model_name, agent_name)
            
            # Record task completion
            if "task_name" in kwargs and "status" in details:
                metrics.record_task(kwargs["task_name"], details["status"])
            
            # Record request completion for run events
            if event_type in ["OPTIMIZED_RUN_COMPLETE", "RUN_COMPLETE"]:
                status = details.get("status", "success")
                duration = details.get("duration_seconds", 0)
                metrics.record_request(agent_name, status, duration)
    
    def log_exception(self, exception: Exception, agent_name: str, model_name: str, details: Dict[str, Any], **kwargs):
        """Log an exception with structured data and Prometheus metrics"""
        # Create a readable message
        message = f"EXCEPTION: {exception.__class__.__name__} - {str(exception)} | Agent: {agent_name} | Model: {model_name}"
        
        # Add important details to the message
        if "task_name" in kwargs:
            message += f" | Task: {kwargs['task_name']}"
        if "crew_name" in kwargs:
            message += f" | Crew: {kwargs['crew_name']}"
        
        # Add stack trace if available
        if "stack_trace" in details:
            message += f"\nStack trace: {details['stack_trace']}"
        
        # Log at ERROR level
        self.logger.error(message)
        
        # Record Prometheus metrics for errors
        if PROMETHEUS_ENABLED:
            if "task_name" in kwargs:
                metrics.record_task(kwargs["task_name"], "error")
            metrics.record_request(agent_name, "error", 0)
    
    def get_task_results(self):
        """Get the task results"""
        return self.task_results
    
    def get_failed_tasks(self):
        """Get the failed tasks"""
        return self.failed_tasks
    
    def prepare_response_with_partial_results(self):
        """Prepare a response with partial results"""
        return {
            "status": "partial_success",
            "completed_tasks": list(self.task_results.keys()),
            "failed_tasks": list(self.failed_tasks.keys()),
            "results": {
                task_name: {"output": task_result.get("result", {}).get("output", "")}
                for task_name, task_result in self.task_results.items()
            }
        }
    def get_task_durations(self) -> Dict[str, float]:
        """Get task durations for completed tasks. Only returns real measured durations."""
        durations = {}
        for task_name, task_data in self.task_results.items():
            if (task_data.get("status") == "completed" and 
                "duration_seconds" in task_data and 
                "start_time" in task_data and 
                "end_time" in task_data):
                # Only include if we have real start/end times (not approximated)
                durations[task_name] = task_data["duration_seconds"]
        return durations
    
    def get_model_latencies(self) -> Dict[str, float]:
        """Get average latencies for each model."""
        latencies = {}
        for model_name, call_times in self.model_calls.items():
            if call_times:
                latencies[model_name] = sum(call_times) / len(call_times)
        return latencies
    
    def get_task_results(self) -> Dict[str, Any]:
        """Get all completed task results."""
        return self.task_results
    
    def get_failed_tasks(self) -> Dict[str, Any]:
        """Get all failed tasks."""
        return self.failed_tasks
    
    def prepare_response_with_partial_results(self) -> Dict[str, Any]:
        """Prepare response when some tasks failed."""
        return {
            "status": "partial_success",
            "completed_tasks": list(self.task_results.keys()),
            "failed_tasks": list(self.failed_tasks.keys())
        }
    
    def __del__(self):
        """Cleanup when tracker is destroyed"""
        if PROMETHEUS_ENABLED:
            metrics.decrement_active_sessions()

# Create a singleton instance
observability = ObservabilityTracker()
