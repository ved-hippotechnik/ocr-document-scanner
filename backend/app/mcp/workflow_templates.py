"""
Pre-built workflow templates for common OCR document processing tasks
"""
from typing import Dict, Any, List
from .orchestrator import MCPOrchestrator


class WorkflowTemplates:
    """Pre-built workflow templates"""
    
    def __init__(self, orchestrator: MCPOrchestrator):
        self.orchestrator = orchestrator
    
    def create_document_processing_workflow(self, 
                                          document_data: str,
                                          document_type_hint: str = None,
                                          user_id: str = None) -> str:
        """
        Create a comprehensive document processing workflow
        
        This workflow includes:
        1. Document classification
        2. Quality assessment
        3. Data extraction
        4. Validation
        5. Result storage
        """
        workflow_id = self.orchestrator.create_workflow(
            name="Document Processing Pipeline",
            description="Complete document processing from classification to storage"
        )
        
        # Step 1: Initialize thinking session
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="init_thinking",
            name="Initialize Processing Session",
            step_type="thinking.create_session",
            config={
                'goal': f"Process document for user {user_id}",
                'metadata': {
                    'user_id': user_id,
                    'document_type_hint': document_type_hint,
                    'process_type': 'full_processing'
                }
            }
        )
        
        # Step 2: Set initial context
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="set_initial_context",
            name="Set Initial Processing Context",
            step_type="context.set",
            dependencies=["init_thinking"],
            config={
                'layer': 'immediate',
                'key': 'processing_status',
                'value': 'started',
                'confidence': 1.0
            }
        )
        
        # Step 3: Document classification
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="classify_document",
            name="Classify Document Type",
            step_type="document.classify",
            dependencies=["set_initial_context"],
            config={
                'document_data': document_data,
                'type_hint': document_type_hint
            }
        )
        
        # Step 4: Record classification thinking
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="record_classification",
            name="Record Classification Result",
            step_type="thinking.add_step",
            dependencies=["classify_document"],
            config={
                'step_type': 'analysis',
                'content': 'Document classification completed',
                'confidence': 0.9
            }
        )
        
        # Step 5: Update context with classification
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="update_classification_context",
            name="Update Context with Classification",
            step_type="context.set",
            dependencies=["classify_document"],
            config={
                'layer': 'immediate',
                'key': 'document_type',
                'value': 'classified_type',  # This would be dynamically set
                'confidence': 0.95
            }
        )
        
        # Step 6: Extract document data
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="extract_data",
            name="Extract Document Data",
            step_type="document.extract",
            dependencies=["classify_document"],
            config={
                'document_data': document_data,
                'document_type': 'from_classification_step'
            }
        )
        
        # Step 7: Validate extracted data
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="validate_data",
            name="Validate Extracted Data",
            step_type="document.validate",
            dependencies=["extract_data"],
            config={
                'extracted_data': 'from_extraction_step',
                'validation_rules': 'default'
            }
        )
        
        # Step 8: Store results in memory
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="store_results",
            name="Store Processing Results",
            step_type="memory.store",
            dependencies=["validate_data"],
            config={
                'content': {
                    'processing_complete': True,
                    'workflow_id': workflow_id,
                    'user_id': user_id
                },
                'context': {
                    'workflow_type': 'document_processing',
                    'user_id': user_id
                },
                'tags': ['document_processing', 'completed', user_id or 'anonymous'],
                'importance': 0.8
            }
        )
        
        # Step 9: Final thinking conclusion
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="conclude_processing",
            name="Conclude Processing",
            step_type="thinking.add_step",
            dependencies=["store_results"],
            config={
                'step_type': 'conclusion',
                'content': 'Document processing workflow completed successfully',
                'confidence': 0.95
            }
        )
        
        # Step 10: Save workflow log
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="save_workflow_log",
            name="Save Workflow Log",
            step_type="filesystem.write",
            dependencies=["conclude_processing"],
            config={
                'filename': f'workflow_log_{workflow_id}.json',
                'content': f'{{"workflow_id": "{workflow_id}", "status": "completed"}}'
            }
        )
        
        return workflow_id
    
    def create_batch_processing_workflow(self,
                                       document_list: List[Dict[str, Any]],
                                       user_id: str = None) -> str:
        """
        Create a batch document processing workflow
        """
        workflow_id = self.orchestrator.create_workflow(
            name="Batch Document Processing",
            description=f"Process {len(document_list)} documents in batch"
        )
        
        # Step 1: Initialize batch processing
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="init_batch",
            name="Initialize Batch Processing",
            step_type="thinking.create_session",
            config={
                'goal': f"Process batch of {len(document_list)} documents",
                'metadata': {
                    'user_id': user_id,
                    'batch_size': len(document_list),
                    'process_type': 'batch_processing'
                }
            }
        )
        
        # Step 2: Set batch context
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="set_batch_context",
            name="Set Batch Context",
            step_type="context.set",
            dependencies=["init_batch"],
            config={
                'layer': 'session',
                'key': 'batch_status',
                'value': {
                    'total_documents': len(document_list),
                    'processed': 0,
                    'failed': 0
                },
                'confidence': 1.0
            }
        )
        
        # Step 3: Process documents in parallel
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="process_documents_parallel",
            name="Process Documents in Parallel",
            step_type="workflow.parallel",
            dependencies=["set_batch_context"],
            config={
                'sub_steps': [
                    {
                        'type': 'document.classify',
                        'document_data': doc.get('data'),
                        'document_id': doc.get('id')
                    }
                    for doc in document_list
                ]
            }
        )
        
        # Step 4: Collect and store batch results
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="collect_batch_results",
            name="Collect Batch Results",
            step_type="memory.store",
            dependencies=["process_documents_parallel"],
            config={
                'content': {
                    'batch_id': workflow_id,
                    'total_documents': len(document_list),
                    'user_id': user_id
                },
                'context': {
                    'workflow_type': 'batch_processing',
                    'user_id': user_id
                },
                'tags': ['batch_processing', 'completed', user_id or 'anonymous'],
                'importance': 0.9
            }
        )
        
        return workflow_id
    
    def create_quality_assessment_workflow(self,
                                         document_data: str,
                                         quality_threshold: float = 0.8) -> str:
        """
        Create a document quality assessment workflow
        """
        workflow_id = self.orchestrator.create_workflow(
            name="Document Quality Assessment",
            description="Assess document quality and provide recommendations"
        )
        
        # Step 1: Initialize quality assessment
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="init_quality_check",
            name="Initialize Quality Assessment",
            step_type="thinking.create_session",
            config={
                'goal': "Assess document quality and provide recommendations",
                'metadata': {
                    'quality_threshold': quality_threshold,
                    'process_type': 'quality_assessment'
                }
            }
        )
        
        # Step 2: Perform quality analysis
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="analyze_quality",
            name="Analyze Document Quality",
            step_type="document.validate",  # Reusing validation for quality check
            dependencies=["init_quality_check"],
            config={
                'document_data': document_data,
                'quality_threshold': quality_threshold,
                'check_type': 'quality_assessment'
            }
        )
        
        # Step 3: Conditional processing based on quality
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="quality_conditional",
            name="Quality-based Processing Decision",
            step_type="workflow.conditional",
            dependencies=["analyze_quality"],
            config={
                'condition': "workflow.context.get('quality_score', 0) >= 0.8"
            }
        )
        
        # Step 4: Store quality assessment results
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="store_quality_results",
            name="Store Quality Results",
            step_type="memory.store",
            dependencies=["quality_conditional"],
            config={
                'content': {
                    'quality_assessment_complete': True,
                    'workflow_id': workflow_id
                },
                'context': {
                    'workflow_type': 'quality_assessment'
                },
                'tags': ['quality_assessment', 'completed'],
                'importance': 0.7
            }
        )
        
        return workflow_id
    
    def create_error_recovery_workflow(self,
                                     failed_workflow_id: str,
                                     error_context: Dict[str, Any]) -> str:
        """
        Create an error recovery workflow for failed processing
        """
        workflow_id = self.orchestrator.create_workflow(
            name="Error Recovery Process",
            description=f"Recover from failed workflow {failed_workflow_id}"
        )
        
        # Step 1: Analyze failure
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="analyze_failure",
            name="Analyze Failure Cause",
            step_type="thinking.create_session",
            config={
                'goal': f"Analyze and recover from workflow failure",
                'metadata': {
                    'failed_workflow_id': failed_workflow_id,
                    'error_context': error_context,
                    'process_type': 'error_recovery'
                }
            }
        )
        
        # Step 2: Retrieve failure context from memory
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="retrieve_failure_context",
            name="Retrieve Failure Context",
            step_type="memory.search",
            dependencies=["analyze_failure"],
            config={
                'tags': ['workflow', failed_workflow_id, 'error'],
                'limit': 5
            }
        )
        
        # Step 3: Determine recovery strategy
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="determine_recovery",
            name="Determine Recovery Strategy",
            step_type="thinking.add_step",
            dependencies=["retrieve_failure_context"],
            config={
                'step_type': 'analysis',
                'content': 'Analyzing failure patterns and determining recovery approach',
                'confidence': 0.8
            }
        )
        
        # Step 4: Execute recovery actions
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="execute_recovery",
            name="Execute Recovery Actions",
            step_type="workflow.conditional",
            dependencies=["determine_recovery"],
            config={
                'condition': "True"  # Always execute for now
            }
        )
        
        # Step 5: Store recovery results
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="store_recovery_results",
            name="Store Recovery Results",
            step_type="memory.store",
            dependencies=["execute_recovery"],
            config={
                'content': {
                    'recovery_complete': True,
                    'original_workflow_id': failed_workflow_id,
                    'recovery_workflow_id': workflow_id
                },
                'context': {
                    'workflow_type': 'error_recovery',
                    'original_workflow': failed_workflow_id
                },
                'tags': ['error_recovery', 'completed', failed_workflow_id],
                'importance': 0.9
            }
        )
        
        return workflow_id
    
    def create_monitoring_workflow(self, 
                                 target_workflow_id: str,
                                 check_interval: int = 30) -> str:
        """
        Create a monitoring workflow for another workflow
        """
        workflow_id = self.orchestrator.create_workflow(
            name="Workflow Monitoring",
            description=f"Monitor progress of workflow {target_workflow_id}"
        )
        
        # Step 1: Initialize monitoring
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="init_monitoring",
            name="Initialize Monitoring",
            step_type="thinking.create_session",
            config={
                'goal': f"Monitor workflow {target_workflow_id}",
                'metadata': {
                    'target_workflow_id': target_workflow_id,
                    'check_interval': check_interval,
                    'process_type': 'monitoring'
                }
            }
        )
        
        # Step 2: Set monitoring context
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="set_monitoring_context",
            name="Set Monitoring Context",
            step_type="context.set",
            dependencies=["init_monitoring"],
            config={
                'layer': 'session',
                'key': 'monitoring_target',
                'value': target_workflow_id,
                'confidence': 1.0
            }
        )
        
        # Step 3: Delay before first check
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="initial_delay",
            name="Initial Monitoring Delay",
            step_type="workflow.delay",
            dependencies=["set_monitoring_context"],
            config={
                'delay_seconds': check_interval
            }
        )
        
        # Step 4: Check target workflow status
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="check_target_status",
            name="Check Target Workflow Status",
            step_type="memory.search",
            dependencies=["initial_delay"],
            config={
                'tags': ['workflow', target_workflow_id],
                'limit': 1
            }
        )
        
        # Step 5: Store monitoring result
        self.orchestrator.add_workflow_step(
            workflow_id=workflow_id,
            step_id="store_monitoring_result",
            name="Store Monitoring Result",
            step_type="memory.store",
            dependencies=["check_target_status"],
            config={
                'content': {
                    'monitoring_complete': True,
                    'target_workflow_id': target_workflow_id,
                    'monitor_workflow_id': workflow_id
                },
                'context': {
                    'workflow_type': 'monitoring',
                    'target_workflow': target_workflow_id
                },
                'tags': ['monitoring', 'completed', target_workflow_id],
                'importance': 0.6
            }
        )
        
        return workflow_id


# Helper function to create template instances
def create_workflow_templates(orchestrator: MCPOrchestrator) -> WorkflowTemplates:
    """Create workflow templates instance"""
    return WorkflowTemplates(orchestrator)