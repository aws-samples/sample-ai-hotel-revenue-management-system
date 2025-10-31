"""
Prometheus metrics exporter for AgentCore Hotel Revenue Optimization.
"""

import os
import time
import threading
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry, REGISTRY
import boto3
import requests
from datetime import datetime

class PrometheusMetrics:
    """Prometheus metrics collector for AgentCore"""
    
    def __init__(self):
        # Create custom registry to avoid conflicts
        self.registry = CollectorRegistry()
        
        # Define metrics
        self.request_counter = Counter(
            'agentcore_requests_total',
            'Total number of AgentCore requests',
            ['agent_name', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'agentcore_request_duration_seconds',
            'Request duration in seconds',
            ['agent_name'],
            registry=self.registry
        )
        
        self.active_sessions = Gauge(
            'agentcore_active_sessions',
            'Number of active sessions',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'agentcore_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.task_counter = Counter(
            'agentcore_tasks_total',
            'Total number of tasks executed',
            ['task_name', 'status'],
            registry=self.registry
        )
        
        self.model_calls = Counter(
            'agentcore_model_calls_total',
            'Total number of model calls',
            ['model_name', 'agent_name'],
            registry=self.registry
        )
        
        # AMP configuration
        self.amp_workspace_id = os.environ.get('AMP_WORKSPACE_ID', 'ws-faa7717b-42ab-42f5-bcfa-d0ebd8bdc442')
        self.aws_region = os.environ.get('AWS_REGION', 'us-west-2')
        
        # Start metrics server
        self.metrics_port = int(os.environ.get('METRICS_PORT', '8080'))
        self._start_metrics_server()
        
        # Initialize session tracking
        self.active_sessions.set(0)
        
    def _start_metrics_server(self):
        """Start Prometheus metrics HTTP server"""
        try:
            # Skip starting metrics server in AgentCore environment to avoid port conflicts
            if os.environ.get('DOCKER_CONTAINER') == '1':
                print(f"Skipping Prometheus metrics server in containerized environment")
                return
            start_http_server(self.metrics_port, registry=self.registry)
            print(f"Prometheus metrics server started on port {self.metrics_port}")
        except Exception as e:
            print(f"Failed to start metrics server: {e}")
    
    def record_request(self, agent_name: str, status: str, duration: float):
        """Record a request with status and duration"""
        self.request_counter.labels(agent_name=agent_name, status=status).inc()
        self.request_duration.labels(agent_name=agent_name).observe(duration)
    
    def increment_active_sessions(self):
        """Increment active sessions counter"""
        self.active_sessions.inc()
    
    def decrement_active_sessions(self):
        """Decrement active sessions counter"""
        self.active_sessions.dec()
    
    def update_memory_usage(self, bytes_used: int):
        """Update memory usage gauge"""
        self.memory_usage.set(bytes_used)
    
    def record_task(self, task_name: str, status: str):
        """Record task execution"""
        self.task_counter.labels(task_name=task_name, status=status).inc()
    
    def record_model_call(self, model_name: str, agent_name: str):
        """Record model API call"""
        self.model_calls.labels(model_name=model_name, agent_name=agent_name).inc()
    
    def get_metrics_endpoint(self):
        """Get the metrics endpoint URL"""
        return f"http://localhost:{self.metrics_port}/metrics"

# Global metrics instance
metrics = PrometheusMetrics()
