"""
MCP Orchestrator for coordinated workflows
Manages complex multi-step processes using multiple MCP servers
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import asyncio
import json

from .sequential_thinking import SequentialThinkingMCP
from .memory import MemoryMCP
from .context7 import Context7MCP, ContextLayer
from .filesystem import FilesystemMCP

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    """Individual workflow step"""
    
    def __init__(self, 
                 step_id: str,
                 name: str,
                 step_type: str,
                 handler: Callable,
                 dependencies: List[str] = None,
                 config: Dict[str, Any] = None):
        self.step_id = step_id
        self.name = name
        self.step_type = step_type
        self.handler = handler
        self.dependencies = dependencies or []
        self.config = config or {}
        self.status = WorkflowStatus.PENDING
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None


class Workflow:
    """Workflow definition and execution container"""
    
    def __init__(self, workflow_id: str, name: str, description: str = ""):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps: Dict[str, WorkflowStep] = {}
        self.status = WorkflowStatus.PENDING
        self.context = {}
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.error = None
    
    def add_step(self, 
                 step_id: str,
                 name: str,
                 step_type: str,
                 handler: Callable,
                 dependencies: List[str] = None,
                 config: Dict[str, Any] = None):
        """Add a step to the workflow"""
        step = WorkflowStep(step_id, name, step_type, handler, dependencies, config)
        self.steps[step_id] = step
        return step
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)"""
        ready_steps = []
        
        for step in self.steps.values():
            if step.status != WorkflowStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            all_deps_completed = all(
                self.steps[dep_id].status == WorkflowStatus.COMPLETED
                for dep_id in step.dependencies
                if dep_id in self.steps
            )
            
            if all_deps_completed:
                ready_steps.append(step)
        
        return ready_steps
    
    def is_complete(self) -> bool:
        """Check if workflow is complete"""
        return all(
            step.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
            for step in self.steps.values()
        )
    
    def has_failed_steps(self) -> bool:
        """Check if any steps have failed"""
        return any(step.status == WorkflowStatus.FAILED for step in self.steps.values())


