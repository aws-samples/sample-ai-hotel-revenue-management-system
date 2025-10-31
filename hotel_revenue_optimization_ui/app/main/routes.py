from flask import render_template, redirect, url_for, flash, request, current_app, session, jsonify, Response
from app.main import bp
from app.main.forms import NaturalLanguageForm, StructuredForm
from app.api.agentcore import invoke_agentcore
from app.auth.cognito import token_required
from app.services.history import QueryHistoryService
from app.services.email_report import EmailReportService
from app.services.async_processor import async_processor
import markdown
import json
import logging
import time
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize services
history_service = QueryHistoryService()
email_service = EmailReportService()

# Create console handler if it doesn't exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

@bp.route('/')
def index():
    """Landing page with overview of the system"""
    return render_template('index.html')

@bp.route('/dashboard')
@token_required
def dashboard():
    """Main dashboard for authenticated users"""
    return render_template('dashboard.html')

@bp.route('/natural_language', methods=['GET', 'POST'])
@token_required
def natural_language():
    """Natural language interface for hotel revenue optimization"""
    logger.info("Accessing natural language interface")
    form = NaturalLanguageForm()
    result = None
    markdown_content = None
    
    # Sample queries for the user to try - sequenced for optimal demo flow
    sample_queries = [
        # Start with detailed business hotel analysis with seasonal events
        "Forecast demand for Metropolitan Business Hotel in Chicago, IL 60601 with current 65% occupancy and $220 ADR. Plan for next 3 months considering McCormick Place convention schedule, Chicago Marathon in October, and holiday business travel patterns. Target 75% occupancy by December.",
        
        # Comprehensive luxury resort with specific location and competitive landscape
        "Optimize revenue for The Grand Oceanview Resort in Miami Beach, FL 33139. 5-star luxury oceanfront property with 200 suites, premium ocean-view rooms, and standard accommodations. Current metrics: 78% occupancy, $485 ADR, $378 RevPAR. Target $420 RevPAR for Q1 2025. Competing with Fontainebleau, St. Regis, and new luxury developments. Address Art Basel Miami Beach impact and winter season pricing.",
        
        # Seasonal ski resort with summer/winter strategy
        "Create year-round revenue strategy for Sunset Mountain Resort in Aspen, CO 81611. 4.5-star ski resort with 150 rooms: standard mountain rooms, deluxe slope-view suites, and luxury chalets. Winter season: 85% occupancy, $650 ADR. Summer challenge: 45% occupancy, $280 ADR. Plan for Aspen Music Festival, hiking season, and shoulder periods. Target consistent $400 RevPAR year-round.",
        
        # Tech hub boutique with event-driven demand
        "Analyze competitor pricing for Artisan Loft boutique hotel in San Francisco, CA 94103 (SOMA district). 4-star property with 80 loft-style rooms and creative suites, currently $295 ADR, 72% occupancy. Prepare pricing strategy for Dreamforce conference, Oracle OpenWorld, and tech IPO season. Competing with Hotel Zephyr, The Phoenix, and Airbnb market.",
        
        # Budget hotel with OTA optimization focus
        "Increase RevPAR for Budget Stay Inn in Austin, TX 78701 (downtown). 3-star property with 120 standard and family rooms. Current: 82% occupancy, $95 ADR, $78 RevPAR. Target $90 RevPAR within 6 months. Address SXSW pricing, UT football season demand, and reduce 35% OTA commission dependency. Competing with Hampton Inn, Holiday Inn Express."
    ]
    
    # Pre-fill the form if query is provided in URL parameters
    if request.args.get('query') and not form.query.data:
        query = request.args.get('query')
        logger.info(f"Pre-filling form with query from URL: {query}")
        form.query.data = query
    
    if form.validate_on_submit():
        try:
            query = form.query.data
            logger.info(f"Processing natural language query: {query}")
            
            user_id = session.get('user', {}).get('sub')
            timestamp = datetime.utcnow().isoformat()
            
            # Save pending query immediately
            query_data = {
                'query_type': 'natural_language',
                'query': query
            }
            
            history_service.save_query_result(
                user_id=user_id,
                timestamp=timestamp,
                query_type='natural_language',
                query_summary=query,
                result_data={},
                result_status='processing',
                result_summary='Processing your query...'
            )
            
            # Start async processing
            async_processor.process_query_async(
                user_id=user_id,
                timestamp=timestamp,
                query_data=query_data,
                query_type='natural_language'
            )
            
            # Return JSON response with timestamp for polling
            return jsonify({
                'status': 'processing',
                'timestamp': timestamp,
                'message': 'Query submitted successfully'
            })
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            flash(f'Error processing query: {str(e)}', 'danger')
            result = {
                "summary": "Error processing query",
                "markdown_content": f"""
# Error Processing Query

We encountered an issue while processing your query. This could be due to:

- Service availability
- Network connectivity issues
- Authentication or permission issues

## Error Details

```
{str(e)}
```

Please try again in a few minutes. If the issue persists, contact your system administrator.
""",
                "status": "error",
                "completed_tasks": [],
                "failed_tasks": ["response_processing"]
            }
            markdown_content = markdown.markdown(
                result['markdown_content'],
                extensions=['tables', 'fenced_code']
            )
    
    return render_template(
        'natural_language.html',
        form=form,
        result=result,
        markdown_content=markdown_content,
        sample_queries=sample_queries
    )

