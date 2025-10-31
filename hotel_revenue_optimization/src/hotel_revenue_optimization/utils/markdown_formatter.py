"""
Markdown formatting utilities for Hotel Revenue Optimization System
"""

import re
from typing import Dict, Any, List, Optional


class MarkdownFormatter:
    """Utility class for ensuring consistent markdown formatting in agent outputs"""
    
    @staticmethod
    def format_agent_output(content: str, agent_name: str) -> str:
        """
        Ensure agent output is properly formatted in markdown
        
        Args:
            content: The raw content from the agent
            agent_name: Name of the agent for context
            
        Returns:
            Properly formatted markdown content
        """
        if not content or not isinstance(content, str):
            return content
            
        # If content already has proper markdown headers, return as-is
        if MarkdownFormatter._has_markdown_structure(content):
            return MarkdownFormatter._enhance_existing_markdown(content)
        
        # Otherwise, add basic markdown structure
        return MarkdownFormatter._add_markdown_structure(content, agent_name)
    
    @staticmethod
    def _has_markdown_structure(content: str) -> bool:
        """Check if content already has markdown headers"""
        # Look for markdown headers (# ## ###)
        header_pattern = r'^#{1,6}\s+.+$'
        return bool(re.search(header_pattern, content, re.MULTILINE))
    
    @staticmethod
    def _enhance_existing_markdown(content: str) -> str:
        """Enhance existing markdown with better formatting"""
        lines = content.split('\n')
        enhanced_lines = []
        
        for line in lines:
            # Ensure proper spacing around headers
            if re.match(r'^#{1,6}\s+', line):
                if enhanced_lines and enhanced_lines[-1].strip():
                    enhanced_lines.append('')  # Add blank line before header
                enhanced_lines.append(line)
                enhanced_lines.append('')  # Add blank line after header
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    @staticmethod
    def _add_markdown_structure(content: str, agent_name: str) -> str:
        """Add basic markdown structure to unformatted content"""
        # Map agent names to appropriate headers
        header_map = {
            'market_analyst': '# Market Analysis Report',
            'demand_forecaster': '# Demand Forecast Report', 
            'pricing_strategist': '# Pricing Strategy Report',
            'revenue_manager': '# Hotel Revenue Optimization Plan'
        }
        
        header = header_map.get(agent_name, f'# {agent_name.replace("_", " ").title()} Report')
        
        # Split content into paragraphs and add basic structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        formatted_content = [header, '']
        
        for i, paragraph in enumerate(paragraphs):
            # First paragraph becomes executive summary
            if i == 0:
                formatted_content.extend(['## Executive Summary', '', paragraph, ''])
            else:
                # Try to identify if paragraph should be a section header
                if MarkdownFormatter._looks_like_section_title(paragraph):
                    formatted_content.extend([f'## {paragraph}', ''])
                else:
                    # Format as regular content with bullet points if appropriate
                    formatted_paragraph = MarkdownFormatter._format_paragraph(paragraph)
                    formatted_content.extend([formatted_paragraph, ''])
        
        return '\n'.join(formatted_content)
    
    @staticmethod
    def _looks_like_section_title(text: str) -> bool:
        """Determine if text looks like a section title"""
        # Short text, no periods, title case indicators
        return (
            len(text) < 100 and
            not text.endswith('.') and
            not text.endswith(':') and
            len(text.split()) <= 8 and
            any(word[0].isupper() for word in text.split())
        )
    
    @staticmethod
    def _format_paragraph(paragraph: str) -> str:
        """Format a paragraph with appropriate markdown"""
        lines = paragraph.split('\n')
        
        # If it looks like a list, format as markdown list
        if MarkdownFormatter._looks_like_list(lines):
            return MarkdownFormatter._format_as_list(lines)
        
        # If it contains key-value pairs, format as table or definition list
        if MarkdownFormatter._looks_like_key_value(paragraph):
            return MarkdownFormatter._format_key_value(paragraph)
        
        return paragraph
    
    @staticmethod
    def _looks_like_list(lines: List[str]) -> bool:
        """Check if lines look like a list"""
        if len(lines) < 2:
            return False
        
        # Check for numbered lists or bullet points
        list_indicators = [
            r'^\d+\.',  # 1. 2. 3.
            r'^[-*+]\s',  # - * +
            r'^[a-zA-Z]\)',  # a) b) c)
        ]
        
        matching_lines = 0
        for line in lines:
            line = line.strip()
            if any(re.match(pattern, line) for pattern in list_indicators):
                matching_lines += 1
        
        return matching_lines >= len(lines) * 0.6  # 60% of lines match list pattern
    
    @staticmethod
    def _format_as_list(lines: List[str]) -> str:
        """Format lines as a proper markdown list"""
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Convert to markdown bullet point if not already
            if not re.match(r'^[-*+]\s', line):
                # Remove existing numbering or bullets
                line = re.sub(r'^\d+\.\s*', '', line)
                line = re.sub(r'^[a-zA-Z]\)\s*', '', line)
                line = f'- {line}'
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    @staticmethod
    def _looks_like_key_value(text: str) -> bool:
        """Check if text contains key-value pairs"""
        # Look for patterns like "Key: Value" or "Key - Value"
        kv_pattern = r'^[^:]+:\s*.+$'
        lines = text.split('\n')
        
        matching_lines = sum(1 for line in lines if re.match(kv_pattern, line.strip()))
        return matching_lines >= len(lines) * 0.5
    
    @staticmethod
    def _format_key_value(text: str) -> str:
        """Format key-value pairs as a markdown table or definition list"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Try to format as table
        table_rows = []
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                table_rows.append(f'| {key.strip()} | {value.strip()} |')
        
        if table_rows:
            table = ['| Metric | Value |', '|--------|-------|'] + table_rows
            return '\n'.join(table)
        
        return text
    
    @staticmethod
    def create_executive_summary_template(hotel_name: str, key_metrics: Dict[str, Any]) -> str:
        """Create a standardized executive summary template"""
        template = f"""# Hotel Revenue Optimization Plan

## Executive Summary

**Hotel**: {hotel_name}
**Analysis Date**: {datetime.now().strftime('%B %d, %Y')}

### Current Performance
| Metric | Current | Target | Opportunity |
|--------|---------|--------|-------------|"""
        
        for metric, data in key_metrics.items():
            if isinstance(data, dict) and 'current' in data and 'target' in data:
                current = data['current']
                target = data['target']
                opportunity = data.get('opportunity', 'TBD')
                template += f"\n| {metric} | {current} | {target} | {opportunity} |"
        
        template += "\n\n### Key Recommendations\n"
        return template
    
    @staticmethod
    def format_final_output(content: str) -> str:
        """Final formatting pass for the complete output"""
        if not content:
            return content
            
        # Ensure proper spacing between sections
        content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 consecutive newlines
        
        # Ensure headers have proper spacing
        content = re.sub(r'(\n)(#{1,6}\s+)', r'\1\n\2', content)
        content = re.sub(r'(#{1,6}\s+.+)(\n)([^#\n])', r'\1\2\n\3', content)
        
        # Clean up any trailing whitespace
        lines = [line.rstrip() for line in content.split('\n')]
        content = '\n'.join(lines)
        
        # Ensure file ends with single newline
        return content.rstrip() + '\n'


# Global formatter instance
formatter = MarkdownFormatter()
