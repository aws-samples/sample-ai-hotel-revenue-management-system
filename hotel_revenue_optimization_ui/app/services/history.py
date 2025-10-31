import boto3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class QueryHistoryService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('HISTORY_TABLE_NAME')
        if self.table_name:
            self.table = self.dynamodb.Table(self.table_name)
        else:
            self.table = None
    
    def save_query_result(self, user_id: str, timestamp: str, query_type: str, query_summary: str, result_data: Dict, result_status: str, result_summary: str) -> bool:
        """Save query result to DynamoDB with specific parameters"""
        if not self.table or not user_id:
            return False
        
        try:
            item = {
                'user_id': user_id,
                'timestamp': timestamp,
                'query_type': query_type,
                'query_summary': query_summary,
                'query_data': json.dumps({'query': query_summary}),
                'result_status': result_status,
                'result_summary': result_summary,
                'result_data': json.dumps(result_data),
                'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
            }
            
            self.table.put_item(Item=item)
            return True
            
        except Exception as e:
            print(f"Error saving query result: {e}")
            return False

    def get_query_result(self, user_id: str, timestamp: str) -> Optional[Dict]:
        """Get specific query result by user_id and timestamp"""
        if not self.table or not user_id or not timestamp:
            return None
        
        try:
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'timestamp': timestamp
                }
            )
            return response.get('Item')
            
        except Exception as e:
            print(f"Error getting query result: {e}")
            return None

    def save_query_result(self, user_id: str, timestamp: str, query_type: str, query_summary: str, result_data: Dict, result_status: str, result_summary: str) -> bool:
        """Save query result to DynamoDB with specific parameters"""
        if not self.table or not user_id:
            return False
        
        try:
            item = {
                'user_id': user_id,
                'timestamp': timestamp,
                'query_type': query_type,
                'query_summary': query_summary,
                'query_data': json.dumps({'query': query_summary}),
                'result_status': result_status,
                'result_summary': result_summary,
                'result_data': json.dumps(result_data),
                'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
            }
            
            self.table.put_item(Item=item)
            return True
            
        except Exception as e:
            print(f"Error saving query result: {e}")
            return False

    def get_query_result(self, user_id: str, timestamp: str) -> Optional[Dict]:
        """Get specific query result by user_id and timestamp"""
        if not self.table or not user_id or not timestamp:
            return None
        
        try:
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'timestamp': timestamp
                }
            )
            return response.get('Item')
            
        except Exception as e:
            print(f"Error getting query result: {e}")
            return None

    def save_query(self, user_id: str, query_data: Dict, result_data: Dict) -> bool:
        """Save query and result to DynamoDB"""
        if not self.table or not user_id:
            return False
        
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Generate query summary
            query_summary = self._generate_query_summary(query_data)
            result_summary = self._generate_result_summary(result_data)
            
            item = {
                'user_id': user_id,
                'timestamp': timestamp,
                'query_type': query_data.get('query_type', 'natural_language'),
                'query_summary': query_summary,
                'query_data': json.dumps(query_data),
                'result_status': result_data.get('status', 'unknown'),
                'result_summary': result_summary,
                'result_data': json.dumps(result_data),
                'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
            }
            
            self.table.put_item(Item=item)
            return True
            
        except Exception as e:
            print(f"Error saving query history: {e}")
            return False
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's query history from DynamoDB"""
        if not self.table or not user_id:
            return []
        
        try:
            response = self.table.query(
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,  # Latest first
                Limit=limit
            )
            
            items = []
            for item in response.get('Items', []):
                # Parse JSON strings back to objects
                try:
                    item['query_data'] = json.loads(item.get('query_data', '{}'))
                    item['result_data'] = json.loads(item.get('result_data', '{}'))
                except json.JSONDecodeError:
                    item['query_data'] = {}
                    item['result_data'] = {}
                
                items.append(item)
            
            return items
            
        except Exception as e:
            print(f"Error retrieving query history: {e}")
            return []
    
    def get_query_result(self, user_id: str, timestamp: str) -> Optional[Dict]:
        """Get specific query result"""
        if not self.table or not user_id:
            return None
        
        try:
            response = self.table.get_item(
                Key={
                    'user_id': user_id,
                    'timestamp': timestamp
                }
            )
            
            item = response.get('Item')
            if item:
                # Parse JSON strings
                try:
                    item['query_data'] = json.loads(item.get('query_data', '{}'))
                    item['result_data'] = json.loads(item.get('result_data', '{}'))
                except json.JSONDecodeError:
                    item['query_data'] = {}
                    item['result_data'] = {}
            
            return item
            
        except Exception as e:
            print(f"Error retrieving query result: {e}")
            return None
    
    def _generate_query_summary(self, query_data: Dict) -> str:
        """Generate a human-readable summary of the query"""
        if query_data.get('query_type') == 'structured_form':
            hotel_name = query_data.get('hotel_name', 'Unknown Hotel')
            hotel_type = query_data.get('hotel_type', 'Unknown')
            location = query_data.get('location', 'Unknown Location')
            season = query_data.get('season', 'Unknown Season')
            return f"Hotel: {hotel_name}, Type: {hotel_type}, Location: {location}, Season: {season}"
        else:
            # Natural language query
            query_text = query_data.get('query', '')
            return query_text[:200] + ('...' if len(query_text) > 200 else '')
    
    def _generate_result_summary(self, result_data: Dict) -> str:
        """Generate a summary of the result"""
        status = result_data.get('status', 'unknown')
        if status == 'success':
            return "Revenue optimization recommendations"
        elif status == 'partial_success':
            return "Partial revenue recommendations"
        elif status == 'error':
            return "Query failed"
        else:
            return "Unknown result"
