"""
Comprehensive tests for MCP (Model Context Protocol) servers
"""
import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open

from app.mcp.sequential_thinking import SequentialThinkingMCP
from app.mcp.memory import MemoryMCP
from app.mcp.context7 import Context7MCP, ContextLayer
from app.mcp.filesystem import FilesystemMCP


class TestSequentialThinkingMCP:
    """Test Sequential Thinking MCP server"""
    
    @pytest.fixture
    def thinking_mcp(self):
        return SequentialThinkingMCP()
    
    def test_create_context(self, thinking_mcp):
        """Test creating a thinking context"""
        session_id = thinking_mcp.create_context(
            goal="Process document analysis",
            metadata={"document_type": "aadhaar_card"}
        )
        
        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        
        # Verify context was stored
        assert session_id in thinking_mcp.contexts
        context = thinking_mcp.contexts[session_id]
        assert context['goal'] == "Process document analysis"
        assert context['metadata']['document_type'] == "aadhaar_card"
    
    def test_add_step(self, thinking_mcp):
        """Test adding steps to thinking process"""
        session_id = thinking_mcp.create_context("Test goal")
        
        # Add first step
        result = thinking_mcp.add_step(
            session_id=session_id,
            step_type="observation",
            content="Document appears to be an Aadhaar card",
            confidence=0.9
        )
        
        assert result is True
        context = thinking_mcp.contexts[session_id]
        assert len(context['steps']) == 1
        
        step = context['steps'][0]
        assert step['type'] == "observation"
        assert step['content'] == "Document appears to be an Aadhaar card"
        assert step['confidence'] == 0.9
        assert 'timestamp' in step
    
    def test_get_context(self, thinking_mcp):
        """Test retrieving thinking context"""
        session_id = thinking_mcp.create_context("Test goal")
        thinking_mcp.add_step(session_id, "analysis", "Testing step", 0.8)
        
        context = thinking_mcp.get_context(session_id)
        
        assert context is not None
        assert context['goal'] == "Test goal"
        assert len(context['steps']) == 1
    
    def test_process_thinking_chain(self, thinking_mcp):
        """Test complete thinking chain processing"""
        session_id = thinking_mcp.create_context(
            "Analyze document for data extraction",
            {"document_type": "unknown"}
        )
        
        # Simulate thinking chain
        steps = [
            ("observation", "Document contains Hindi and English text", 0.9),
            ("hypothesis", "This appears to be an Indian government document", 0.8),
            ("analysis", "Text patterns match Aadhaar card format", 0.85),
            ("conclusion", "Document classified as Aadhaar card", 0.95)
        ]
        
        for step_type, content, confidence in steps:
            thinking_mcp.add_step(session_id, step_type, content, confidence)
        
        # Get final context
        context = thinking_mcp.get_context(session_id)
        assert len(context['steps']) == 4
        
        # Verify step types
        step_types = [step['type'] for step in context['steps']]
        assert step_types == ["observation", "hypothesis", "analysis", "conclusion"]
    
    def test_invalid_session_handling(self, thinking_mcp):
        """Test handling of invalid session IDs"""
        # Try to add step to non-existent session
        result = thinking_mcp.add_step("invalid-session", "test", "content", 0.5)
        assert result is False
        
        # Try to get non-existent context
        context = thinking_mcp.get_context("invalid-session")
        assert context is None


