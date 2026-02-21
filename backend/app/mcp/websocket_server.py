"""
WebSocket server for real-time MCP updates and communication
"""
import json
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request

from .orchestrator import mcp_orchestrator
from .sequential_thinking import SequentialThinkingMCP
from .memory import MemoryMCP
from .context7 import Context7MCP, ContextLayer
from .filesystem import FilesystemMCP

logger = logging.getLogger(__name__)


class MCPWebSocketServer:
    """WebSocket server for MCP real-time communication"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.client_subscriptions: Dict[str, List[str]] = {}
        
        # MCP server instances
        self.sequential_thinking = SequentialThinkingMCP()
        self.memory = MemoryMCP()
        self.context7 = Context7MCP()
        self.filesystem = FilesystemMCP()
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            client_id = request.sid
            
            self.connected_clients[client_id] = {
                'id': client_id,
                'connected_at': datetime.utcnow(),
                'ip_address': request.environ.get('REMOTE_ADDR'),
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
            
            logger.info(f"WebSocket client connected: {client_id}")
            
            # Send welcome message
            emit('connected', {
                'client_id': client_id,
                'server_time': datetime.utcnow().isoformat(),
                'available_services': [
                    'sequential_thinking',
                    'memory',
                    'context7',
                    'filesystem',
                    'orchestrator'
                ]
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            client_id = request.sid
            
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            
            if client_id in self.client_subscriptions:
                del self.client_subscriptions[client_id]
            
            logger.info(f"WebSocket client disconnected: {client_id}")
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Handle subscription to specific topics"""
            client_id = request.sid
            topics = data.get('topics', [])
            
            if client_id not in self.client_subscriptions:
                self.client_subscriptions[client_id] = []
            
            for topic in topics:
                if topic not in self.client_subscriptions[client_id]:
                    self.client_subscriptions[client_id].append(topic)
                    join_room(topic)
            
            emit('subscribed', {
                'topics': self.client_subscriptions[client_id],
                'message': 'Successfully subscribed to topics'
            })
        
        @self.socketio.on('unsubscribe')
        def handle_unsubscribe(data):
            """Handle unsubscription from topics"""
            client_id = request.sid
            topics = data.get('topics', [])
            
            if client_id in self.client_subscriptions:
                for topic in topics:
                    if topic in self.client_subscriptions[client_id]:
                        self.client_subscriptions[client_id].remove(topic)
                        leave_room(topic)
            
            emit('unsubscribed', {
                'topics': topics,
                'remaining_subscriptions': self.client_subscriptions.get(client_id, [])
            })
        
        # Sequential Thinking handlers
        @self.socketio.on('thinking.create_session')
        def handle_thinking_create(data):
            """Create thinking session"""
            try:
                goal = data.get('goal', 'WebSocket thinking session')
                metadata = data.get('metadata', {})
                metadata['client_id'] = request.sid
                
                session_id = self.sequential_thinking.create_context(goal, metadata)
                
                # Broadcast to subscribers
                self._broadcast_to_topic('thinking', {
                    'event': 'session_created',
                    'session_id': session_id,
                    'goal': goal,
                    'client_id': request.sid
                })
                
                emit('thinking.session_created', {
                    'success': True,
                    'session_id': session_id,
                    'goal': goal
                })
                
            except Exception as e:
                logger.error(f"Error creating thinking session: {e}")
                emit('error', {'message': str(e), 'event': 'thinking.create_session'})
        
        @self.socketio.on('thinking.add_step')
        def handle_thinking_add_step(data):
            """Add step to thinking session"""
            try:
                session_id = data.get('session_id')
                step_type = data.get('step_type', 'observation')
                content = data.get('content', '')
                confidence = data.get('confidence', 0.8)
                
                success = self.sequential_thinking.add_step(
                    session_id, step_type, content, confidence
                )
                
                if success:
                    # Broadcast to subscribers
                    self._broadcast_to_topic(f'thinking.{session_id}', {
                        'event': 'step_added',
                        'session_id': session_id,
                        'step_type': step_type,
                        'content': content,
                        'confidence': confidence,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                emit('thinking.step_added', {
                    'success': success,
                    'session_id': session_id,
                    'step_type': step_type
                })
                
            except Exception as e:
                logger.error(f"Error adding thinking step: {e}")
                emit('error', {'message': str(e), 'event': 'thinking.add_step'})
        
        @self.socketio.on('thinking.get_context')
        def handle_thinking_get_context(data):
            """Get thinking context"""
            try:
                session_id = data.get('session_id')
                context = self.sequential_thinking.get_context(session_id)
                
                emit('thinking.context', {
                    'success': True,
                    'session_id': session_id,
                    'context': context
                })
                
            except Exception as e:
                logger.error(f"Error getting thinking context: {e}")
                emit('error', {'message': str(e), 'event': 'thinking.get_context'})
        
        # Memory handlers
        @self.socketio.on('memory.store')
        def handle_memory_store(data):
            """Store memory"""
            try:
                content = data.get('content', {})
                context = data.get('context', {})
                tags = data.get('tags', [])
                importance = data.get('importance', 0.5)
                
                # Add client context
                context['client_id'] = request.sid
                context['stored_via'] = 'websocket'
                
                memory_id = self.memory.store_memory(content, context, tags, importance)
                
                # Broadcast to memory subscribers
                self._broadcast_to_topic('memory', {
                    'event': 'memory_stored',
                    'memory_id': memory_id,
                    'tags': tags,
                    'importance': importance,
                    'client_id': request.sid
                })
                
                emit('memory.stored', {
                    'success': True,
                    'memory_id': memory_id
                })
                
            except Exception as e:
                logger.error(f"Error storing memory: {e}")
                emit('error', {'message': str(e), 'event': 'memory.store'})
        
        @self.socketio.on('memory.search')
        def handle_memory_search(data):
            """Search memories"""
            try:
                tags = data.get('tags')
                min_importance = data.get('min_importance')
                limit = data.get('limit', 10)
                
                results = self.memory.search_memories(tags, min_importance, limit)
                
                emit('memory.search_results', {
                    'success': True,
                    'results': results,
                    'count': len(results)
                })
                
            except Exception as e:
                logger.error(f"Error searching memories: {e}")
                emit('error', {'message': str(e), 'event': 'memory.search'})
        
        # Context7 handlers
        @self.socketio.on('context.set')
        def handle_context_set(data):
            """Set context value"""
            try:
                context_id = data.get('context_id')
                layer = ContextLayer(data.get('layer', 'session'))
                key = data.get('key')
                value = data.get('value')
                confidence = data.get('confidence', 1.0)
                
                success = self.context7.set_context(
                    context_id, layer, key, value, confidence, 
                    source='websocket', metadata={'client_id': request.sid}
                )
                
                if success:
                    # Broadcast to context subscribers
                    self._broadcast_to_topic(f'context.{context_id}', {
                        'event': 'context_updated',
                        'context_id': context_id,
                        'layer': layer.value,
                        'key': key,
                        'value': value,
                        'confidence': confidence,
                        'client_id': request.sid
                    })
                
                emit('context.set_result', {
                    'success': success,
                    'context_id': context_id,
                    'key': key
                })
                
            except Exception as e:
                logger.error(f"Error setting context: {e}")
                emit('error', {'message': str(e), 'event': 'context.set'})
        
        @self.socketio.on('context.get')
        def handle_context_get(data):
            """Get context value"""
            try:
                context_id = data.get('context_id')
                layer = ContextLayer(data.get('layer', 'session'))
                key = data.get('key')
                
                value = self.context7.get_context(context_id, layer, key)
                
                emit('context.value', {
                    'success': True,
                    'context_id': context_id,
                    'layer': layer.value,
                    'key': key,
                    'value': value
                })
                
            except Exception as e:
                logger.error(f"Error getting context: {e}")
                emit('error', {'message': str(e), 'event': 'context.get'})
        
        # Workflow orchestrator handlers
        @self.socketio.on('workflow.create')
        def handle_workflow_create(data):
            """Create workflow"""
            try:
                name = data.get('name', 'WebSocket Workflow')
                description = data.get('description', '')
                
                workflow_id = mcp_orchestrator.create_workflow(name, description)
                
                # Broadcast to workflow subscribers
                self._broadcast_to_topic('workflows', {
                    'event': 'workflow_created',
                    'workflow_id': workflow_id,
                    'name': name,
                    'client_id': request.sid
                })
                
                emit('workflow.created', {
                    'success': True,
                    'workflow_id': workflow_id,
                    'name': name
                })
                
            except Exception as e:
                logger.error(f"Error creating workflow: {e}")
                emit('error', {'message': str(e), 'event': 'workflow.create'})
        
        @self.socketio.on('workflow.execute')
        def handle_workflow_execute(data):
            """Execute workflow (async)"""
            try:
                workflow_id = data.get('workflow_id')
                context = data.get('context', {})
                
                # Add client context
                context['client_id'] = request.sid
                context['execution_source'] = 'websocket'
                
                # Start workflow execution in background
                self.socketio.start_background_task(
                    self._execute_workflow_background, workflow_id, context
                )
                
                emit('workflow.execution_started', {
                    'success': True,
                    'workflow_id': workflow_id,
                    'message': 'Workflow execution started'
                })
                
            except Exception as e:
                logger.error(f"Error starting workflow execution: {e}")
                emit('error', {'message': str(e), 'event': 'workflow.execute'})
        
        @self.socketio.on('workflow.status')
        def handle_workflow_status(data):
            """Get workflow status"""
            try:
                workflow_id = data.get('workflow_id')
                status = mcp_orchestrator.get_workflow_status(workflow_id)
                
                emit('workflow.status_result', {
                    'success': True,
                    'workflow_id': workflow_id,
                    'status': status
                })
                
            except Exception as e:
                logger.error(f"Error getting workflow status: {e}")
                emit('error', {'message': str(e), 'event': 'workflow.status'})
        
        # Real-time data streaming
        @self.socketio.on('stream.start')
        def handle_stream_start(data):
            """Start real-time data streaming"""
            try:
                stream_type = data.get('type', 'general')
                interval = data.get('interval', 5)  # seconds
                
                # Start streaming task
                self.socketio.start_background_task(
                    self._stream_data_background, request.sid, stream_type, interval
                )
                
                emit('stream.started', {
                    'success': True,
                    'type': stream_type,
                    'interval': interval
                })
                
            except Exception as e:
                logger.error(f"Error starting stream: {e}")
                emit('error', {'message': str(e), 'event': 'stream.start'})
    
    def _broadcast_to_topic(self, topic: str, data: Dict[str, Any]):
        """Broadcast data to all subscribers of a topic"""
        self.socketio.emit('broadcast', {
            'topic': topic,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }, room=topic)
    
    def _execute_workflow_background(self, workflow_id: str, context: Dict[str, Any]):
        """Execute workflow in background and stream updates"""
        try:
            # Create event loop for async execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Execute workflow
            result = loop.run_until_complete(
                mcp_orchestrator.execute_workflow(workflow_id, context)
            )
            
            # Broadcast completion
            self._broadcast_to_topic(f'workflow.{workflow_id}', {
                'event': 'workflow_completed',
                'workflow_id': workflow_id,
                'result': result
            })
            
            self.socketio.emit('workflow.completed', {
                'workflow_id': workflow_id,
                'result': result
            }, room=context.get('client_id'))
            
        except Exception as e:
            logger.error(f"Background workflow execution error: {e}")
            
            self._broadcast_to_topic(f'workflow.{workflow_id}', {
                'event': 'workflow_failed',
                'workflow_id': workflow_id,
                'error': str(e)
            })
            
            self.socketio.emit('workflow.failed', {
                'workflow_id': workflow_id,
                'error': str(e)
            }, room=context.get('client_id'))
    
    def _stream_data_background(self, client_id: str, stream_type: str, interval: int):
        """Stream real-time data to client"""
        try:
            while client_id in self.connected_clients:
                data = self._get_stream_data(stream_type)
                
                self.socketio.emit('stream.data', {
                    'type': stream_type,
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=client_id)
                
                self.socketio.sleep(interval)
                
        except Exception as e:
            logger.error(f"Streaming error for client {client_id}: {e}")
    
    def _get_stream_data(self, stream_type: str) -> Dict[str, Any]:
        """Get data for streaming based on type"""
        if stream_type == 'system_stats':
            import psutil
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'connected_clients': len(self.connected_clients)
            }
        
        elif stream_type == 'workflow_stats':
            return {
                'total_workflows': len(mcp_orchestrator.workflows),
                'active_workflows': len(mcp_orchestrator.active_workflows),
                'recent_workflows': [
                    mcp_orchestrator.get_workflow_status(wf_id)
                    for wf_id in list(mcp_orchestrator.workflows.keys())[-5:]
                ]
            }
        
        elif stream_type == 'memory_stats':
            return {
                'total_memories': len(self.memory.memories),
                'recent_memories': [
                    {'id': mem_id, 'timestamp': mem['timestamp'], 'tags': mem['tags']}
                    for mem_id, mem in list(self.memory.memories.items())[-5:]
                ]
            }
        
        else:
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'message': f'Streaming {stream_type} data'
            }
    
    def broadcast_system_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast system-wide events"""
        self._broadcast_to_topic('system_events', {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients"""
        return list(self.connected_clients.values())
    
    def get_client_subscriptions(self, client_id: str) -> List[str]:
        """Get subscriptions for a specific client"""
        return self.client_subscriptions.get(client_id, [])


def create_mcp_websocket_server(socketio: SocketIO) -> MCPWebSocketServer:
    """Create MCP WebSocket server instance"""
    return MCPWebSocketServer(socketio)