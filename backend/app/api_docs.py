"""
OpenAPI/Swagger documentation configuration
"""

from flask_restx import Api, Resource, fields, Namespace
from flask import Blueprint
import logging

logger = logging.getLogger(__name__)

# Create API documentation blueprint
api_bp = Blueprint('api_docs', __name__)

# Initialize Flask-RESTX API
api = Api(
    api_bp,
    version='2.0',
    title='OCR Document Scanner API',
    description='Advanced OCR Document Processing API with AI capabilities',
    doc='/docs',
    prefix='/api/v2',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT token in format: Bearer <token>'
        },
        'ApiKey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'API key for authentication'
        }
    },
    security=['Bearer', 'ApiKey']
)

# Define namespaces
scan_ns = Namespace('scan', description='Document scanning operations')
async_ns = Namespace('async', description='Asynchronous processing operations')
batch_ns = Namespace('batch', description='Batch processing operations')
auth_ns = Namespace('auth', description='Authentication operations')
analytics_ns = Namespace('analytics', description='Analytics and reporting')
mcp_ns = Namespace('mcp', description='Model Context Protocol operations')

# Add namespaces to API
api.add_namespace(scan_ns)
api.add_namespace(async_ns)
api.add_namespace(batch_ns)
api.add_namespace(auth_ns)
api.add_namespace(analytics_ns)
api.add_namespace(mcp_ns)

# Define common models
error_model = api.model('Error', {
    'error': fields.String(required=True, description='Error message'),
    'code': fields.Integer(description='Error code'),
    'details': fields.Raw(description='Additional error details')
})

success_response = api.model('SuccessResponse', {
    'success': fields.Boolean(required=True, default=True),
    'message': fields.String(description='Success message')
})

# Document models
document_type_enum = ['emirates_id', 'aadhaar_card', 'driving_license', 
                     'passport', 'us_drivers_license', 'unknown']

quality_metrics = api.model('QualityMetrics', {
    'overall_score': fields.Float(description='Overall quality score (0-1)'),
    'brightness': fields.Float(description='Image brightness score'),
    'contrast': fields.Float(description='Image contrast score'),
    'sharpness': fields.Float(description='Image sharpness score'),
    'orientation': fields.String(description='Image orientation')
})

extracted_data = api.model('ExtractedData', {
    'document_type': fields.String(enum=document_type_enum),
    'confidence': fields.Float(description='Classification confidence'),
    'data': fields.Raw(description='Extracted document data'),
    'quality': fields.Nested(quality_metrics),
    'validation': fields.Raw(description='Validation results')
})

# Scan models
scan_request = api.model('ScanRequest', {
    'image': fields.String(required=True, description='Base64 encoded image'),
    'document_type': fields.String(enum=document_type_enum, description='Document type hint'),
    'enhance_quality': fields.Boolean(default=True, description='Enable quality enhancement'),
    'validate_data': fields.Boolean(default=True, description='Enable data validation')
})

scan_response = api.model('ScanResponse', {
    'success': fields.Boolean(required=True),
    'scan_id': fields.Integer(description='Scan record ID'),
    'document_type': fields.String(enum=document_type_enum),
    'extracted_data': fields.Nested(extracted_data),
    'processing_time': fields.Float(description='Processing time in seconds'),
    'timestamp': fields.DateTime(description='Processing timestamp')
})

# Async models
async_scan_request = api.model('AsyncScanRequest', {
    'image': fields.String(required=True, description='Base64 encoded image'),
    'document_type': fields.String(enum=document_type_enum, description='Document type hint'),
    'priority': fields.Integer(default=0, description='Processing priority'),
    'callback_url': fields.String(description='Webhook URL for completion notification')
})

async_scan_response = api.model('AsyncScanResponse', {
    'success': fields.Boolean(required=True),
    'scan_id': fields.Integer(description='Scan record ID'),
    'task_id': fields.String(description='Celery task ID'),
    'status': fields.String(description='Task status'),
    'message': fields.String(description='Status message')
})

task_status_response = api.model('TaskStatusResponse', {
    'task_id': fields.String(required=True),
    'state': fields.String(description='Task state'),
    'ready': fields.Boolean(description='Task completion status'),
    'result': fields.Raw(description='Task result if completed'),
    'error': fields.String(description='Error message if failed'),
    'current': fields.Raw(description='Current progress information')
})

# Batch models
batch_request = api.model('BatchRequest', {
    'images': fields.List(fields.String, required=True, description='List of base64 encoded images'),
    'document_types': fields.List(fields.String, description='Document type hints'),
    'job_name': fields.String(description='Batch job name'),
    'priority': fields.Integer(default=0, description='Processing priority')
})

batch_response = api.model('BatchResponse', {
    'success': fields.Boolean(required=True),
    'job_id': fields.Integer(description='Batch job ID'),
    'task_id': fields.String(description='Celery task ID'),
    'total_documents': fields.Integer(description='Total documents in batch'),
    'status': fields.String(description='Job status'),
    'message': fields.String(description='Status message')
})

# Auth models
login_request = api.model('LoginRequest', {
    'username': fields.String(required=True, description='Username or email'),
    'password': fields.String(required=True, description='Password')
})

login_response = api.model('LoginResponse', {
    'success': fields.Boolean(required=True),
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'expires_in': fields.Integer(description='Token expiration time in seconds'),
    'user': fields.Raw(description='User information')
})

# Analytics models
analytics_request = api.model('AnalyticsRequest', {
    'start_date': fields.DateTime(description='Start date for analytics'),
    'end_date': fields.DateTime(description='End date for analytics'),
    'document_types': fields.List(fields.String, description='Filter by document types'),
    'aggregation': fields.String(enum=['hour', 'day', 'week', 'month'], default='day')
})

analytics_response = api.model('AnalyticsResponse', {
    'success': fields.Boolean(required=True),
    'data': fields.Raw(description='Analytics data'),
    'summary': fields.Raw(description='Summary statistics'),
    'charts': fields.List(fields.String, description='Generated chart URLs')
})

# MCP models
mcp_thinking_request = api.model('MCPThinkingRequest', {
    'goal': fields.String(required=True, description='Processing goal'),
    'metadata': fields.Raw(description='Additional context metadata')
})

mcp_thinking_response = api.model('MCPThinkingResponse', {
    'success': fields.Boolean(required=True),
    'session_id': fields.String(description='Thinking session ID'),
    'goal': fields.String(description='Processing goal')
})

mcp_context_request = api.model('MCPContextRequest', {
    'layer': fields.String(required=True, enum=['immediate', 'session', 'historical', 
                                               'domain', 'behavioral', 'environmental', 'global']),
    'key': fields.String(required=True, description='Context key'),
    'value': fields.Raw(required=True, description='Context value'),
    'confidence': fields.Float(default=1.0, description='Confidence score'),
    'metadata': fields.Raw(description='Additional metadata')
})

mcp_memory_request = api.model('MCPMemoryRequest', {
    'content': fields.Raw(required=True, description='Memory content'),
    'context': fields.Raw(description='Memory context'),
    'tags': fields.List(fields.String, description='Memory tags'),
    'importance': fields.Float(default=1.0, description='Importance score (0-1)')
})


def init_api_docs(app):
    """Initialize API documentation with the Flask app"""
    app.register_blueprint(api_bp)
    logger.info("API documentation initialized at /api/v2/docs")