class TestMemoryMCP:
    """Test Memory MCP server"""
    
    @pytest.fixture
    def memory_mcp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mcp = MemoryMCP(storage_path=os.path.join(temp_dir, "memory.pkl"))
            yield mcp
    
    def test_store_memory(self, memory_mcp):
        """Test storing memories"""
        memory_id = memory_mcp.store_memory(
            content={"processed_document": "aadhaar_card", "confidence": 0.95},
            context={"user_id": "test-user", "session": "test-session"},
            tags=["document", "classification", "aadhaar"],
            importance=0.9
        )
        
        assert memory_id is not None
        assert isinstance(memory_id, str)
        
        # Verify memory was stored
        assert memory_id in memory_mcp.memories
        memory = memory_mcp.memories[memory_id]
        assert memory['content']['processed_document'] == "aadhaar_card"
        assert memory['importance'] == 0.9
        assert "document" in memory['tags']
    
    def test_retrieve_memory(self, memory_mcp):
        """Test retrieving memories"""
        # Store test memory
        memory_id = memory_mcp.store_memory(
            content={"test": "data"},
            tags=["test"]
        )
        
        # Retrieve by ID
        memory = memory_mcp.retrieve_memory(memory_id)
        assert memory is not None
        assert memory['id'] == memory_id
        assert memory['content']['test'] == "data"
    
    def test_search_memories(self, memory_mcp):
        """Test searching memories"""
        # Store multiple memories
        memory_ids = []
        
        memory_ids.append(memory_mcp.store_memory(
            content={"document_type": "aadhaar_card"},
            tags=["aadhaar", "indian", "document"],
            importance=0.8
        ))
        
        memory_ids.append(memory_mcp.store_memory(
            content={"document_type": "passport"},
            tags=["passport", "travel", "document"],
            importance=0.7
        ))
        
        memory_ids.append(memory_mcp.store_memory(
            content={"processing_result": "success"},
            tags=["result", "processing"],
            importance=0.6
        ))
        
        # Search by tags
        results = memory_mcp.search_memories(tags=["document"])
        assert len(results) == 2
        
        results = memory_mcp.search_memories(tags=["aadhaar"])
        assert len(results) == 1
        assert results[0]['content']['document_type'] == "aadhaar_card"
        
        # Search by importance
        results = memory_mcp.search_memories(min_importance=0.75)
        assert len(results) == 2
    
    def test_memory_persistence(self, memory_mcp):
        """Test memory persistence to disk"""
        # Store memory
        memory_id = memory_mcp.store_memory(
            content={"persistent": "data"},
            tags=["test"]
        )
        
        # Save to disk
        memory_mcp.save_to_disk()
        
        # Create new instance and load
        new_mcp = MemoryMCP(storage_path=memory_mcp.storage_path)
        new_mcp.load_from_disk()
        
        # Verify memory was loaded
        assert memory_id in new_mcp.memories
        memory = new_mcp.retrieve_memory(memory_id)
        assert memory['content']['persistent'] == "data"
    
    def test_memory_cleanup(self, memory_mcp):
        """Test memory cleanup based on age and importance"""
        import time
        
        # Store memories with different importance
        low_importance_id = memory_mcp.store_memory(
            content={"test": "low"},
            importance=0.1
        )
        
        high_importance_id = memory_mcp.store_memory(
            content={"test": "high"},
            importance=0.9
        )
        
        # Simulate time passing
        memory_mcp.memories[low_importance_id]['timestamp'] -= 86400  # 1 day ago
        
        # Cleanup memories
        initial_count = len(memory_mcp.memories)
        memory_mcp.cleanup_memories(max_age_hours=12, min_importance=0.5)
        
        # Low importance, old memory should be removed
        assert len(memory_mcp.memories) < initial_count
        assert low_importance_id not in memory_mcp.memories
        assert high_importance_id in memory_mcp.memories