@bp.route('/structured_form', methods=['GET', 'POST'])
@token_required
def structured_form():
    """Structured form interface for hotel revenue optimization"""
    logger.info("Accessing structured form interface")
    form = StructuredForm()
    result = None
    markdown_content = None
    
    if form.validate_on_submit():
        try:
            # Build the payload from form data
            payload = {
                "query_type": "structured",
                "hotel_name": form.hotel_name.data,
                "hotel_type": form.hotel_type.data,
                "location": form.location.data,
                "season": form.season.data,
                "star_rating": form.star_rating.data,
                "occupancy_rate": form.occupancy_rate.data,
                "competitor_analysis": form.competitor_analysis.data,
                "optimization_goal": form.optimization_goal.data
            }
            
            logger.info(f"Processing structured form: hotel_name={payload['hotel_name']}, hotel_type={payload['hotel_type']}")
            
            user_id = session.get('user', {}).get('sub')
            timestamp = datetime.utcnow().isoformat()
            
            # Save pending query immediately
            history_service.save_query_result(
                user_id=user_id,
                timestamp=timestamp,
                query_type='structured_form',
                query_summary=f"{payload['hotel_name']} - {payload['optimization_goal']}",
                result_data={},
                result_status='processing',
                result_summary='Processing your analysis...'
            )
            
            # Start async processing
            async_processor.process_query_async(
                user_id=user_id,
                timestamp=timestamp,
                query_data=payload,
                query_type='structured_form'
            )
            
            flash('Your analysis has been submitted and is being processed. Check your history for results.', 'success')
            return jsonify({
                'status': 'processing',
                'timestamp': timestamp,
                'message': 'Analysis submitted successfully'
            })
        
        except Exception as e:
            response_content = response.get('markdown_content') or response.get('report', '')
            if response_content and response_content.strip().startswith('{'):
                try:
                    # Try to parse the content as JSON (it might be an error response)
                    import json
                    logger.info(f"Structured Form - Attempting to parse response content as JSON: {response_content[:200]}...")
                    error_data = json.loads(response_content)
                    if error_data.get('status') == 'error':
                        logger.info("Structured Form - Detected JSON error response")
                        logger.info(f"Structured Form - Error data: {error_data}")
                        # Update the result with parsed error data
                        result.update(error_data)
                        # Clear the content fields since they're now parsed
                        result['markdown_content'] = None
                        result['report'] = None
                        logger.info(f"Structured Form - Updated result: {result}")
                except (json.JSONDecodeError, ValueError) as e:
                    # If it's not valid JSON, treat it as regular content
                    logger.info(f"Structured Form - Failed to parse as JSON: {e}")
                    pass
            
            # Check if there was an error
            if "error" in response or result.get('status') == 'error':
                error_msg = response.get('error') or result.get('message', 'Unknown error occurred')
                logger.error(f"Error in AgentCore response: {error_msg}")
                flash(f"Error: {error_msg}", 'danger')
            else:
                # Handle the new response schema with 'report' field
                if 'report' in response and response['report'] and not result.get('status') == 'error':
                    logger.info("Converting report content to HTML")
                    markdown_content = markdown.markdown(
                        response['report'],
                        extensions=['tables', 'fenced_code']
                    )
                elif 'markdown_content' in response and response['markdown_content'] and not result.get('status') == 'error':
                    logger.info("Converting markdown_content to HTML")
                    markdown_content = markdown.markdown(
                        response['markdown_content'],
                        extensions=['tables', 'fenced_code']
                    )
                    logger.info("Converting markdown content to HTML")
                    markdown_content = markdown.markdown(
                        response['markdown_content'],
                        extensions=['tables', 'fenced_code']
                    )
                
                # Save to session for history
                if 'query_history' not in session:
                    session['query_history'] = []
                
                logger.info("Adding query to history")
                session['query_history'].append({
                    'query': f"Hotel: {payload['hotel_name']}, Type: {payload['hotel_type']}, Location: {payload['location']}, Season: {payload['season']}",
                    'timestamp': datetime.now().isoformat(),
                    'result_summary': response.get('summary', 'No summary available'),
                    'status': response.get('status', 'unknown')
                })
                session.modified = True
                
                flash('Form processed successfully', 'success')
        
        except Exception as e:
            logger.error(f"Error processing form: {str(e)}", exc_info=True)
            flash(f'Error processing form: {str(e)}', 'danger')
            result = {
                "summary": "Error processing form",
                "markdown_content": f"""
# Error Processing Form

We encountered an issue while processing your form submission. This could be due to:

- Service availability
- Network connectivity issues
- Authentication or permission issues

## Error Details

```
{str(e)}
```

Please try again in a few minutes. If the issue persists, contact your system administrator.
""",
                "status": "error",
                "completed_tasks": [],
                "failed_tasks": ["response_processing"]
            }
            markdown_content = markdown.markdown(
                result['markdown_content'],
                extensions=['tables', 'fenced_code']
            )
    
    return render_template(
        'structured_form.html',
        form=form,
        result=result,
        markdown_content=markdown_content
    )

