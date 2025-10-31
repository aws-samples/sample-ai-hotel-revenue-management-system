"""
Custom CrewAI callback for automatic markdown formatting
"""

from typing import Dict, Any, Optional
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tasks.task import Task

from .markdown_formatter import formatter
from .observability import observability


class MarkdownFormattingCallback:
    """Callback to automatically format agent outputs in markdown"""
    
    def __init__(self):
        self.task_outputs = {}
    
    def on_task_start(self, task: Task, agent: BaseAgent, inputs: Dict[str, Any]) -> None:
        """Called when a task starts"""
        task_name = getattr(task, 'description', 'unknown_task')[:50]
        agent_name = getattr(agent, 'role', 'unknown_agent')
        
        observability.log_event(
            event_type="TASK_START_MARKDOWN",
            agent_name=agent_name,
            model_name="unknown",
            task_name=task_name,
            details={
                "inputs": inputs,
                "markdown_formatting": "enabled"
            }
        )
    
    def on_task_complete(self, task: Task, agent: BaseAgent, output: str) -> str:
        """Called when a task completes - format output in markdown"""
        agent_name = getattr(agent, 'role', 'unknown_agent').lower().replace(' ', '_')
        task_name = getattr(task, 'description', 'unknown_task')[:50]
        
        # Format the output in markdown
        formatted_output = formatter.format_agent_output(output, agent_name)
        
        # Store the formatted output
        self.task_outputs[agent_name] = formatted_output
        
        observability.log_event(
            event_type="TASK_COMPLETE_MARKDOWN",
            agent_name=agent_name,
            model_name="unknown",
            task_name=task_name,
            details={
                "original_length": len(output) if output else 0,
                "formatted_length": len(formatted_output) if formatted_output else 0,
                "markdown_enhanced": True
            }
        )
        
        return formatted_output
    
    def on_task_error(self, task: Task, agent: BaseAgent, error: Exception) -> None:
        """Called when a task encounters an error"""
        agent_name = getattr(agent, 'role', 'unknown_agent')
        task_name = getattr(task, 'description', 'unknown_task')[:50]
        
        observability.log_exception(
            exception=error,
            agent_name=agent_name,
            model_name="unknown",
            details={
                "task_name": task_name,
                "markdown_formatting": "failed"
            }
        )
    
    def get_formatted_outputs(self) -> Dict[str, str]:
        """Get all formatted outputs from tasks"""
        return self.task_outputs.copy()


# Global callback instance
markdown_callback = MarkdownFormattingCallback()
