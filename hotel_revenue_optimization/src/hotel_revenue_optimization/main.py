#!/usr/bin/env python
# src/hotel_revenue_optimization/main.py 
import sys
import warnings
import os
import json
import time
import uuid
from datetime import datetime, timedelta
import traceback
from typing import Dict, Any, Union

# Import crew for hotel revenue optimization
from src.hotel_revenue_optimization import HotelRevenueOptimizationCrew, observability, NLPProcessor

from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

@app.entrypoint
def run(payload=None):
    """
    Main entrypoint for the Hotel Revenue Optimization System.
    
    Processes hotel data through a multi-agent crew to generate comprehensive
    revenue optimization recommendations including market analysis, demand forecasting,
    pricing strategies, and revenue management plans.
    
    Args:
        payload: Input data containing hotel information. Supports multiple formats:
                - Structured JSON with hotel details
                - Natural language prompts ({"prompt": "..."})
                - Message format ({"message": "..."})
    
    Returns:
        Dict: Revenue optimization report with analysis and recommendations
    """
    run_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log the start of the run with optimization flag
    observability.log_event(
        event_type="OPTIMIZED_RUN_START",
        agent_name="system",
        model_name="none",
        details={
            "run_id": run_id,
            "start_time": datetime.now().isoformat(),
            "payload": payload,
            "optimization": "enabled",
            "target_duration": "under_60_seconds"
        }
    )
    
    try:
        # Initialize NLP processor
        nlp_processor = NLPProcessor()
        
        # Process input - handle both structured JSON and natural language
        if payload:
            # Check if payload is wrapped in UI format (prompt or message)
            if isinstance(payload, dict) and len(payload) == 1:
                # Handle different UI formats
                message_content = None
                if "prompt" in payload:
                    message_content = payload["prompt"]
                elif "message" in payload:
                    message_content = payload["message"]
                
                if message_content:
                    # Extract the message content for natural language processing
                    inputs = nlp_processor.process_input(message_content)
                    
                    # Log that NLP processing was used
                    observability.log_event(
                        event_type="NLP_PROCESSING",
                        agent_name="system",
                        model_name="none",
                        details={
                            "original_input": message_content,
                            "processed_input": inputs,
                            "input_format": "prompt" if "prompt" in payload else "message"
                        }
                    )
                    
                    # Check if we have enough information to proceed
                    missing_fields = []
                    for field in nlp_processor.defaults.keys():
                        if inputs[field] == nlp_processor.defaults[field]:
                            missing_fields.append(field)
                    
                    # Check if the query is relevant to hotel revenue optimization
                    hotel_keywords = ['hotel', 'resort', 'inn', 'lodge', 'motel', 'property', 'accommodation', 
                                    'revenue', 'pricing', 'occupancy', 'adr', 'revpar', 'room', 'guest',
                                    'mountain', 'ski', 'chalet', 'suite', 'deluxe', 'luxury', 'standard',
                                    'festival', 'event', 'conference', 'convention', 'season', 'hiking']
                    
                    irrelevant_keywords = ['politics', 'political', 'election', 'president', 'government', 
                                         'news', 'weather', 'celebrity', 'movie', 
                                         'food', 'recipe', 'health', 'medical', 'stock', 'investment']
                    
                    # Remove booking keywords from irrelevant list - they can be part of hotel context
                    booking_keywords = ['book', 'booking', 'reserve', 'reservation']
                    
                    message_lower = message_content.lower()
                    has_hotel_keywords = any(keyword in message_lower for keyword in hotel_keywords)
                    has_irrelevant_keywords = any(keyword in message_lower for keyword in irrelevant_keywords)
                    
                    # Special check for booking-related queries (only if no hotel context)
                    is_booking_query = any(word in message_lower for word in booking_keywords) and not has_hotel_keywords
                    
                    # If query seems irrelevant to revenue optimization (but allow hotel-related booking queries)
                    if has_irrelevant_keywords or is_booking_query:
                        error_response = {
                            "status": "error",
                            "error_type": "irrelevant_query",
                            "message": "I'm a specialized Hotel Revenue Optimization assistant. I can only help with hotel revenue management, pricing strategies, and demand forecasting.",
                            "guidance": "Please ask me about hotel revenue optimization topics such as:",
                            "capabilities": [
                                "Revenue optimization strategies",
                                "Pricing and rate management", 
                                "Demand forecasting",
                                "Market analysis and competitor pricing",
                                "Occupancy and ADR improvement",
                                "RevPAR optimization"
                            ],
                            "example": "Try asking: 'Optimize revenue for [Hotel Name] in [City] with [occupancy]% occupancy and $[amount] ADR'"
                        }
                        return error_response
                    
                    # If query is hotel-related but missing information
                    if len(missing_fields) > 8:  # Adjusted threshold - more lenient for natural language
                        # Determine what type of hotel information is missing
                        critical_missing = []
                        if inputs['hotel_name'] == nlp_processor.defaults['hotel_name']:
                            critical_missing.append("hotel name")
                        if inputs['hotel_location'] == nlp_processor.defaults['hotel_location']:
                            critical_missing.append("location")
                        if inputs['current_adr'] == nlp_processor.defaults['current_adr'] and inputs['current_revpar'] == nlp_processor.defaults['current_revpar']:
                            critical_missing.append("current financial metrics (ADR or RevPAR)")
                        
                        error_response = {
                            "status": "error",
                            "error_type": "insufficient_information",
                            "message": "I need more specific information about your hotel to provide revenue optimization guidance.",
                            "missing_critical_info": critical_missing,
                            "guidance": "To help you optimize hotel revenue, please provide:",
                            "required_info": [
                                "Hotel name and location",
                                "Current performance metrics (occupancy %, ADR, RevPAR)",
                                "Property details (star rating, room types)",
                                "Specific challenges or goals"
                            ],
                            "examples": [
                                "Optimize revenue for Seaside Resort in Miami, FL with 75% occupancy and $250 ADR",
                                "Improve RevPAR for Downtown Business Hotel in Chicago with current RevPAR $180, targeting $200",
                                "Analyze pricing strategy for 4-star boutique hotel in San Francisco with luxury suites and standard rooms"
                            ]
                        }
                        return error_response
                    
                else:
                    # If it's a single-key dict but not prompt/message, treat as structured JSON
                    inputs = {
                        'hotel_name': payload.get("hotel_name", "Grand Pacific Resort"),
                        'hotel_location': payload.get("hotel_location", "Miami, FL"),
                        'hotel_rating': payload.get("hotel_rating", "4.5"),
                        'room_types': payload.get("room_types", "Standard, Deluxe, Suite"),
                        'analysis_period': payload.get("analysis_period", "Next 90 days"),
                        'forecast_period': payload.get("forecast_period", "Next 90 days"),
                        'historical_occupancy': payload.get("historical_occupancy", "72%"),
                        'current_adr': payload.get("current_adr", "$245"),
                        'current_revpar': payload.get("current_revpar", "$176"),
                        'target_revpar': payload.get("target_revpar", "$195"),
                        'current_challenges': payload.get("current_challenges", "Weekday occupancy below target, OTA dependency")
                    }
            # Check if payload is a string (natural language) or dict (structured JSON)
            elif isinstance(payload, str):
                # Process natural language input
                inputs = nlp_processor.process_input(payload)
                
                # Log that NLP processing was used
                observability.log_event(
                    event_type="NLP_PROCESSING",
                    agent_name="system",
                    model_name="none",
                    details={
                        "original_input": payload,
                        "processed_input": inputs,
                        "input_format": "string"
                    }
                )
                
                # Check if we have enough information to proceed
                missing_fields = []
                for field in nlp_processor.defaults.keys():
                    if inputs[field] == nlp_processor.defaults[field]:
                        missing_fields.append(field)
                
                # Check if the query is relevant to hotel revenue optimization
                hotel_keywords = ['hotel', 'resort', 'inn', 'lodge', 'motel', 'property', 'accommodation', 
                                'revenue', 'pricing', 'occupancy', 'adr', 'revpar', 'room', 'guest',
                                'mountain', 'ski', 'chalet', 'suite', 'deluxe', 'luxury', 'standard',
                                'festival', 'event', 'conference', 'convention', 'season', 'hiking']
                
                irrelevant_keywords = ['politics', 'political', 'election', 'president', 'government', 
                                     'news', 'weather', 'celebrity', 'movie', 
                                     'food', 'recipe', 'health', 'medical', 'stock', 'investment']
                
                # Remove booking keywords from irrelevant list - they can be part of hotel context
                booking_keywords = ['book', 'booking', 'reserve', 'reservation']
                
                payload_lower = payload.lower()
                has_hotel_keywords = any(keyword in payload_lower for keyword in hotel_keywords)
                has_irrelevant_keywords = any(keyword in payload_lower for keyword in irrelevant_keywords)
                
                # Special check for booking-related queries (only if no hotel context)
                is_booking_query = any(word in payload_lower for word in booking_keywords) and not has_hotel_keywords
                
                # If query seems irrelevant to revenue optimization (but allow hotel-related booking queries)
                if has_irrelevant_keywords or is_booking_query:
                    error_response = {
                        "status": "error",
                        "error_type": "irrelevant_query",
                        "message": "I'm a specialized Hotel Revenue Optimization assistant. I can only help with hotel revenue management, pricing strategies, and demand forecasting.",
                        "guidance": "Please ask me about hotel revenue optimization topics such as:",
                        "capabilities": [
                            "Revenue optimization strategies",
                            "Pricing and rate management", 
                            "Demand forecasting",
                            "Market analysis and competitor pricing",
                            "Occupancy and ADR improvement",
                            "RevPAR optimization"
                        ],
                        "example": "Try asking: 'Optimize revenue for [Hotel Name] in [City] with [occupancy]% occupancy and $[amount] ADR'"
                    }
                    return error_response
                
                # If query is hotel-related but missing information
                if len(missing_fields) > 8:  # Adjusted threshold - more lenient for natural language
                    # Determine what type of hotel information is missing
                    critical_missing = []
                    if inputs['hotel_name'] == nlp_processor.defaults['hotel_name']:
                        critical_missing.append("hotel name")
                    if inputs['hotel_location'] == nlp_processor.defaults['hotel_location']:
                        critical_missing.append("location")
                    if inputs['current_adr'] == nlp_processor.defaults['current_adr'] and inputs['current_revpar'] == nlp_processor.defaults['current_revpar']:
                        critical_missing.append("current financial metrics (ADR or RevPAR)")
                    
                    error_response = {
                        "status": "error",
                        "error_type": "insufficient_information",
                        "message": "I need more specific information about your hotel to provide revenue optimization guidance.",
                        "missing_critical_info": critical_missing,
                        "guidance": "To help you optimize hotel revenue, please provide:",
                        "required_info": [
                            "Hotel name and location",
                            "Current performance metrics (occupancy %, ADR, RevPAR)",
                            "Property details (star rating, room types)",
                            "Specific challenges or goals"
                        ],
                        "examples": [
                            "Optimize revenue for Seaside Resort in Miami, FL with 75% occupancy and $250 ADR",
                            "Improve RevPAR for Downtown Business Hotel in Chicago with current RevPAR $180, targeting $200",
                            "Analyze pricing strategy for 4-star boutique hotel in San Francisco with luxury suites and standard rooms"
                        ]
                    }
                    return error_response
            else:
                # Use structured JSON input
                inputs = {
                    'hotel_name': payload.get("hotel_name", "Grand Pacific Resort"),
                    'hotel_location': payload.get("hotel_location", "Miami, FL"),
                    'hotel_rating': payload.get("hotel_rating", "4.5"),
                    'room_types': payload.get("room_types", "Standard, Deluxe, Suite"),
                    'analysis_period': payload.get("analysis_period", "Next 90 days"),
                    'forecast_period': payload.get("forecast_period", "Next 90 days"),
                    'historical_occupancy': payload.get("historical_occupancy", "72%"),
                    'current_adr': payload.get("current_adr", "$245"),
                    'current_revpar': payload.get("current_revpar", "$176"),
                    'target_revpar': payload.get("target_revpar", "$195"),
                    'current_challenges': payload.get("current_challenges", "Weekday occupancy below target, OTA dependency")
                }
        else:
            # Use default values
            inputs = nlp_processor.defaults.copy()
        
        # Log the inputs
        observability.log_event(
            event_type="INPUTS_PROCESSED",
            agent_name="system",
            model_name="none",
            details=inputs
        )
        
        # Add dynamic current date to inputs
        inputs['current_date'] = datetime.now().strftime("%B %d, %Y")
        
        # Calculate next Monday for implementation start date
        today = datetime.now()
        days_ahead = 0 - today.weekday()  # Monday is 0
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        inputs['implementation_start_date'] = next_monday.strftime("%B %d, %Y")
        
        # Create the crew for hotel revenue optimization
        crew = HotelRevenueOptimizationCrew()
        
        # Run the crew
        try:
            crew_result = crew.kickoff(inputs=inputs)
            
            # Extract result and metadata from enhanced response
            if isinstance(crew_result, dict) and "metadata" in crew_result:
                metadata = crew_result["metadata"]
                status = "success"
            else:
                # Fallback for old response format
                metadata = {
                    "total_duration_seconds": 0,
                    "task_completion_times": {},
                    "task_durations": {},
                    "agent_count": 4,
                    "task_count": 4
                }
                status = "success"
                
        except Exception as e:
            # Log the crew error but continue to generate partial results
            observability.log_exception(
                exception=e,
                agent_name="system",
                model_name="none",
                details={
                    "run_id": run_id,
                    "error_location": "crew_execution"
                }
            )
            status = "partial_success"
            metadata = {
                "total_duration_seconds": 0,
                "task_completion_times": {},
                "task_durations": {},
                "agent_count": 0,
                "task_count": 0,
                "error": str(e)
            }
        
        # Try to read the report file
        report_content = None
        report_path = "output/revenue_optimization_plan.md"
        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                report_content = f.read()
        
        # Calculate performance metrics
        duration = time.time() - start_time
        task_results = observability.get_task_results()
        failed_tasks = observability.get_failed_tasks()
        
        # Get performance data - only include if not empty
        task_durations = observability.get_task_durations()
        model_latencies = observability.get_model_latencies()
        
        # Build performance object only with non-empty data
        performance = {}
        if task_durations:
            performance["task_durations"] = task_durations
        if model_latencies:
            performance["model_latencies"] = model_latencies
        
        # Prepare the response
        if status == "success" and not failed_tasks:
            # All tasks completed successfully
            response = {
                "status": "success",
                "completed_tasks": list(task_results.keys()),
                "failed_tasks": [],
                "metadata": {
                    "run_id": run_id,
                    "start_time": datetime.fromtimestamp(start_time).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_seconds": duration,
                    "crew_metadata": metadata,  # Enhanced crew timing data
                }
            }
            
            # Only add performance if it has data
            if performance:
                response["metadata"]["performance"] = performance
            
            # Log individual task results at DEBUG level
            for task_name, task_result in task_results.items():
                output = task_result.get("result", {}).get("output", "")
                if output:
                    logger.debug(f"Task {task_name} output: {output[:200]}...")
            
            if report_content:
                response["report"] = report_content
        else:
            # Some tasks failed, prepare partial results
            response = observability.prepare_response_with_partial_results()
            
            # Add metadata
            response["metadata"] = {
                "run_id": run_id,
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": duration,
            }
            
            # Only add performance if it has data
            if performance:
                response["metadata"]["performance"] = performance
            
            if report_content:
                response["report"] = report_content
        
        # Log the completion
        observability.log_event(
            event_type="RUN_COMPLETE",
            agent_name="system",
            model_name="none",
            details={
                "run_id": run_id,
                "duration_seconds": duration,
                "status": status,
                "completed_tasks": len(task_results),
                "failed_tasks": len(failed_tasks),
                "report_generated": report_content is not None,
                "report_length": len(report_content) if report_content else 0
            }
        )
        
        # Make sure the response is JSON serializable
        def make_serializable(obj):
            """Convert non-serializable objects to serializable format."""
            if hasattr(obj, 'dict') and callable(obj.dict):
                # Handle Pydantic models
                return obj.dict()
            elif hasattr(obj, 'model_dump') and callable(obj.model_dump):
                # Handle Pydantic v2 models
                return obj.model_dump()
            elif hasattr(obj, 'json') and callable(obj.json):
                # Handle objects with json method
                return json.loads(obj.json())
            elif hasattr(obj, '__dict__'):
                # Handle generic objects
                return {k: make_serializable(v) for k, v in obj.__dict__.items() 
                        if not k.startswith('_')}
            elif isinstance(obj, (list, tuple)):
                # Handle lists and tuples
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                # Handle dictionaries
                return {k: make_serializable(v) for k, v in obj.items()}
            else:
                # Convert to string as last resort
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, OverflowError):
                    return str(obj)
        
        # Convert the response to a serializable format
        serializable_response = make_serializable(response)
        
        # Return the serializable response
        return serializable_response
        
    except Exception as e:
        # Log the error with full stack trace
        stack_trace = traceback.format_exc()
        duration = time.time() - start_time
        
        observability.log_exception(
            exception=e,
            agent_name="system",
            model_name="none",
            details={
                "run_id": run_id,
                "duration_seconds": duration,
                "stack_trace": stack_trace
            }
        )
        
        # Prepare error response
        error_response = {
            "status": "failure",
            "completed_tasks": [],
            "failed_tasks": ["system"],
            "results": {},
            "metadata": {
                "run_id": run_id,
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": duration,
                "error": str(e),
                "stack_trace": stack_trace
            }
        }
        
        # Make sure the error response is JSON serializable
        def make_serializable(obj):
            """Convert non-serializable objects to serializable format."""
            if hasattr(obj, 'dict') and callable(obj.dict):
                # Handle Pydantic models
                return obj.dict()
            elif hasattr(obj, 'model_dump') and callable(obj.model_dump):
                # Handle Pydantic v2 models
                return obj.model_dump()
            elif hasattr(obj, 'json') and callable(obj.json):
                # Handle objects with json method
                return json.loads(obj.json())
            elif hasattr(obj, '__dict__'):
                # Handle generic objects
                return {k: make_serializable(v) for k, v in obj.__dict__.items() 
                        if not k.startswith('_')}
            elif isinstance(obj, (list, tuple)):
                # Handle lists and tuples
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                # Handle dictionaries
                return {k: make_serializable(v) for k, v in obj.items()}
            else:
                # Convert to string as last resort
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, OverflowError):
                    return str(obj)
        
        # Convert the error response to a serializable format
        serializable_error_response = make_serializable(error_response)
        
        # Return the serializable error response
        return serializable_error_response

if __name__ == "__main__":
    # Only run the app when executed directly, not when imported by AgentCore
    app.run()
