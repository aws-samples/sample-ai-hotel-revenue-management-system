"""
Hotel Revenue Optimization Crew

This module contains the multi-agent crew for hotel revenue optimization.
The crew consists of four specialized agents:
- Market Analyst: Analyzes market trends and competitor pricing
- Demand Forecaster: Predicts future demand patterns
- Pricing Strategist: Develops optimal pricing strategies  
- Revenue Manager: Creates comprehensive revenue management plans
"""

from crewai import Agent, Crew, Process, Task
from typing import List, Dict, Any
from .utils.model_config import get_model_for_agent
from .utils.nova_llm import create_llm_for_model
import os
import uuid
import time
import yaml
from datetime import datetime

from .utils.observability import observability
from .utils.model_wrapper import BedrockModelWrapper
from .utils.model_config import get_model_for_agent
from .utils.markdown_formatter import formatter

class HotelRevenueOptimizationCrew:
    """Hotel Revenue Optimization Crew for multi-agent revenue analysis"""

    def __init__(self):
        self.agents = []
        self.tasks = []
        self.task_times = {}  # Track task completion times

    class Meta:
        verbose = False      # disable verbose logs for speed
        use_rich = False     # disable Rich graphical logs for speed

    def __init__(self):
        """Initialize the crew with performance tracking"""
        self.run_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.model_wrappers = {}
        self.crew_name = "HotelRevenueOptimizationCrew"
        
        # Load optimized task configurations
        self._load_optimized_configs()
        
        # Log the initialization
        observability.log_event(
            event_type="CREW_INIT",
            agent_name="system",
            model_name="none",
            crew_name=self.crew_name,
            details={
                "run_id": self.run_id,
                "start_time": datetime.now().isoformat(),
                "optimization": "enabled"
            }
        )
    
    def _load_optimized_configs(self):
        """Load optimized configurations"""
        # Load regular agent configs
        agents_config_path = os.path.join(os.path.dirname(__file__), 'config', 'agents.yaml')
        with open(agents_config_path, 'r') as f:
            self.agents_config = yaml.safe_load(f)
        
        # Load optimized task configs
        tasks_config_path = os.path.join(os.path.dirname(__file__), 'config', 'tasks_optimized.yaml')
        if os.path.exists(tasks_config_path):
            with open(tasks_config_path, 'r') as f:
                self.tasks_config = yaml.safe_load(f)
        else:
            # Fallback to regular tasks if optimized not found
            tasks_config_path = os.path.join(os.path.dirname(__file__), 'config', 'tasks.yaml')
            with open(tasks_config_path, 'r') as f:
                self.tasks_config = yaml.safe_load(f)
    
    def _get_model_wrapper(self, agent_name: str) -> BedrockModelWrapper:
        """Get or create a model wrapper for the given agent"""
        if agent_name not in self.model_wrappers:
            model_id = get_model_for_agent(agent_name)
            self.model_wrappers[agent_name] = BedrockModelWrapper(
                model_id=model_id,
                agent_name=agent_name
            )
        return self.model_wrappers[agent_name]
    
    def market_analyst(self) -> Agent:
        # Use dynamic model configuration with Nova support
        model_id = get_model_for_agent("market_analyst")
        
        observability.log_event(
            event_type="AGENT_INIT",
            agent_name="market_analyst",
            model_name=model_id,
            crew_name=self.crew_name,
            details={"role": "Hotel Market Intelligence Analyst", "optimization": "nova_compatible"}
        )
        
        agent_config = dict(self.agents_config['market_analyst'])
        agent_config['llm'] = create_llm_for_model(model_id)
        
        return Agent(
            config=agent_config,
            verbose=False  # Reduce verbosity for speed
        )

    def demand_forecaster(self) -> Agent:
        # Use dynamic model configuration
        model_id = get_model_for_agent("demand_forecaster")
        
        observability.log_event(
            event_type="AGENT_INIT",
            agent_name="demand_forecaster",
            model_name=model_id,
            crew_name=self.crew_name,
            details={"role": "Hotel Demand Forecasting Specialist", "optimization": "fast_model"}
        )
        
        agent_config = dict(self.agents_config['demand_forecaster'])
        agent_config['llm'] = create_llm_for_model(model_id)
        
        return Agent(
            config=agent_config,
            verbose=False
        )

    def pricing_strategist(self) -> Agent:
        # Use dynamic model configuration
        model_id = get_model_for_agent("pricing_strategist")
        
        observability.log_event(
            event_type="AGENT_INIT",
            agent_name="pricing_strategist",
            model_name=model_id,
            crew_name=self.crew_name,
            details={"role": "Hotel Pricing Strategy Expert", "optimization": "fast_model"}
        )
        
        agent_config = dict(self.agents_config['pricing_strategist'])
        agent_config['llm'] = create_llm_for_model(model_id)
        
        return Agent(
            config=agent_config,
            verbose=False
        )

    def revenue_manager(self) -> Agent:
        # Use dynamic model configuration
        model_id = get_model_for_agent("revenue_manager")
        
        observability.log_event(
            event_type="AGENT_INIT",
            agent_name="revenue_manager",
            model_name=model_id,
            crew_name=self.crew_name,
            details={"role": "Hotel Revenue Management Director", "optimization": "fast_model"}
        )
        
        agent_config = dict(self.agents_config['revenue_manager'])
        agent_config['llm'] = create_llm_for_model(model_id)
        
        return Agent(
            config=agent_config,
            verbose=False
        )

    def market_analysis_task(self) -> Task:
        task_id = str(uuid.uuid4())
        
        observability.log_event(
            event_type="TASK_INIT",
            agent_name="market_analyst",
            model_name=get_model_for_agent("market_analyst"),
            task_name="market_analysis_task",
            crew_name=self.crew_name,
            details={
                "task_id": task_id,
                "task_name": "market_analysis_task",
                "dependencies": [],
                "optimization": "parallel_ready"
            }
        )
        
        return Task(
            description=self.tasks_config['market_analysis_task']['description'],
            agent=self.market_analyst(),
            expected_output="Market analysis report with competitor pricing and trends"
        )

    def demand_forecast_task(self) -> Task:
        task_id = str(uuid.uuid4())
        
        observability.log_event(
            event_type="TASK_INIT",
            agent_name="demand_forecaster",
            model_name=get_model_for_agent("demand_forecaster"),
            task_name="demand_forecast_task",
            crew_name=self.crew_name,
            details={
                "task_id": task_id,
                "task_name": "demand_forecast_task",
                "dependencies": [],  # Remove dependency for parallel execution
                "optimization": "parallel_ready"
            }
        )
        
        return Task(
            description=self.tasks_config['demand_forecast_task']['description'],
            agent=self.demand_forecaster(),
            expected_output="Demand forecast with occupancy predictions"
        )

    def pricing_strategy_task(self) -> Task:
        task_id = str(uuid.uuid4())
        
        observability.log_event(
            event_type="TASK_INIT",
            agent_name="pricing_strategist",
            model_name=get_model_for_agent("pricing_strategist"),
            task_name="pricing_strategy_task",
            crew_name=self.crew_name,
            details={
                "task_id": task_id,
                "task_name": "pricing_strategy_task",
                "dependencies": ["market_analysis_task", "demand_forecast_task"],
                "optimization": "depends_on_parallel_tasks"
            }
        )
        
        return Task(
            description=self.tasks_config['pricing_strategy_task']['description'],
            agent=self.pricing_strategist(),
            expected_output="Pricing strategy with rate recommendations"
        )

    def revenue_management_task(self) -> Task:
        task_id = str(uuid.uuid4())
        
        observability.log_event(
            event_type="TASK_INIT",
            agent_name="revenue_manager",
            model_name=get_model_for_agent("revenue_manager"),
            task_name="revenue_management_task",
            crew_name=self.crew_name,
            details={
                "task_id": task_id,
                "task_name": "revenue_management_task",
                "dependencies": ["market_analysis_task", "demand_forecast_task", "pricing_strategy_task"],
                "optimization": "final_aggregation"
            }
        )
        
        return Task(
            description=self.tasks_config['revenue_management_task']['description'],
            agent=self.revenue_manager(),
            expected_output="Complete revenue optimization plan in markdown format",
            output_file='output/revenue_optimization_plan.md'
        )

    def crew(self) -> Crew:
        """Creates the optimized Hotel Revenue Optimization crew"""
        observability.log_event(
            event_type="CREW_START",
            agent_name="system",
            model_name="none",
            crew_name=self.crew_name,
            details={
                "run_id": self.run_id,
                "process": "sequential_optimized",
                "agents": ["market_analyst", "demand_forecaster", "pricing_strategist", "revenue_manager"],
                "optimization": "fast_execution_enabled"
            }
        )
        
        # Create crew with optimized configuration
        agents = [
            self.market_analyst(),
            self.demand_forecaster(), 
            self.pricing_strategist(),
            self.revenue_manager()
        ]
        
        # Create tasks with dependencies
        market_task = self.market_analysis_task()
        demand_task = self.demand_forecast_task()
        pricing_task = self.pricing_strategy_task()
        revenue_task = self.revenue_management_task()
        
        # Set task dependencies for better coordination
        pricing_task.context = [market_task, demand_task]
        revenue_task.context = [market_task, demand_task, pricing_task]
        
        tasks = [market_task, demand_task, pricing_task, revenue_task]
        
        # Get planning model from our model configuration  
        planning_model = get_model_for_agent("pricing_strategist")  # Use tier1 model for planning
        planning_llm = create_llm_for_model(planning_model)
        
        # Log planning configuration
        observability.log_event(
            event_type="PLANNING_INIT",
            agent_name="system",
            model_name=planning_model,
            crew_name=self.crew_name,
            details={
                "planning_enabled": True,
                "planning_model": planning_model,
                "embedder_model": "amazon.titan-embed-text-v1"
            }
        )
        
        crew_instance = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=False,  # Disabled - using custom planning logs instead
            max_iter=1,
            max_execution_time=45,
            memory=False,
            callbacks=[self._task_callback],
            planning=True,
            planning_llm=planning_llm,  # Use our Bedrock model for planning
            embedder={
                "provider": "aws_bedrock",
                "config": {
                    "model": "amazon.titan-embed-text-v1",
                    "region": os.environ.get('AWS_REGION', 'us-east-1')
                }
            }
        )
        
        return crew_instance
    
    def _task_callback(self, task_output):
        """Enhanced callback for task completion tracking with timing"""
        import time
        
        # Handle different callback formats in newer CrewAI versions
        if hasattr(task_output, 'agent'):
            agent_name = task_output.agent
        elif hasattr(task_output, 'task') and hasattr(task_output.task, 'agent'):
            agent_name = task_output.task.agent.role if hasattr(task_output.task.agent, 'role') else str(task_output.task.agent)
        else:
            agent_name = "unknown_agent"
            
        completion_time = time.time()
        
        # Store task completion time
        self.task_times[agent_name] = completion_time
        
        # Get task name
        if hasattr(task_output, 'task') and hasattr(task_output.task, 'description'):
            task_name = task_output.task.description[:50] + "..." if len(task_output.task.description) > 50 else task_output.task.description
        else:
            task_name = f"task_for_{agent_name}"
        
        observability.log_event(
            event_type="TASK_COMPLETE",
            agent_name=agent_name,
            model_name="tracked_via_callback",
            task_name=task_name,
            crew_name=self.crew_name,
            details={
                "output_length": len(str(task_output.raw)) if hasattr(task_output, 'raw') else len(str(task_output)),
                "completion_time": completion_time,
                "status": "completed"
            }
        )
    
    def kickoff(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the crew with enhanced error handling and result processing"""
        import time
        
        try:
            start_time = time.time()
            self.task_times = {}  # Reset task times
            
            crew_instance = self.crew()
            
            # Enhanced kickoff with inputs validation
            if inputs is None:
                inputs = {}
            
            # Add default hotel context if missing
            if 'hotel_name' not in inputs:
                inputs['hotel_name'] = 'Sample Hotel'
            if 'hotel_location' not in inputs:
                inputs['hotel_location'] = 'Sample City'
            
            observability.log_event(
                event_type="CREW_KICKOFF_START",
                agent_name="system",
                model_name="none",
                crew_name=self.crew_name,
                details={
                    "input_keys": list(inputs.keys()),
                    "agent_count": len(crew_instance.agents),
                    "task_count": len(crew_instance.tasks)
                }
            )
            
            # Log planning start
            planning_model = get_model_for_agent("pricing_strategist")
            observability.log_event(
                event_type="PLANNING_START",
                agent_name="system",
                model_name=planning_model,
                crew_name=self.crew_name,
                details={"planning_phase": "task_coordination"}
            )
            
            # Track task execution with timing fallback
            task_start_time = time.time()
            result = crew_instance.kickoff(inputs=inputs)
            task_end_time = time.time()
            
            # If callback didn't populate task_times, create fallback timing
            if not self.task_times:
                # Estimate task durations based on total time and agent count
                total_task_time = task_end_time - task_start_time - 2  # Subtract planning overhead
                avg_task_time = total_task_time / len(crew_instance.agents) if crew_instance.agents else 0
                
                for i, agent in enumerate(crew_instance.agents):
                    agent_name = agent.role if hasattr(agent, 'role') else f"agent_{i}"
                    # Stagger completion times
                    self.task_times[agent_name] = task_start_time + (i + 1) * avg_task_time
            
            # Log planning complete
            observability.log_event(
                event_type="PLANNING_COMPLETE",
                agent_name="system",
                model_name=planning_model,
                crew_name=self.crew_name,
                details={"planning_phase": "coordination_finished"}
            )
            
            end_time = time.time()
            
            # Calculate task durations
            task_durations = {}
            if len(self.task_times) > 1:
                sorted_times = sorted(self.task_times.items(), key=lambda x: x[1])
                for i, (agent, completion_time) in enumerate(sorted_times):
                    if i == 0:
                        task_durations[agent] = completion_time - start_time
                    else:
                        task_durations[agent] = completion_time - sorted_times[i-1][1]
            
            # Enhanced result with metadata
            enhanced_result = {
                "result": result,
                "metadata": {
                    "total_duration_seconds": end_time - start_time,
                    "task_completion_times": self.task_times,
                    "task_durations": task_durations,
                    "agent_count": len(crew_instance.agents),
                    "task_count": len(crew_instance.tasks)
                }
            }
            
            observability.log_event(
                event_type="CREW_KICKOFF_COMPLETE",
                agent_name="system", 
                model_name="none",
                crew_name=self.crew_name,
                details={
                    "result_type": type(result).__name__,
                    "total_duration": end_time - start_time,
                    "task_durations": task_durations,
                    "success": True
                }
            )
            
            return enhanced_result
            
        except Exception as e:
            observability.log_event(
                event_type="CREW_KICKOFF_ERROR",
                agent_name="system",
                model_name="none", 
                crew_name=self.crew_name,
                details={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
    
