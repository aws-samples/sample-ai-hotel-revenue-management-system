#!/usr/bin/env python
"""
Script to analyze performance logs from the Hotel Revenue Optimization system.
"""

import os
import json
import argparse
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional

def load_logs(log_file: str) -> List[Dict[str, Any]]:
    """Load logs from a JSON file"""
    with open(log_file, 'r') as f:
        return json.load(f)

def analyze_model_performance(logs: List[Dict[str, Any]]) -> pd.DataFrame:
    """Analyze model performance from logs"""
    model_data = []
    
    for entry in logs:
        if entry.get('operation_type') == 'MODEL_INVOKE' and entry.get('status') == 'completed':
            model_data.append({
                'agent': entry.get('agent', 'unknown'),
                'model': entry.get('model', 'unknown'),
                'duration_seconds': entry.get('duration_seconds', 0),
                'input_tokens': entry.get('result', {}).get('estimated_input_tokens', 0),
                'output_tokens': entry.get('result', {}).get('estimated_output_tokens', 0),
                'timestamp': entry.get('start_time', '')
            })
    
    return pd.DataFrame(model_data)

def analyze_task_performance(logs: List[Dict[str, Any]]) -> pd.DataFrame:
    """Analyze task performance from logs"""
    task_data = []
    
    for entry in logs:
        if entry.get('operation_type') == 'TASK_EXECUTION':
            task_data.append({
                'agent': entry.get('agent', 'unknown'),
                'task': entry.get('details', {}).get('task', {}).get('name', 'unknown'),
                'duration_seconds': entry.get('duration_seconds', 0),
                'status': entry.get('status', 'unknown'),
                'timestamp': entry.get('start_time', '')
            })
    
    return pd.DataFrame(task_data)

def analyze_rate_limits(logs: List[Dict[str, Any]]) -> pd.DataFrame:
    """Analyze rate limit events from logs"""
    rate_limit_data = []
    
    for entry in logs:
        if entry.get('event_type') == 'RATE_LIMIT':
            rate_limit_data.append({
                'agent': entry.get('agent', 'unknown'),
                'model': entry.get('model', 'unknown'),
                'attempt': entry.get('details', {}).get('attempt', 0),
                'delay': entry.get('details', {}).get('delay', 0),
                'error_message': entry.get('details', {}).get('error_message', ''),
                'timestamp': entry.get('timestamp', '')
            })
    
    return pd.DataFrame(rate_limit_data)

