#!/usr/bin/env python
import re
import json
from typing import Dict, Any, Optional, Union

class NLPProcessor:
    """
    Natural Language Processor for extracting structured information from free-form text inputs.
    This allows the Hotel Revenue Optimization agent to support natural language prompts.
    """
    
    def __init__(self):
        # Default values for required fields
        self.defaults = {
            'hotel_name': "Grand Pacific Resort",
            'hotel_location': "Miami, FL",
            'hotel_rating': "4.5",
            'room_types': "Standard, Deluxe, Suite",
            'analysis_period': "Next 90 days",
            'forecast_period': "Next 90 days",
            'historical_occupancy': "72%",
            'current_adr': "$245",
            'current_revpar': "$176",
            'target_revpar': "$195",
            'current_challenges': "Weekday occupancy below target, OTA dependency"
        }
        
        # Patterns for extracting information from natural language
        self.patterns = {
            'hotel_name': [
                r'(?:for|optimize|analyze)\s+(?:revenue\s+for\s+)?(?:the\s+)?([A-Za-z\s]+?)(?:\s+in\s+[A-Za-z\s,]+)',
                r'(?:hotel|property|resort|inn)(?:\s+named|\s+called)?\s+["\']?([^"\'.,;]+)["\']?',
                r'for\s+(?:the\s+)?([^,.]+?)(?:\s+hotel|\s+resort|\s+inn)',
                r'(?:analyze|forecast|optimize)\s+(?:for\s+)?(?:the\s+)?([^,.]+?)(?:\s+in\s+|$|\s+hotel|\s+resort)'
            ],
            'hotel_location': [
                r'(?:in|at|located\s+in)\s+([A-Za-z\s]+,\s*[A-Z]{2})',
                r'(?:in|at|located\s+in)\s+([A-Za-z\s]+)'
            ],
            'hotel_rating': [
                r'(\d+(?:\.\d+)?)\s*(?:star|stars|-star|-stars)',
                r'rating(?:\s+of)?\s+(\d+(?:\.\d+)?)'
            ],
            'room_types': [
                r'room\s+types?(?:\s+include|\s+are|\s*:)?\s+([^.]+)',
                r'(?:with|having|offering)\s+([^,.]+?)\s+rooms?'
            ],
            'analysis_period': [
                r'(?:analysis|analyze)(?:\s+for|\s+over|\s+period)?\s+(?:the\s+)?(?:next|coming)\s+(\d+\s+(?:days|weeks|months|quarters|years))',
                r'(?:for|over|during)(?:\s+the)?\s+(?:next|coming)\s+(\d+\s+(?:days|weeks|months|quarters|years))'
            ],
            'forecast_period': [
                r'(?:forecast|prediction|projections?)(?:\s+for|\s+over|\s+period)?\s+(?:the\s+)?(?:next|coming)\s+(\d+\s+(?:days|weeks|months|quarters|years))',
                r'(?:next|coming)\s+(\d+\s+(?:days|weeks|months|quarters|years))'
            ],
            'historical_occupancy': [
                r'(?:historical\s+)?occupancy(?:\s+(?:is|of|at))?\s+(\d+(?:\.\d+)?%)',
                r'(\d+(?:\.\d+)?%)\s+occupancy',
                r'with\s+(\d+(?:\.\d+)?%)\s+occupancy'
            ],
            'current_adr': [
                r'(?:current\s+)?adr(?:\s+(?:of|at|is))?\s+(\$\d+(?:\.\d+)?)',
                r'average\s+daily\s+rate(?:\s+(?:of|at|is))?\s+(\$\d+(?:\.\d+)?)',
                r'adr\s+(\$\d+(?:\.\d+)?)',
                r'and\s+(\$\d+(?:\.\d+)?)\s+adr',
                r'with.*?(\$\d+(?:\.\d+)?)\s+adr'
            ],
            'current_revpar': [
                r'(?:current\s+)?revpar(?:\s+of|\s+at|\s+is|\s*:)?\s+(\$\d+(?:\.\d+)?)',
                r'revenue\s+per\s+available\s+room(?:\s+of|\s+at|\s+is|\s*:)?\s+(\$\d+(?:\.\d+)?)'
            ],
            'target_revpar': [
                r'target\s+revpar(?:\s+of|\s+at|\s+is|\s*:)?\s+(\$\d+(?:\.\d+)?)',
                r'goal\s+revpar(?:\s+of|\s+at|\s+is|\s*:)?\s+(\$\d+(?:\.\d+)?)'
            ],
            'current_challenges': [
                r'challenges?(?:\s+include|\s+are|\s*:)?\s+([^.]+)',
                r'issues?(?:\s+include|\s+are|\s*:)?\s+([^.]+)',
                r'problems?(?:\s+include|\s+are|\s*:)?\s+([^.]+)'
            ]
        }
        
        # Special case handlers for common request types
        self.special_cases = {
            r'(?:analyze|study)\s+competitor\s+pricing': self._handle_competitor_pricing,
            r'forecast\s+demand': self._handle_demand_forecast,
            r'optimize\s+revenue': self._handle_revenue_optimization,
            r'pricing\s+strategy': self._handle_pricing_strategy,
            r'occupancy\s+(?:forecast|prediction)': self._handle_occupancy_forecast
        }
        
        # Optional instruction patterns
        self.optional_instructions = {
            r'include\s+competitor\s+analysis': 'include_competitor_analysis',
            r'with\s+competitor\s+analysis': 'include_competitor_analysis',
            r'add\s+competitor\s+analysis': 'include_competitor_analysis',
            r'competitor\s+analysis\s+included': 'include_competitor_analysis'
        }
    
    def _detect_optional_instructions(self, text: str) -> Dict[str, bool]:
        """Detect optional instructions in the input text."""
        instructions = {}
        
        for pattern, instruction_key in self.optional_instructions.items():
            if re.search(pattern, text, re.IGNORECASE):
                instructions[instruction_key] = True
        
        return instructions
    
    def _extract_with_patterns(self, text: str, field: str) -> Optional[str]:
        """Extract information using regex patterns for a specific field."""
        for pattern in self.patterns[field]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _handle_competitor_pricing(self, text: str) -> Dict[str, str]:
        """Handle special case for competitor pricing analysis."""
        result = {}
        
        # Extract location
        location_match = re.search(r'in\s+([A-Za-z\s,]+)', text, re.IGNORECASE)
        if location_match:
            result['hotel_location'] = location_match.group(1).strip()
        
        # Extract hotel type/segment
        hotel_type_match = re.search(r'(luxury|budget|business|boutique|resort)\s+hotels?', text, re.IGNORECASE)
        if hotel_type_match:
            hotel_type = hotel_type_match.group(1).strip()
            result['hotel_name'] = f"{hotel_type.capitalize()} Hotel"
            
            # Set appropriate rating based on hotel type
            if hotel_type.lower() == 'luxury':
                result['hotel_rating'] = "5.0"
            elif hotel_type.lower() == 'business':
                result['hotel_rating'] = "4.0"
            elif hotel_type.lower() == 'boutique':
                result['hotel_rating'] = "4.5"
            elif hotel_type.lower() == 'budget':
                result['hotel_rating'] = "3.0"
            
        # Set appropriate challenges
        result['current_challenges'] = "Competitive pricing environment, need competitor pricing analysis"
        
        return result
    
    def _handle_demand_forecast(self, text: str) -> Dict[str, str]:
        """Handle special case for demand forecasting."""
        result = {}
        
        # Extract location
        location_match = re.search(r'(?:in|for)\s+([A-Za-z\s,]+)', text, re.IGNORECASE)
        if location_match:
            result['hotel_location'] = location_match.group(1).strip()
        
        # Extract hotel type/segment
        hotel_type_match = re.search(r'(luxury|budget|business|boutique|resort)\s+hotels?', text, re.IGNORECASE)
        if hotel_type_match:
            hotel_type = hotel_type_match.group(1).strip()
            result['hotel_name'] = f"{hotel_type.capitalize()} Hotel"
        
        # Extract time period
        period_match = re.search(r'(?:for|next|coming)\s+(\d+\s+(?:days|weeks|months|quarters?|years?))', text, re.IGNORECASE)
        if period_match:
            period = period_match.group(1).strip()
            result['analysis_period'] = f"Next {period}"
            result['forecast_period'] = f"Next {period}"
        elif 'quarter' in text.lower():
            result['analysis_period'] = "Next 90 days"
            result['forecast_period'] = "Next 90 days"
        
        # Set appropriate challenges
        result['current_challenges'] = "Need accurate demand forecasting for effective planning"
        
        return result
    
    def _handle_revenue_optimization(self, text: str) -> Dict[str, str]:
        """Handle special case for revenue optimization."""
        result = {}
        
        # Extract location
        location_match = re.search(r'(?:in|for)\s+([A-Za-z\s,]+)', text, re.IGNORECASE)
        if location_match:
            result['hotel_location'] = location_match.group(1).strip()
        
        # Extract hotel type/segment
        hotel_type_match = re.search(r'(luxury|budget|business|boutique|resort)\s+hotels?', text, re.IGNORECASE)
        if hotel_type_match:
            hotel_type = hotel_type_match.group(1).strip()
            result['hotel_name'] = f"{hotel_type.capitalize()} Hotel"
        
        # Set appropriate challenges
        result['current_challenges'] = "Revenue optimization needed, balancing occupancy and ADR"
        
        return result
    
    def _handle_pricing_strategy(self, text: str) -> Dict[str, str]:
        """Handle special case for pricing strategy."""
        result = {}
        
        # Extract location
        location_match = re.search(r'(?:in|for)\s+([A-Za-z\s,]+)', text, re.IGNORECASE)
        if location_match:
            result['hotel_location'] = location_match.group(1).strip()
        
        # Extract hotel type/segment
        hotel_type_match = re.search(r'(luxury|budget|business|boutique|resort)\s+hotels?', text, re.IGNORECASE)
        if hotel_type_match:
            hotel_type = hotel_type_match.group(1).strip()
            result['hotel_name'] = f"{hotel_type.capitalize()} Hotel"
        
        # Set appropriate challenges
        result['current_challenges'] = "Need effective pricing strategy to maximize revenue"
        
        return result
    
    def _handle_occupancy_forecast(self, text: str) -> Dict[str, str]:
        """Handle special case for occupancy forecasting."""
        result = {}
        
        # Extract location
        location_match = re.search(r'(?:in|for)\s+([A-Za-z\s,]+)', text, re.IGNORECASE)
        if location_match:
            result['hotel_location'] = location_match.group(1).strip()
        
        # Extract hotel type/segment
        hotel_type_match = re.search(r'(luxury|budget|business|boutique|resort)\s+hotels?', text, re.IGNORECASE)
        if hotel_type_match:
            hotel_type = hotel_type_match.group(1).strip()
            result['hotel_name'] = f"{hotel_type.capitalize()} Hotel"
        
        # Extract time period
        period_match = re.search(r'(?:for|next|coming)\s+(\d+\s+(?:days|weeks|months|quarters?|years?))', text, re.IGNORECASE)
        if period_match:
            period = period_match.group(1).strip()
            result['analysis_period'] = f"Next {period}"
            result['forecast_period'] = f"Next {period}"
        elif 'quarter' in text.lower():
            result['analysis_period'] = "Next 90 days"
            result['forecast_period'] = "Next 90 days"
        
        # Set appropriate challenges
        result['current_challenges'] = "Need accurate occupancy forecasting for effective planning"
        
        return result
    
    def _handle_special_cases(self, text: str) -> Dict[str, str]:
        """Check if the text matches any special case patterns and handle accordingly."""
        for pattern, handler in self.special_cases.items():
            if re.search(pattern, text, re.IGNORECASE):
                return handler(text)
        return {}
    
    def _extract_city_state(self, location: str) -> str:
        """Format location as City, State if possible."""
        # Check if location already has state code
        if re.search(r'[A-Za-z\s]+,\s*[A-Z]{2}', location):
            return location
        
        # Common city-state mappings
        city_state_map = {
            'new york': 'New York, NY',
            'los angeles': 'Los Angeles, CA',
            'chicago': 'Chicago, IL',
            'houston': 'Houston, TX',
            'phoenix': 'Phoenix, AZ',
            'philadelphia': 'Philadelphia, PA',
            'san antonio': 'San Antonio, TX',
            'san diego': 'San Diego, CA',
            'dallas': 'Dallas, TX',
            'san jose': 'San Jose, CA',
            'austin': 'Austin, TX',
            'jacksonville': 'Jacksonville, FL',
            'fort worth': 'Fort Worth, TX',
            'columbus': 'Columbus, OH',
            'san francisco': 'San Francisco, CA',
            'charlotte': 'Charlotte, NC',
            'indianapolis': 'Indianapolis, IN',
            'seattle': 'Seattle, WA',
            'denver': 'Denver, CO',
            'washington': 'Washington, DC',
            'boston': 'Boston, MA',
            'el paso': 'El Paso, TX',
            'nashville': 'Nashville, TN',
            'detroit': 'Detroit, MI',
            'portland': 'Portland, OR',
            'las vegas': 'Las Vegas, NV',
            'memphis': 'Memphis, TN',
            'louisville': 'Louisville, KY',
            'baltimore': 'Baltimore, MD',
            'milwaukee': 'Milwaukee, WI',
            'albuquerque': 'Albuquerque, NM',
            'tucson': 'Tucson, AZ',
            'fresno': 'Fresno, CA',
            'sacramento': 'Sacramento, CA',
            'kansas city': 'Kansas City, MO',
            'miami': 'Miami, FL',
            'orlando': 'Orlando, FL',
            'atlanta': 'Atlanta, GA'
        }
        
        # Try to match the location to a known city
        location_lower = location.lower()
        for city, city_state in city_state_map.items():
            if city in location_lower:
                return city_state
        
        # If no match, return the original location
        return location
    
    def _normalize_period(self, period: str) -> str:
        """Normalize time period expressions."""
        if not period:
            return "Next 90 days"
            
        period_lower = period.lower()
        
        # Handle quarter references
        if 'quarter' in period_lower:
            return "Next 90 days"
        
        # Handle month references
        if 'month' in period_lower:
            # Extract number if present
            num_match = re.search(r'(\d+)', period_lower)
            if num_match:
                num = int(num_match.group(1))
                return f"Next {num * 30} days"
            return "Next 30 days"
        
        # Handle week references
        if 'week' in period_lower:
            # Extract number if present
            num_match = re.search(r'(\d+)', period_lower)
            if num_match:
                num = int(num_match.group(1))
                return f"Next {num * 7} days"
            return "Next 7 days"
        
        # Handle year references
        if 'year' in period_lower:
            return "Next 365 days"
        
        return period
    
    def _normalize_percentage(self, percentage: str) -> str:
        """Ensure percentage has % symbol."""
        if not percentage:
            return None
            
        if '%' not in percentage:
            return f"{percentage}%"
        return percentage
    
    def _normalize_currency(self, amount: str) -> str:
        """Ensure currency has $ symbol."""
        if not amount:
            return None
            
        if '$' not in amount:
            return f"${amount}"
        return amount
    
    def _normalize_hotel_name(self, name: str) -> str:
        """Normalize hotel name."""
        if not name:
            return None
            
        # If name doesn't contain "Hotel", "Resort", "Inn", etc., add "Hotel"
        hotel_keywords = ['hotel', 'resort', 'inn', 'suites', 'plaza']
        if not any(keyword in name.lower() for keyword in hotel_keywords):
            return f"{name} Hotel"
        return name
    
    def process_input(self, input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process the input data, which can be either a JSON object or a natural language string.
        Returns a structured dictionary with all required fields.
        """
        # Initialize with default values
        result = self.defaults.copy()
        
        # Check if input is already a dictionary (JSON object)
        if isinstance(input_data, dict):
            # Update result with provided values
            for key, value in input_data.items():
                if key in result:
                    result[key] = value
            return result
        
        # If input is a string, check if it's a JSON string
        if isinstance(input_data, str):
            # Check if it's a JSON string
            try:
                json_data = json.loads(input_data)
                if isinstance(json_data, dict):
                    # Update result with provided values
                    for key, value in json_data.items():
                        if key in result:
                            result[key] = value
                    return result
            except (json.JSONDecodeError, ValueError):
                # Not a valid JSON string, treat as natural language
                pass
            
            # Check for "prompt" field in case of {"prompt": "..."} format
            try:
                json_data = json.loads(input_data)
                if isinstance(json_data, dict) and "prompt" in json_data:
                    input_text = json_data["prompt"]
                else:
                    input_text = input_data
            except (json.JSONDecodeError, ValueError):
                input_text = input_data
            
            # Process as natural language
            # Detect optional instructions first
            optional_instructions = self._detect_optional_instructions(input_text)
            
            # First check for special cases
            special_case_result = self._handle_special_cases(input_text)
            if special_case_result:
                for key, value in special_case_result.items():
                    result[key] = value
            
            # Then extract specific fields using patterns
            for field in self.patterns.keys():
                extracted_value = self._extract_with_patterns(input_text, field)
                if extracted_value:
                    result[field] = extracted_value
            
            # Add optional instructions to result
            for instruction_key, value in optional_instructions.items():
                result[instruction_key] = str(value).lower()
            
            # Normalize extracted values
            if 'hotel_location' in result:
                result['hotel_location'] = self._extract_city_state(result['hotel_location'])
            
            if 'hotel_name' in result:
                result['hotel_name'] = self._normalize_hotel_name(result['hotel_name'])
            
            if 'analysis_period' in result:
                result['analysis_period'] = self._normalize_period(result['analysis_period'])
            
            if 'forecast_period' in result:
                result['forecast_period'] = self._normalize_period(result['forecast_period'])
            
            if 'historical_occupancy' in result:
                result['historical_occupancy'] = self._normalize_percentage(result['historical_occupancy'])
            
            if 'current_adr' in result:
                result['current_adr'] = self._normalize_currency(result['current_adr'])
            
            if 'current_revpar' in result:
                result['current_revpar'] = self._normalize_currency(result['current_revpar'])
            
            if 'target_revpar' in result:
                result['target_revpar'] = self._normalize_currency(result['target_revpar'])
            
            return result
        
        # If input is neither a dictionary nor a string, return defaults
        return result