@bp.route('/history')
@token_required
def history():
    """View history of queries and results"""
    logger.info("Accessing history page")
    
    # Get history from DynamoDB if user is authenticated
    user_id = session.get('user', {}).get('sub')
    if user_id:
        query_history = history_service.get_user_history(user_id)
    else:
        query_history = []
    
    return render_template('history.html', query_history=query_history)

@bp.route('/history/<timestamp>')
@token_required
def view_history_result(timestamp):
    """View a specific query result from history"""
    user_id = session.get('user', {}).get('sub')
    if not user_id:
        flash('Authentication required', 'error')
        return redirect(url_for('main.index'))
    
    # Get the specific query result
    query_result = history_service.get_query_result(user_id, timestamp)
    if not query_result:
        flash('Query result not found', 'error')
        return redirect(url_for('main.history'))
    
    # Process the result data for display
    result_data = query_result.get('result_data', {})
    markdown_content = None
    error_details = None
    
    if result_data.get('markdown_content'):
        markdown_content = markdown.markdown(
            result_data['markdown_content'],
            extensions=['tables', 'fenced_code']
        )
    
    # Parse JSON error messages for better display
    if query_result.get('result_status') in ['failed', 'error'] and query_result.get('result_summary'):
        error_message = query_result.get('result_summary', '')
        if error_message.startswith('{') and error_message.endswith('}'):
            try:
                import json
                error_details = json.loads(error_message)
            except:
                pass
    
    return render_template('history_result.html', 
                         query_result=query_result,
                         result=result_data,
                         markdown_content=markdown_content,
                         error_details=error_details)

