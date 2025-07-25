"""
Sequential Thinking MCP Server

Provides step-by-step reasoning and planning capabilities for complex document processing tasks.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ThinkingStage(Enum):
    """Stages of sequential thinking process"""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    VALIDATION = "validation"
    COMPLETION = "completion"


@dataclass
class ThoughtStep:
    """Represents a single step in the thinking process"""
    step_id: str
    stage: ThinkingStage
    description: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: str = "pending"
    timestamp: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ThinkingContext:
    """Context for a sequential thinking session"""
    session_id: str
    goal: str
    steps: List[ThoughtStep] = field(default_factory=list)
    current_stage: ThinkingStage = ThinkingStage.ANALYSIS
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class SequentialThinkingMCP:
    """
    Sequential Thinking MCP Server
    
    Provides structured thinking and planning capabilities for document processing.
    """
    
    def __init__(self):
        self.contexts: Dict[str, ThinkingContext] = {}
        self.step_processors = {
            ThinkingStage.ANALYSIS: self._process_analysis,
            ThinkingStage.PLANNING: self._process_planning,
            ThinkingStage.EXECUTION: self._process_execution,
            ThinkingStage.VALIDATION: self._process_validation,
            ThinkingStage.COMPLETION: self._process_completion
        }
    
    def create_context(self, goal: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new thinking context"""
        import uuid
        session_id = str(uuid.uuid4())
        
        context = ThinkingContext(
            session_id=session_id,
            goal=goal,
            metadata=metadata or {}
        )
        
        self.contexts[session_id] = context
        logger.info(f"Created thinking context {session_id} for goal: {goal}")
        
        return session_id
    
    def add_step(self, session_id: str, step: ThoughtStep) -> bool:
        """Add a step to the thinking process"""
        if session_id not in self.contexts:
            logger.error(f"Context {session_id} not found")
            return False
        
        context = self.contexts[session_id]
        context.steps.append(step)
        
        logger.debug(f"Added step {step.step_id} to context {session_id}")
        return True
    
    def process_next_step(self, session_id: str) -> Optional[ThoughtStep]:
        """Process the next pending step in the context"""
        if session_id not in self.contexts:
            logger.error(f"Context {session_id} not found")
            return None
        
        context = self.contexts[session_id]
        
        # Find next pending step
        pending_steps = [s for s in context.steps if s.status == "pending"]
        if not pending_steps:
            logger.info(f"No pending steps in context {session_id}")
            return None
        
        # Check dependencies
        next_step = None
        for step in pending_steps:
            if self._check_dependencies(context, step):
                next_step = step
                break
        
        if not next_step:
            logger.warning(f"No steps with satisfied dependencies in context {session_id}")
            return None
        
        # Process the step
        processor = self.step_processors.get(next_step.stage)
        if processor:
            try:
                next_step.status = "processing"
                output_data = processor(context, next_step)
                next_step.output_data = output_data
                next_step.status = "completed"
                
                # Update context stage if needed
                self._update_context_stage(context)
                
            except Exception as e:
                logger.error(f"Error processing step {next_step.step_id}: {str(e)}")
                next_step.status = "failed"
                next_step.error = str(e)
        
        return next_step
    
    def _check_dependencies(self, context: ThinkingContext, step: ThoughtStep) -> bool:
        """Check if all dependencies for a step are satisfied"""
        for dep_id in step.dependencies:
            dep_step = next((s for s in context.steps if s.step_id == dep_id), None)
            if not dep_step or dep_step.status != "completed":
                return False
        return True
    
    def _update_context_stage(self, context: ThinkingContext):
        """Update the context stage based on completed steps"""
        stage_steps = {stage: [] for stage in ThinkingStage}
        
        for step in context.steps:
            stage_steps[step.stage].append(step)
        
        # Check if all steps in current stage are completed
        current_stage_steps = stage_steps[context.current_stage]
        if all(s.status == "completed" for s in current_stage_steps):
            # Move to next stage
            stages = list(ThinkingStage)
            current_index = stages.index(context.current_stage)
            if current_index < len(stages) - 1:
                context.current_stage = stages[current_index + 1]
                logger.info(f"Context {context.session_id} moved to stage: {context.current_stage}")
    
    def _process_analysis(self, context: ThinkingContext, step: ThoughtStep) -> Dict[str, Any]:
        """Process an analysis step"""
        logger.info(f"Processing analysis step: {step.description}")
        
        # Analyze the input data
        input_data = step.input_data
        analysis_result = {
            "document_type": input_data.get("document_type", "unknown"),
            "complexity": self._assess_complexity(input_data),
            "required_processors": self._identify_processors(input_data),
            "quality_score": input_data.get("quality_score", 0.0),
            "recommendations": []
        }
        
        # Add recommendations based on analysis
        if analysis_result["complexity"] == "high":
            analysis_result["recommendations"].append("Use advanced preprocessing")
        
        if analysis_result["quality_score"] < 0.5:
            analysis_result["recommendations"].append("Enhance image quality before processing")
        
        return analysis_result
    
    def _process_planning(self, context: ThinkingContext, step: ThoughtStep) -> Dict[str, Any]:
        """Process a planning step"""
        logger.info(f"Processing planning step: {step.description}")
        
        # Create execution plan based on analysis
        analysis_steps = [s for s in context.steps if s.stage == ThinkingStage.ANALYSIS and s.status == "completed"]
        
        plan = {
            "execution_order": [],
            "resource_requirements": {},
            "estimated_duration": 0,
            "parallel_tasks": []
        }
        
        # Build execution plan
        for analysis_step in analysis_steps:
            if analysis_step.output_data:
                processors = analysis_step.output_data.get("required_processors", [])
                for processor in processors:
                    plan["execution_order"].append({
                        "processor": processor,
                        "priority": self._get_processor_priority(processor),
                        "dependencies": []
                    })
        
        # Sort by priority
        plan["execution_order"].sort(key=lambda x: x["priority"], reverse=True)
        
        return plan
    
    def _process_execution(self, context: ThinkingContext, step: ThoughtStep) -> Dict[str, Any]:
        """Process an execution step"""
        logger.info(f"Processing execution step: {step.description}")
        
        # Execute the planned action
        result = {
            "action": step.description,
            "status": "executed",
            "metrics": {
                "start_time": datetime.now().isoformat(),
                "duration": 0,
                "resources_used": {}
            }
        }
        
        # Simulate execution based on input
        if "processor" in step.input_data:
            processor_name = step.input_data["processor"]
            result["processor_output"] = f"Processed with {processor_name}"
            result["metrics"]["duration"] = 1.5  # Simulated duration
        
        return result
    
    def _process_validation(self, context: ThinkingContext, step: ThoughtStep) -> Dict[str, Any]:
        """Process a validation step"""
        logger.info(f"Processing validation step: {step.description}")
        
        # Validate execution results
        execution_steps = [s for s in context.steps if s.stage == ThinkingStage.EXECUTION and s.status == "completed"]
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "quality_metrics": {}
        }
        
        # Check each execution result
        for exec_step in execution_steps:
            if exec_step.output_data:
                if exec_step.output_data.get("status") != "executed":
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Step {exec_step.step_id} failed")
        
        return validation_result
    
    def _process_completion(self, context: ThinkingContext, step: ThoughtStep) -> Dict[str, Any]:
        """Process a completion step"""
        logger.info(f"Processing completion step: {step.description}")
        
        # Summarize the entire process
        summary = {
            "goal": context.goal,
            "total_steps": len(context.steps),
            "completed_steps": len([s for s in context.steps if s.status == "completed"]),
            "failed_steps": len([s for s in context.steps if s.status == "failed"]),
            "duration": (datetime.now() - context.created_at).total_seconds(),
            "final_output": {}
        }
        
        # Collect outputs from all stages
        for stage in ThinkingStage:
            stage_outputs = []
            for s in context.steps:
                if s.stage == stage and s.output_data:
                    stage_outputs.append(s.output_data)
            if stage_outputs:
                summary["final_output"][stage.value] = stage_outputs
        
        context.completed_at = datetime.now()
        
        return summary
    
    def _assess_complexity(self, input_data: Dict[str, Any]) -> str:
        """Assess the complexity of the task"""
        # Simple heuristic based on input data
        if input_data.get("batch_size", 1) > 10:
            return "high"
        elif input_data.get("document_type") in ["passport", "emirates_id"]:
            return "medium"
        else:
            return "low"
    
    def _identify_processors(self, input_data: Dict[str, Any]) -> List[str]:
        """Identify required processors based on input"""
        processors = []
        
        doc_type = input_data.get("document_type", "")
        if doc_type:
            processors.append(f"{doc_type}_processor")
        
        if input_data.get("require_validation", False):
            processors.append("validation_processor")
        
        if input_data.get("require_security_check", False):
            processors.append("security_processor")
        
        return processors
    
    def _get_processor_priority(self, processor: str) -> int:
        """Get priority for a processor"""
        priority_map = {
            "security_processor": 10,
            "validation_processor": 8,
            "passport_processor": 6,
            "emirates_id_processor": 6,
            "aadhaar_processor": 5,
            "driving_license_processor": 5
        }
        return priority_map.get(processor, 1)
    
    def get_context_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a thinking context"""
        if session_id not in self.contexts:
            return None
        
        context = self.contexts[session_id]
        return {
            "session_id": session_id,
            "goal": context.goal,
            "current_stage": context.current_stage.value,
            "total_steps": len(context.steps),
            "completed_steps": len([s for s in context.steps if s.status == "completed"]),
            "pending_steps": len([s for s in context.steps if s.status == "pending"]),
            "failed_steps": len([s for s in context.steps if s.status == "failed"]),
            "created_at": context.created_at.isoformat(),
            "completed_at": context.completed_at.isoformat() if context.completed_at else None
        }
    
    def export_thinking_trace(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export the complete thinking trace for analysis"""
        if session_id not in self.contexts:
            return None
        
        context = self.contexts[session_id]
        return {
            "session_id": session_id,
            "goal": context.goal,
            "metadata": context.metadata,
            "stages": {
                stage.value: [
                    {
                        "step_id": step.step_id,
                        "description": step.description,
                        "status": step.status,
                        "input": step.input_data,
                        "output": step.output_data,
                        "error": step.error,
                        "timestamp": step.timestamp.isoformat()
                    }
                    for step in context.steps if step.stage == stage
                ]
                for stage in ThinkingStage
            },
            "created_at": context.created_at.isoformat(),
            "completed_at": context.completed_at.isoformat() if context.completed_at else None,
            "duration": (context.completed_at - context.created_at).total_seconds() if context.completed_at else None
        }