class TestContext7MCP:
    """Test Context7 MCP server"""
    
    @pytest.fixture
    def context7_mcp(self):
        return Context7MCP()
    
    def test_context_layers(self, context7_mcp):
        """Test different context layers"""
        context_id = "test-context"
        
        # Test each layer type
        layers_data = [
            (ContextLayer.IMMEDIATE, "current_document", "aadhaar_card"),
            (ContextLayer.SESSION, "user_preferences", {"language": "en"}),
            (ContextLayer.HISTORICAL, "processing_stats", {"total_processed": 100}),
            (ContextLayer.DOMAIN, "document_types", ["aadhaar", "passport", "dl"]),
            (ContextLayer.BEHAVIORAL, "user_patterns", {"avg_processing_time": 2.5}),
            (ContextLayer.ENVIRONMENTAL, "system_load", 0.7),
            (ContextLayer.GLOBAL, "service_config", {"version": "2.0"})
        ]
        
        # Set values in each layer
        for layer, key, value in layers_data:
            result = context7_mcp.set_context(
                context_id=context_id,
                layer=layer,
                key=key,
                value=value,
                confidence=0.9
            )
            assert result is True
        
        # Retrieve values from each layer
        for layer, key, expected_value in layers_data:
            value = context7_mcp.get_context(context_id, layer, key)
            assert value == expected_value
    
    def test_context_inheritance(self, context7_mcp):
        """Test context inheritance between layers"""
        context_id = "inheritance-test"
        
        # Set global context
        context7_mcp.set_context(
            context_id, ContextLayer.GLOBAL, "default_confidence", 0.8
        )
        
        # Set domain-specific override
        context7_mcp.set_context(
            context_id, ContextLayer.DOMAIN, "default_confidence", 0.9
        )
        
        # Get context should return domain-specific value (higher priority)
        value = context7_mcp.get_context(context_id, ContextLayer.DOMAIN, "default_confidence")
        assert value == 0.9
        
        # Global value should still exist
        global_value = context7_mcp.get_context(context_id, ContextLayer.GLOBAL, "default_confidence")
        assert global_value == 0.8
    
    def test_context_history(self, context7_mcp):
        """Test context history tracking"""
        context_id = "history-test"
        key = "processing_confidence"
        
        # Set multiple values over time
        values = [0.7, 0.8, 0.85, 0.9]
        for value in values:
            context7_mcp.set_context(
                context_id, ContextLayer.SESSION, key, value, source="test"
            )
        
        # Get history
        history = context7_mcp.get_context_history(context_id, ContextLayer.SESSION, key)
        assert len(history) == len(values)
        
        # Verify values are in chronological order
        for i, entry in enumerate(history):
            assert entry['value'] == values[i]
            assert 'timestamp' in entry
            assert entry['source'] == "test"
    
    def test_context_query(self, context7_mcp):
        """Test complex context queries"""
        context_id = "query-test"
        
        # Set up test data
        context7_mcp.set_context(context_id, ContextLayer.IMMEDIATE, "document_type", "aadhaar_card")
        context7_mcp.set_context(context_id, ContextLayer.IMMEDIATE, "confidence", 0.95)
        context7_mcp.set_context(context_id, ContextLayer.SESSION, "user_id", "test-user")
        context7_mcp.set_context(context_id, ContextLayer.SESSION, "processed_count", 5)
        
        # Query specific layer
        immediate_context = context7_mcp.get_layer_context(context_id, ContextLayer.IMMEDIATE)
        assert immediate_context['document_type'] == "aadhaar_card"
        assert immediate_context['confidence'] == 0.95
        
        # Query all layers
        all_context = context7_mcp.get_full_context(context_id)
        assert ContextLayer.IMMEDIATE.value in all_context
        assert ContextLayer.SESSION.value in all_context
        assert all_context[ContextLayer.IMMEDIATE.value]['document_type'] == "aadhaar_card"
    
    def test_context_cleanup(self, context7_mcp):
        """Test context cleanup and management"""
        # Create multiple contexts
        context_ids = ["ctx1", "ctx2", "ctx3"]
        for ctx_id in context_ids:
            context7_mcp.set_context(ctx_id, ContextLayer.SESSION, "test", "data")
        
        # Verify contexts exist
        for ctx_id in context_ids:
            assert ctx_id in context7_mcp.contexts
        
        # Clear specific context
        context7_mcp.clear_context("ctx1")
        assert "ctx1" not in context7_mcp.contexts
        assert "ctx2" in context7_mcp.contexts
        
        # Clear all contexts
        context7_mcp.clear_all_contexts()
        assert len(context7_mcp.contexts) == 0