@bp.route('/send-email-report', methods=['POST'])
@token_required
def send_email_report():
    """Send email report for a query result"""
    logger.info("Email report endpoint called")
    try:
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        recipient_email = data.get('email') if data else None
        timestamp = data.get('timestamp') if data else None
        
        logger.info(f"Email: {recipient_email}, Timestamp: {timestamp}")
        
        if not recipient_email or not timestamp:
            logger.warning("Missing email or timestamp")
            return jsonify({'success': False, 'message': 'Email and timestamp required'}), 400
        
        user_id = session.get('user', {}).get('sub')
        user_email = session.get('user', {}).get('email', 'unknown@example.com')
        
        logger.info(f"User ID: {user_id}, User Email: {user_email}")
        
        # Get query result
        query_result = history_service.get_query_result(user_id, timestamp)
        if not query_result:
            logger.warning(f"Query result not found for user {user_id}, timestamp {timestamp}")
            return jsonify({'success': False, 'message': 'Query result not found'}), 404
        
        # Send email
        success = email_service.send_report_email(
            recipient_email=recipient_email,
            cc_email=user_email,
            report_data=query_result.get('result_data', {}),
            query_summary=query_result.get('query_summary', 'Hotel Revenue Analysis')
        )
        
        logger.info(f"Email send result: {success}")
        
        if success:
            return jsonify({'success': True, 'message': 'Report sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send report'}), 500
            
    except Exception as e:
        logger.error(f"Error sending email report: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@bp.route('/check-query-status/<timestamp>')
@token_required
def check_query_status(timestamp):
    """Check the status of a processing query"""
    try:
        user_id = session.get('user', {}).get('sub')
        query_result = history_service.get_query_result(user_id, timestamp)
        
        if not query_result:
            return jsonify({'status': 'not_found'})
        
        # If query is marked as failed but was submitted recently (within 5 minutes), 
        # keep showing as processing to give it more time
        if query_result.get('result_status') == 'failed':
            from datetime import datetime, timedelta
            try:
                # Parse timestamp (format: YYYY-MM-DD HH:MM:SS)
                query_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                time_elapsed = datetime.now() - query_time
                
                # If less than 5 minutes have passed, show as processing
                if time_elapsed < timedelta(minutes=5):
                    # Use the original summary if it indicates processing
                    original_summary = query_result.get('result_summary', '')
                    if 'Processing' in original_summary or 'processing' in original_summary:
                        summary = original_summary
                    else:
                        summary = 'Processing your request...'
                        
                    return jsonify({
                        'status': 'processing',
                        'summary': summary,
                        'timestamp': timestamp
                    })
            except:
                pass  # If timestamp parsing fails, use original status
        
        return jsonify({
            'status': query_result.get('result_status', 'unknown'),
            'summary': query_result.get('result_summary', ''),
            'timestamp': query_result.get('timestamp', '')
        })
        
    except Exception as e:
        logger.error(f"Error checking query status: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@bp.route('/check-status', methods=['POST'])
@token_required
def check_status():
    """Check the status of a query"""
    logger.info("Checking query status")
    
    # Get the query ID from the request
    data = request.get_json()
    query_id = data.get('query_id')
    
    if not query_id:
        logger.warning("No query ID provided")
        return jsonify({'status': 'error', 'message': 'No query ID provided'})
    
    # In a real application, you would check the status of the query in a database or queue
    # For this example, we'll just return a success status
    logger.info(f"Query {query_id} is complete")
    return jsonify({'status': 'complete'})

@bp.route('/refresh-history', methods=['GET'])
@token_required
def refresh_history():
    """Refresh the query history"""
    logger.info("Refreshing query history")
    
    # Get the query history from the session
    query_history = session.get('query_history', [])
    
    # Return the query history as JSON
    return jsonify({'history': query_history})
@bp.route('/help')
@token_required
def help():
    """Help page with documentation and usage instructions"""
    logger.info("Accessing help page")
    return render_template('help.html')