class MCPOrchestrator:
    """Orchestrator for coordinated MCP workflows"""
    
    def __init__(self):
        self.sequential_thinking = SequentialThinkingMCP()
        self.memory = MemoryMCP()
        self.context7 = Context7MCP()
        self.filesystem = FilesystemMCP()
        
        self.workflows: Dict[str, Workflow] = {}
        self.active_workflows: Dict[str, Workflow] = {}
        
        # Register built-in workflow handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register built-in workflow step handlers"""
        self.handlers = {
            'thinking.create_session': self._handle_thinking_create,
            'thinking.add_step': self._handle_thinking_add_step,
            'memory.store': self._handle_memory_store,
            'memory.retrieve': self._handle_memory_retrieve,
            'memory.search': self._handle_memory_search,
            'context.set': self._handle_context_set,
            'context.get': self._handle_context_get,
            'filesystem.write': self._handle_filesystem_write,
            'filesystem.read': self._handle_filesystem_read,
            'document.classify': self._handle_document_classify,
            'document.extract': self._handle_document_extract,
            'document.validate': self._handle_document_validate,
            'workflow.conditional': self._handle_conditional,
            'workflow.parallel': self._handle_parallel,
            'workflow.delay': self._handle_delay
        }
    
    def create_workflow(self, name: str, description: str = "") -> str:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(workflow_id, name, description)
        self.workflows[workflow_id] = workflow
        
        logger.info(f"Created workflow '{name}' with ID: {workflow_id}")
        return workflow_id
    
    def add_workflow_step(self,
                         workflow_id: str,
                         step_id: str,
                         name: str,
                         step_type: str,
                         dependencies: List[str] = None,
                         config: Dict[str, Any] = None) -> bool:
        """Add a step to an existing workflow"""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return False
        
        workflow = self.workflows[workflow_id]
        
        if step_type not in self.handlers:
            logger.error(f"Unknown step type: {step_type}")
            return False
        
        handler = self.handlers[step_type]
        workflow.add_step(step_id, name, step_type, handler, dependencies, config)
        
        logger.info(f"Added step '{name}' to workflow {workflow_id}")
        return True
    
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        workflow.context.update(context or {})
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        
        self.active_workflows[workflow_id] = workflow
        
        try:
            # Create thinking session for the workflow
            thinking_session = self.sequential_thinking.create_context(
                goal=f"Execute workflow: {workflow.name}",
                metadata={
                    'workflow_id': workflow_id,
                    'workflow_name': workflow.name,
                    'step_count': len(workflow.steps)
                }
            )
            workflow.context['thinking_session'] = thinking_session
            
            # Set initial context
            context_id = f"workflow_{workflow_id}"
            self.context7.set_context(
                context_id, ContextLayer.SESSION, 'workflow_status', 'running'
            )
            
            logger.info(f"Starting execution of workflow {workflow_id}")
            
            # Execute workflow steps
            while not workflow.is_complete():
                ready_steps = workflow.get_ready_steps()
                
                if not ready_steps:
                    # Check if we're stuck (no ready steps but not complete)
                    if not workflow.is_complete():
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error = "Workflow stuck - no ready steps available"
                        break
                    else:
                        break
                
                # Execute ready steps (could be parallelized)
                for step in ready_steps:
                    await self._execute_step(workflow, step)
            
            # Determine final status
            if workflow.has_failed_steps():
                workflow.status = WorkflowStatus.FAILED
            else:
                workflow.status = WorkflowStatus.COMPLETED
            
            workflow.completed_at = datetime.utcnow()
            
            # Store final result in memory
            workflow_result = {
                'workflow_id': workflow_id,
                'name': workflow.name,
                'status': workflow.status.value,
                'steps_completed': sum(1 for s in workflow.steps.values() if s.status == WorkflowStatus.COMPLETED),
                'total_steps': len(workflow.steps),
                'duration_seconds': (workflow.completed_at - workflow.started_at).total_seconds(),
                'context': workflow.context
            }
            
            memory_id = self.memory.store_memory(
                content=workflow_result,
                context={'workflow_id': workflow_id, 'type': 'workflow_result'},
                tags=['workflow', 'execution', workflow.status.value],
                importance=0.8
            )
            
            # Final thinking step
            self.sequential_thinking.add_step(
                thinking_session,
                'conclusion',
                f"Workflow {workflow.status.value}: {workflow.name}",
                0.95 if workflow.status == WorkflowStatus.COMPLETED else 0.3
            )
            
            logger.info(f"Workflow {workflow_id} completed with status: {workflow.status.value}")
            
            return {
                'workflow_id': workflow_id,
                'status': workflow.status.value,
                'memory_id': memory_id,
                'thinking_session': thinking_session,
                'result': workflow_result
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.utcnow()
            
            logger.error(f"Workflow {workflow_id} failed: {e}")
            raise
        
        finally:
            # Clean up active workflows
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep):
        """Execute a single workflow step"""
        step.status = WorkflowStatus.RUNNING
        step.started_at = datetime.utcnow()
        
        # Add thinking step
        thinking_session = workflow.context.get('thinking_session')
        if thinking_session:
            self.sequential_thinking.add_step(
                thinking_session,
                'action',
                f"Executing step: {step.name}",
                0.8
            )
        
        try:
            # Prepare step context
            step_context = {
                'workflow': workflow,
                'step': step,
                'orchestrator': self
            }
            
            # Execute step handler
            step.result = await step.handler(step_context)
            step.status = WorkflowStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            
            logger.info(f"Step '{step.name}' completed successfully")
            
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.utcnow()
            
            logger.error(f"Step '{step.name}' failed: {e}")
            
            # Add error to thinking process
            if thinking_session:
                self.sequential_thinking.add_step(
                    thinking_session,
                    'error',
                    f"Step '{step.name}' failed: {str(e)}",
                    0.2
                )
    
    # Built-in step handlers
    
    async def _handle_thinking_create(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a thinking session"""
        config = context['step'].config
        session_id = self.sequential_thinking.create_context(
            goal=config.get('goal', 'Default thinking session'),
            metadata=config.get('metadata', {})
        )
        return {'session_id': session_id}
    
    async def _handle_thinking_add_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add a step to thinking session"""
        config = context['step'].config
        session_id = config.get('session_id')
        
        if not session_id:
            # Use workflow thinking session
            session_id = context['workflow'].context.get('thinking_session')
        
        success = self.sequential_thinking.add_step(
            session_id=session_id,
            step_type=config.get('step_type', 'observation'),
            content=config.get('content', ''),
            confidence=config.get('confidence', 0.8)
        )
        return {'success': success}
    
    async def _handle_memory_store(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Store data in memory"""
        config = context['step'].config
        memory_id = self.memory.store_memory(
            content=config.get('content', {}),
            context=config.get('context', {}),
            tags=config.get('tags', []),
            importance=config.get('importance', 0.5)
        )
        return {'memory_id': memory_id}
    
    async def _handle_memory_retrieve(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve data from memory"""
        config = context['step'].config
        memory_id = config.get('memory_id')
        memory = self.memory.retrieve_memory(memory_id)
        return {'memory': memory}
    
    async def _handle_memory_search(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories"""
        config = context['step'].config
        results = self.memory.search_memories(
            tags=config.get('tags'),
            min_importance=config.get('min_importance'),
            limit=config.get('limit', 10)
        )
        return {'results': results, 'count': len(results)}
    
    async def _handle_context_set(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Set context value"""
        config = context['step'].config
        workflow_id = context['workflow'].workflow_id
        context_id = config.get('context_id', f"workflow_{workflow_id}")
        
        success = self.context7.set_context(
            context_id=context_id,
            layer=ContextLayer(config.get('layer', 'session')),
            key=config.get('key'),
            value=config.get('value'),
            confidence=config.get('confidence', 1.0)
        )
        return {'success': success}
    
    async def _handle_context_get(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get context value"""
        config = context['step'].config
        workflow_id = context['workflow'].workflow_id
        context_id = config.get('context_id', f"workflow_{workflow_id}")
        
        value = self.context7.get_context(
            context_id=context_id,
            layer=ContextLayer(config.get('layer', 'session')),
            key=config.get('key')
        )
        return {'value': value}
    
    async def _handle_filesystem_write(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write file to filesystem"""
        config = context['step'].config
        success = self.filesystem.write_file(
            filename=config.get('filename'),
            content=config.get('content')
        )
        return {'success': success}
    
    async def _handle_filesystem_read(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Read file from filesystem"""
        config = context['step'].config
        content = self.filesystem.read_file(config.get('filename'))
        return {'content': content}
    
    async def _handle_document_classify(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify document (placeholder)"""
        config = context['step'].config
        # This would integrate with the actual document classification system
        return {
            'document_type': 'aadhaar_card',
            'confidence': 0.95,
            'details': config.get('document_data', {})
        }
    
    async def _handle_document_extract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract document data (placeholder)"""
        config = context['step'].config
        # This would integrate with the actual document extraction system
        return {
            'extracted_data': config.get('mock_data', {}),
            'confidence': 0.9
        }
    
    async def _handle_document_validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document (placeholder)"""
        config = context['step'].config
        # This would integrate with the actual document validation system
        return {
            'is_valid': True,
            'validation_score': 0.95,
            'issues': []
        }
    
    async def _handle_conditional(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conditional execution"""
        config = context['step'].config
        condition = config.get('condition')
        
        # Evaluate condition (simple string evaluation for now)
        # In production, this would be more sophisticated
        try:
            result = eval(condition, {'workflow': context['workflow']})
            return {'condition_result': result, 'executed': result}
        except Exception as e:
            return {'condition_result': False, 'error': str(e)}
    
    async def _handle_parallel(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parallel execution of sub-steps"""
        config = context['step'].config
        sub_steps = config.get('sub_steps', [])
        
        # Execute sub-steps in parallel
        tasks = []
        for sub_step in sub_steps:
            # Create sub-step execution task
            task = asyncio.create_task(self._execute_substep(context, sub_step))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'sub_step_results': results,
            'success_count': sum(1 for r in results if not isinstance(r, Exception))
        }
    
    async def _handle_delay(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add delay to workflow"""
        config = context['step'].config
        delay_seconds = config.get('delay_seconds', 1)
        
        await asyncio.sleep(delay_seconds)
        
        return {'delayed_seconds': delay_seconds}
    
    async def _execute_substep(self, parent_context: Dict[str, Any], sub_step_config: Dict[str, Any]):
        """Execute a sub-step"""
        step_type = sub_step_config.get('type')
        if step_type in self.handlers:
            handler = self.handlers[step_type]
            sub_context = {
                **parent_context,
                'step': type('Step', (), {'config': sub_step_config})()
            }
            return await handler(sub_context)
        else:
            raise ValueError(f"Unknown sub-step type: {step_type}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        step_statuses = {}
        for step_id, step in workflow.steps.items():
            step_statuses[step_id] = {
                'name': step.name,
                'status': step.status.value,
                'started_at': step.started_at.isoformat() if step.started_at else None,
                'completed_at': step.completed_at.isoformat() if step.completed_at else None,
                'error': step.error
            }
        
        return {
            'workflow_id': workflow_id,
            'name': workflow.name,
            'description': workflow.description,
            'status': workflow.status.value,
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'steps': step_statuses,
            'error': workflow.error
        }
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        return [self.get_workflow_status(wf_id) for wf_id in self.workflows.keys()]
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.utcnow()
            
            # Cancel running steps
            for step in workflow.steps.values():
                if step.status == WorkflowStatus.RUNNING:
                    step.status = WorkflowStatus.CANCELLED
                    step.completed_at = datetime.utcnow()
            
            logger.info(f"Cancelled workflow {workflow_id}")
            return True
        
        return False


# Global orchestrator instance
mcp_orchestrator = MCPOrchestrator()