class TestFilesystemMCP:
    """Test Filesystem MCP server"""
    
    @pytest.fixture
    def filesystem_mcp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            mcp = FilesystemMCP(base_path=temp_dir)
            yield mcp
    
    def test_write_file(self, filesystem_mcp):
        """Test writing files"""
        content = "Test file content"
        result = filesystem_mcp.write_file("test.txt", content)
        
        assert result is True
        
        # Verify file exists
        file_path = os.path.join(filesystem_mcp.base_path, "test.txt")
        assert os.path.exists(file_path)
        
        # Verify content
        with open(file_path, 'r') as f:
            assert f.read() == content
    
    def test_read_file(self, filesystem_mcp):
        """Test reading files"""
        # Write test file
        content = "Test content for reading"
        filesystem_mcp.write_file("read_test.txt", content)
        
        # Read file
        read_content = filesystem_mcp.read_file("read_test.txt")
        assert read_content == content
    
    def test_list_files(self, filesystem_mcp):
        """Test listing files"""
        # Create test files
        test_files = ["file1.txt", "file2.json", "file3.py"]
        for filename in test_files:
            filesystem_mcp.write_file(filename, f"Content of {filename}")
        
        # List files
        files = filesystem_mcp.list_files()
        assert len(files) >= len(test_files)
        
        for filename in test_files:
            assert filename in files
    
    def test_delete_file(self, filesystem_mcp):
        """Test deleting files"""
        # Create test file
        filesystem_mcp.write_file("delete_test.txt", "To be deleted")
        
        # Verify file exists
        assert "delete_test.txt" in filesystem_mcp.list_files()
        
        # Delete file
        result = filesystem_mcp.delete_file("delete_test.txt")
        assert result is True
        
        # Verify file is gone
        assert "delete_test.txt" not in filesystem_mcp.list_files()
    
    def test_create_directory(self, filesystem_mcp):
        """Test creating directories"""
        result = filesystem_mcp.create_directory("test_dir")
        assert result is True
        
        # Verify directory exists
        dir_path = os.path.join(filesystem_mcp.base_path, "test_dir")
        assert os.path.isdir(dir_path)
    
    def test_file_security(self, filesystem_mcp):
        """Test file access security"""
        # Try to access file outside base path
        result = filesystem_mcp.write_file("../outside.txt", "malicious content")
        assert result is False
        
        # Try to read file outside base path
        content = filesystem_mcp.read_file("../outside.txt")
        assert content is None
        
        # Try absolute path outside base
        result = filesystem_mcp.write_file("/tmp/malicious.txt", "content")
        assert result is False
    
    def test_binary_file_handling(self, filesystem_mcp):
        """Test handling binary files"""
        # Create binary content
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00'
        
        result = filesystem_mcp.write_binary_file("test.png", binary_content)
        assert result is True
        
        # Read binary file
        read_content = filesystem_mcp.read_binary_file("test.png")
        assert read_content == binary_content