def generate_report(log_file: str, output_dir: str = 'output/reports'):
    """Generate a performance report from logs"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load logs
    logs = load_logs(log_file)
    
    # Analyze model performance
    model_df = analyze_model_performance(logs)
    
    # Analyze task performance
    task_df = analyze_task_performance(logs)
    
    # Analyze rate limits
    rate_limit_df = analyze_rate_limits(logs)
    
    # Generate timestamp for report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create report file
    report_file = f"{output_dir}/performance_report_{timestamp}.md"
    
    with open(report_file, 'w') as f:
        f.write("# Hotel Revenue Optimization Performance Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Summary\n\n")
        
        # Overall statistics
        total_duration = sum(entry.get('duration_seconds', 0) for entry in logs if 'duration_seconds' in entry)
        total_model_calls = len(model_df)
        total_rate_limits = len(rate_limit_df)
        
        f.write(f"- Total Duration: {total_duration:.2f} seconds\n")
        f.write(f"- Total Model Calls: {total_model_calls}\n")
        f.write(f"- Total Rate Limit Events: {total_rate_limits}\n\n")
        
        # Model performance
        if not model_df.empty:
            f.write("## Model Performance\n\n")
            
            # Group by model and agent
            model_stats = model_df.groupby(['model', 'agent']).agg({
                'duration_seconds': ['count', 'mean', 'sum'],
                'input_tokens': 'sum',
                'output_tokens': 'sum'
            }).reset_index()
            
            model_stats.columns = ['model', 'agent', 'calls', 'avg_duration', 'total_duration', 'input_tokens', 'output_tokens']
            
            f.write("### By Model and Agent\n\n")
            f.write(model_stats.to_markdown(index=False))
            f.write("\n\n")
            
            # Create a plot of model performance
            if len(model_df) > 0:
                plt.figure(figsize=(10, 6))
                model_df.boxplot(column='duration_seconds', by=['model', 'agent'])
                plt.title('Model Response Time by Model and Agent')
                plt.suptitle('')
                plt.ylabel('Duration (seconds)')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                plot_file = f"{output_dir}/model_performance_{timestamp}.png"
                plt.savefig(plot_file)
                
                f.write(f"![Model Performance]({os.path.basename(plot_file)})\n\n")
        
        # Task performance
        if not task_df.empty:
            f.write("## Task Performance\n\n")
            
            # Group by task and agent
            task_stats = task_df.groupby(['task', 'agent']).agg({
                'duration_seconds': ['mean', 'sum']
            }).reset_index()
            
            task_stats.columns = ['task', 'agent', 'avg_duration', 'total_duration']
            
            f.write("### By Task and Agent\n\n")
            f.write(task_stats.to_markdown(index=False))
            f.write("\n\n")
            
            # Create a plot of task performance
            if len(task_df) > 0:
                plt.figure(figsize=(10, 6))
                task_df.boxplot(column='duration_seconds', by=['task', 'agent'])
                plt.title('Task Execution Time by Task and Agent')
                plt.suptitle('')
                plt.ylabel('Duration (seconds)')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                plot_file = f"{output_dir}/task_performance_{timestamp}.png"
                plt.savefig(plot_file)
                
                f.write(f"![Task Performance]({os.path.basename(plot_file)})\n\n")
        
        # Rate limit analysis
        if not rate_limit_df.empty:
            f.write("## Rate Limit Analysis\n\n")
            
            # Group by model and agent
            rate_limit_stats = rate_limit_df.groupby(['model', 'agent']).agg({
                'attempt': ['count', 'mean', 'max'],
                'delay': ['mean', 'sum']
            }).reset_index()
            
            rate_limit_stats.columns = ['model', 'agent', 'count', 'avg_attempt', 'max_attempt', 'avg_delay', 'total_delay']
            
            f.write("### By Model and Agent\n\n")
            f.write(rate_limit_stats.to_markdown(index=False))
            f.write("\n\n")
            
            # List all rate limit errors
            f.write("### Rate Limit Errors\n\n")
            for _, row in rate_limit_df.iterrows():
                f.write(f"- **{row['model']}** (Agent: {row['agent']}): {row['error_message']} (Attempt: {row['attempt']}, Delay: {row['delay']:.2f}s)\n")
            f.write("\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        
        # Model recommendations
        if not model_df.empty:
            slow_models = model_stats[model_stats['avg_duration'] > model_stats['avg_duration'].mean()]
            if not slow_models.empty:
                f.write("### Model Optimizations\n\n")
                for _, row in slow_models.iterrows():
                    f.write(f"- Consider replacing **{row['model']}** for agent **{row['agent']}** with a faster model. Current average response time: {row['avg_duration']:.2f}s\n")
                f.write("\n")
        
        # Rate limit recommendations
        if not rate_limit_df.empty:
            f.write("### Rate Limit Mitigations\n\n")
            rate_limited_models = rate_limit_stats.sort_values('count', ascending=False)
            for _, row in rate_limited_models.iterrows():
                f.write(f"- **{row['model']}** (Agent: {row['agent']}): Experienced {row['count']} rate limits. Consider:\n")
                f.write(f"  - Increasing backoff parameters\n")
                f.write(f"  - Switching to a model with higher quotas\n")
                f.write(f"  - Requesting quota increases from AWS\n")
            f.write("\n")
    
    print(f"Report generated: {report_file}")
    return report_file

def main():
    parser = argparse.ArgumentParser(description='Analyze performance logs from the Hotel Revenue Optimization system')
    parser.add_argument('log_file', help='Path to the log file')
    parser.add_argument('--output-dir', default='output/reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    generate_report(args.log_file, args.output_dir)

if __name__ == '__main__':
    main()
