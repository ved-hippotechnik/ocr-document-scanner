"""
MCP API Routes

Provides REST API endpoints for MCP servers.
"""

from flask import Blueprint, request, jsonify, current_app
import logging
from typing import Dict, Any
from ..auth.jwt_utils import jwt_required, get_current_user
from .sequential_thinking import SequentialThinkingMCP, ThinkingStage, ThoughtStep
from .filesystem import FilesystemMCP
from .memory import MemoryMCP
from .context7 import Context7MCP, ContextLayer

logger = logging.getLogger(__name__)

# Create Blueprint
mcp_bp = Blueprint('mcp', __name__, url_prefix='/api/mcp')

# Initialize MCP servers (will be properly initialized in app factory)
sequential_thinking_mcp = None
filesystem_mcp = None
memory_mcp = None
context7_mcp = None


def init_mcp_servers(app):
    """Initialize MCP servers with app context"""
    global sequential_thinking_mcp, filesystem_mcp, memory_mcp, context7_mcp
    
    sequential_thinking_mcp = SequentialThinkingMCP()
    filesystem_mcp = FilesystemMCP(base_path=app.config.get('MCP_STORAGE_PATH', 'mcp_storage'))
    memory_mcp = MemoryMCP(
        max_memory_size=app.config.get('MCP_MAX_MEMORY_SIZE', 10000),
        persistence_path=app.config.get('MCP_MEMORY_PERSISTENCE_PATH')
    )
    context7_mcp = Context7MCP()
    
    logger.info("MCP servers initialized")