class TestMCPIntegration:
    """Integration tests for MCP servers"""
    
    @pytest.mark.integration
    def test_document_processing_workflow(self):
        """Test complete document processing workflow using MCP servers"""
        # Initialize MCP servers
        thinking_mcp = SequentialThinkingMCP()
        memory_mcp = MemoryMCP()
        context7_mcp = Context7MCP()
        
        # Simulate document processing workflow
        
        # 1. Start thinking process
        session_id = thinking_mcp.create_context(
            "Analyze and process uploaded document",
            {"user_id": "test-user", "timestamp": "2024-01-01T10:00:00Z"}
        )
        
        # 2. Set immediate context
        context7_mcp.set_context(
            "doc-processing", ContextLayer.IMMEDIATE, 
            "document_received", True, confidence=1.0
        )
        
        # 3. Thinking: Initial observation
        thinking_mcp.add_step(
            session_id, "observation", 
            "Document image received, analyzing content", 0.9
        )
        
        # 4. Update context with preliminary findings
        context7_mcp.set_context(
            "doc-processing", ContextLayer.IMMEDIATE,
            "preliminary_type", "indian_document", confidence=0.7
        )
        
        # 5. Thinking: Hypothesis formation
        thinking_mcp.add_step(
            session_id, "hypothesis",
            "Text patterns suggest this is an Aadhaar card", 0.8
        )
        
        # 6. Store intermediate result in memory
        memory_mcp.store_memory(
            content={"classification_attempt": "aadhaar_card", "confidence": 0.8},
            context={"session_id": session_id, "step": "classification"},
            tags=["classification", "intermediate", "aadhaar"],
            importance=0.6
        )
        
        # 7. Final analysis and conclusion
        thinking_mcp.add_step(
            session_id, "analysis",
            "Aadhaar number pattern detected: 1234 5678 9012", 0.95
        )
        
        thinking_mcp.add_step(
            session_id, "conclusion",
            "Document confirmed as Aadhaar card with high confidence", 0.95
        )
        
        # 8. Update final context
        context7_mcp.set_context(
            "doc-processing", ContextLayer.IMMEDIATE,
            "final_classification", "aadhaar_card", confidence=0.95
        )
        
        # 9. Store final result in memory
        final_memory_id = memory_mcp.store_memory(
            content={
                "document_type": "aadhaar_card",
                "extracted_data": {
                    "name": "RAJESH KUMAR",
                    "aadhaar_number": "1234 5678 9012"
                },
                "confidence": 0.95
            },
            context={"session_id": session_id, "user_id": "test-user"},
            tags=["final_result", "aadhaar", "extraction"],
            importance=0.9
        )
        
        # Verify workflow results
        
        # Check thinking process
        final_context = thinking_mcp.get_context(session_id)
        assert len(final_context['steps']) == 4
        assert final_context['steps'][-1]['type'] == "conclusion"
        
        # Check context layers
        final_type = context7_mcp.get_context(
            "doc-processing", ContextLayer.IMMEDIATE, "final_classification"
        )
        assert final_type == "aadhaar_card"
        
        # Check memory storage
        final_memory = memory_mcp.retrieve_memory(final_memory_id)
        assert final_memory['content']['document_type'] == "aadhaar_card"
        assert final_memory['content']['confidence'] == 0.95
        
        # Search memories by tag
        aadhaar_memories = memory_mcp.search_memories(tags=["aadhaar"])
        assert len(aadhaar_memories) == 2  # intermediate + final
    
    @pytest.mark.performance
    def test_mcp_performance(self, performance_tracker):
        """Test MCP server performance under load"""
        thinking_mcp = SequentialThinkingMCP()
        memory_mcp = MemoryMCP()
        context7_mcp = Context7MCP()
        
        performance_tracker.start_timer('mcp_bulk_operations')
        
        # Perform bulk operations
        session_ids = []
        memory_ids = []
        
        for i in range(100):
            # Create thinking contexts
            session_id = thinking_mcp.create_context(f"Test goal {i}")
            session_ids.append(session_id)
            
            # Add steps
            thinking_mcp.add_step(session_id, "test", f"Step {i}", 0.8)
            
            # Store memories
            memory_id = memory_mcp.store_memory(
                content={"test": i},
                tags=[f"tag_{i}", "bulk_test"]
            )
            memory_ids.append(memory_id)
            
            # Set context
            context7_mcp.set_context(
                f"ctx_{i}", ContextLayer.SESSION, "test_value", i
            )
        
        performance_tracker.end_timer('mcp_bulk_operations')
        
        # Should complete 100 operations per server in reasonable time
        assert performance_tracker.get_duration('mcp_bulk_operations') < 5.0
        
        # Verify all operations completed
        assert len(session_ids) == 100
        assert len(memory_ids) == 100
        
        # Test bulk retrieval
        performance_tracker.start_timer('mcp_bulk_retrieval')
        
        for i in range(100):
            thinking_mcp.get_context(session_ids[i])
            memory_mcp.retrieve_memory(memory_ids[i])
            context7_mcp.get_context(f"ctx_{i}", ContextLayer.SESSION, "test_value")
        
        performance_tracker.end_timer('mcp_bulk_retrieval')
        
        # Bulk retrieval should be fast
        assert performance_tracker.get_duration('mcp_bulk_retrieval') < 2.0