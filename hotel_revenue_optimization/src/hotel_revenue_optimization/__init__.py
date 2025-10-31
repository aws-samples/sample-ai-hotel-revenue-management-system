# Hotel Revenue Optimization System
# A multi-agent AI solution for hotel revenue management using CrewAI and Amazon Bedrock AgentCore

from .crew import HotelRevenueOptimizationCrew
from .utils.observability import observability
from .utils.nlp_processor import NLPProcessor

__all__ = ['HotelRevenueOptimizationCrew', 'observability', 'NLPProcessor']