# Sequential Thinking Routes
@mcp_bp.route('/thinking/create', methods=['POST'])
@jwt_required
def create_thinking_context():
    """Create a new sequential thinking context"""
    try:
        data = request.get_json()
        goal = data.get('goal', 'Process document')
        metadata = data.get('metadata', {})
        
        session_id = sequential_thinking_mcp.create_context(goal, metadata)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'goal': goal
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating thinking context: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/thinking/<session_id>/step', methods=['POST'])
@jwt_required
def add_thinking_step(session_id):
    """Add a step to the thinking process"""
    try:
        data = request.get_json()
        
        step = ThoughtStep(
            step_id=data.get('step_id', f"step_{len(sequential_thinking_mcp.contexts.get(session_id, {}).get('steps', []))}"),
            stage=ThinkingStage(data['stage']),
            description=data['description'],
            input_data=data.get('input_data', {}),
            dependencies=data.get('dependencies', [])
        )
        
        success = sequential_thinking_mcp.add_step(session_id, step)
        
        return jsonify({
            'success': success,
            'step_id': step.step_id
        }), 200 if success else 404
        
    except Exception as e:
        logger.error(f"Error adding thinking step: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/thinking/<session_id>/process', methods=['POST'])
@jwt_required
def process_thinking_step(session_id):
    """Process the next step in the thinking context"""
    try:
        result = sequential_thinking_mcp.process_next_step(session_id)
        
        if result:
            return jsonify({
                'success': True,
                'step': {
                    'step_id': result.step_id,
                    'status': result.status,
                    'output': result.output_data,
                    'error': result.error
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No pending steps or context not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error processing thinking step: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/thinking/<session_id>/status', methods=['GET'])
@jwt_required
def get_thinking_status(session_id):
    """Get the status of a thinking context"""
    try:
        status = sequential_thinking_mcp.get_context_status(session_id)
        
        if status:
            return jsonify({
                'success': True,
                'status': status
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Context not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting thinking status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Filesystem Routes
@mcp_bp.route('/filesystem/write', methods=['POST'])
@jwt_required
def write_file():
    """Write content to a file"""
    try:
        data = request.get_json()
        path = data['path']
        content = data['content']
        metadata = data.get('metadata', {})
        
        file_info = filesystem_mcp.write_file(path, content, metadata)
        
        if file_info:
            return jsonify({
                'success': True,
                'file_info': {
                    'path': file_info.path,
                    'size': file_info.size,
                    'checksum': file_info.checksum
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to write file'
            }), 500
            
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/filesystem/read/<path:path>', methods=['GET'])
@jwt_required
def read_file(path):
    """Read content from a file"""
    try:
        content = filesystem_mcp.read_file(path)
        
        if content is not None:
            return jsonify({
                'success': True,
                'content': content if isinstance(content, str) else content.decode('utf-8', errors='replace')
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/filesystem/list', methods=['GET'])
@jwt_required
def list_files():
    """List files in a directory"""
    try:
        path = request.args.get('path', '')
        pattern = request.args.get('pattern', '*')
        recursive = request.args.get('recursive', 'false').lower() == 'true'
        
        files = filesystem_mcp.list_directory(path, pattern, recursive)
        
        return jsonify({
            'success': True,
            'files': [
                {
                    'path': f.path,
                    'name': f.name,
                    'size': f.size,
                    'is_directory': f.is_directory,
                    'modified': f.modified.isoformat()
                }
                for f in files
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/filesystem/stats', methods=['GET'])
@jwt_required
def get_storage_stats():
    """Get storage statistics"""
    try:
        stats = filesystem_mcp.get_storage_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Memory Routes
@mcp_bp.route('/memory/store', methods=['POST'])
@jwt_required
def store_memory():
    """Store a new memory"""
    try:
        data = request.get_json()
        content = data['content']
        context = data.get('context', {})
        tags = data.get('tags', [])
        ttl = data.get('ttl')
        importance = data.get('importance', 1.0)
        
        memory_id = memory_mcp.store_memory(content, context, tags, ttl, importance)
        
        return jsonify({
            'success': True,
            'memory_id': memory_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/memory/retrieve/<memory_id>', methods=['GET'])
@jwt_required
def retrieve_memory(memory_id):
    """Retrieve a specific memory"""
    try:
        memory = memory_mcp.retrieve_memory(memory_id)
        
        if memory:
            return jsonify({
                'success': True,
                'memory': {
                    'memory_id': memory.memory_id,
                    'content': memory.content,
                    'context': memory.context,
                    'tags': memory.tags,
                    'timestamp': memory.timestamp.isoformat(),
                    'access_count': memory.access_count
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Memory not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error retrieving memory: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/memory/search', methods=['POST'])
@jwt_required
def search_memories():
    """Search memories"""
    try:
        data = request.get_json()
        query = data.get('query')
        tags = data.get('tags', [])
        context_filter = data.get('context_filter', {})
        limit = data.get('limit', 10)
        
        results = memory_mcp.search_memories(query, tags, context_filter, limit)
        
        return jsonify({
            'success': True,
            'results': [
                {
                    'memory_id': m.memory_id,
                    'content': m.content,
                    'tags': m.tags,
                    'importance': m.importance,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in results
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/memory/conversation/create', methods=['POST'])
@jwt_required
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json()
        initial_context = data.get('context', {})
        
        conversation_id = memory_mcp.create_conversation(initial_context)
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/memory/stats', methods=['GET'])
@jwt_required
def get_memory_stats():
    """Get memory statistics"""
    try:
        stats = memory_mcp.get_memory_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Context7 Routes
@mcp_bp.route('/context7/create', methods=['POST'])
@jwt_required
def create_context7():
    """Create a new context7 state"""
    try:
        data = request.get_json()
        context_id = data.get('context_id')
        
        context_id = context7_mcp.create_context(context_id)
        
        return jsonify({
            'success': True,
            'context_id': context_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating context7: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/context7/<context_id>/set', methods=['POST'])
@jwt_required
def set_context7(context_id):
    """Set a value in context7"""
    try:
        data = request.get_json()
        layer = ContextLayer(data['layer'])
        key = data['key']
        value = data['value']
        confidence = data.get('confidence', 1.0)
        source = data.get('source', 'api')
        metadata = data.get('metadata', {})
        
        success = context7_mcp.set_context(
            context_id, layer, key, value, 
            confidence, source, metadata
        )
        
        return jsonify({
            'success': success
        }), 200 if success else 404
        
    except Exception as e:
        logger.error(f"Error setting context7: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/context7/<context_id>/get', methods=['GET'])
@jwt_required
def get_context7(context_id):
    """Get context7 values"""
    try:
        layer = request.args.get('layer')
        key = request.args.get('key')
        
        if layer:
            layer = ContextLayer(layer)
        
        result = context7_mcp.get_context(context_id, layer, key)
        
        if result is not None:
            return jsonify({
                'success': True,
                'context': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Context not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting context7: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/context7/<context_id>/analyze', methods=['POST'])
@jwt_required
def analyze_context7(context_id):
    """Analyze context to make decisions"""
    try:
        data = request.get_json()
        query = data.get('query', {})
        
        analysis = context7_mcp.analyze_context(context_id, query)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing context7: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@mcp_bp.route('/context7/<context_id>/summary', methods=['GET'])
@jwt_required
def get_context7_summary(context_id):
    """Get context7 summary"""
    try:
        summary = context7_mcp.get_context_summary(context_id)
        
        if summary:
            return jsonify({
                'success': True,
                'summary': summary
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Context not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting context7 summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# General MCP Routes
@mcp_bp.route('/status', methods=['GET'])
def get_mcp_status():
    """Get the status of all MCP servers"""
    try:
        return jsonify({
            'success': True,
            'servers': {
                'sequential_thinking': sequential_thinking_mcp is not None,
                'filesystem': filesystem_mcp is not None,
                'memory': memory_mcp is not None,
                'context7': context7_mcp is not None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting MCP status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500