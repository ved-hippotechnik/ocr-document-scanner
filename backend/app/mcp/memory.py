"""
Memory MCP Server

Provides context and conversation memory management for document processing.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import pickle
import os

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry"""
    memory_id: str
    content: Any
    context: Dict[str, Any]
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    ttl: Optional[int] = None  # Time to live in seconds
    importance: float = 1.0  # 0.0 to 1.0


@dataclass
class ConversationTurn:
    """A turn in a conversation"""
    turn_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationMemory:
    """Memory of a conversation"""
    conversation_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: Optional[datetime] = None
    summary: Optional[str] = None


class MemoryMCP:
    """
    Memory MCP Server
    
    Provides memory management for document processing contexts and conversations.
    """
    
    def __init__(self, max_memory_size: int = 10000, persistence_path: Optional[str] = None):
        self.max_memory_size = max_memory_size
        self.persistence_path = persistence_path
        
        # Different memory stores
        self.short_term_memory: deque = deque(maxlen=1000)
        self.long_term_memory: Dict[str, MemoryEntry] = {}
        self.conversations: Dict[str, ConversationMemory] = {}
        self.semantic_index: Dict[str, List[str]] = defaultdict(list)  # tag -> memory_ids
        
        # Memory statistics
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.memory_scores: Dict[str, float] = {}
        
        # Load persisted memory if available
        if persistence_path and os.path.exists(persistence_path):
            self._load_memory()
        
        logger.info(f"MemoryMCP initialized with max size: {max_memory_size}")
    
    def store_memory(self, content: Any, context: Dict[str, Any], 
                    tags: Optional[List[str]] = None, 
                    ttl: Optional[int] = None,
                    importance: float = 1.0) -> str:
        """Store a new memory"""
        import uuid
        memory_id = str(uuid.uuid4())
        
        memory = MemoryEntry(
            memory_id=memory_id,
            content=content,
            context=context,
            timestamp=datetime.now(),
            tags=tags or [],
            ttl=ttl,
            importance=importance
        )
        
        # Add to appropriate store based on importance
        if importance >= 0.7:
            self.long_term_memory[memory_id] = memory
        else:
            self.short_term_memory.append(memory)
        
        # Update semantic index
        for tag in memory.tags:
            self.semantic_index[tag].append(memory_id)
        
        # Calculate initial memory score
        self._update_memory_score(memory_id, importance)
        
        logger.debug(f"Stored memory {memory_id} with tags: {tags}")
        
        # Cleanup old memories if needed
        self._cleanup_memory()
        
        return memory_id
    
    def retrieve_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory"""
        memory = None
        
        # Check long-term memory
        if memory_id in self.long_term_memory:
            memory = self.long_term_memory[memory_id]
        else:
            # Check short-term memory
            for mem in self.short_term_memory:
                if mem.memory_id == memory_id:
                    memory = mem
                    break
        
        if memory:
            # Update access statistics
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            self.access_patterns[memory_id].append(datetime.now())
            
            # Update memory score based on access
            self._update_memory_score(memory_id, memory.importance, access_boost=0.1)
            
            # Check if should promote to long-term memory
            if memory in self.short_term_memory and memory.access_count >= 3:
                self._promote_to_long_term(memory)
            
            logger.debug(f"Retrieved memory {memory_id}")
            return memory
        
        return None
    
    def search_memories(self, query: Optional[str] = None, 
                       tags: Optional[List[str]] = None,
                       context_filter: Optional[Dict[str, Any]] = None,
                       limit: int = 10) -> List[MemoryEntry]:
        """Search memories based on criteria"""
        results = []
        
        # Collect all memories
        all_memories = list(self.long_term_memory.values())
        all_memories.extend(self.short_term_memory)
        
        # Filter by tags
        if tags:
            tagged_memory_ids = set()
            for tag in tags:
                tagged_memory_ids.update(self.semantic_index.get(tag, []))
            
            all_memories = [m for m in all_memories if m.memory_id in tagged_memory_ids]
        
        # Filter by context
        if context_filter:
            filtered = []
            for memory in all_memories:
                match = True
                for key, value in context_filter.items():
                    if key not in memory.context or memory.context[key] != value:
                        match = False
                        break
                if match:
                    filtered.append(memory)
            all_memories = filtered
        
        # Search in content if query provided
        if query:
            query_lower = query.lower()
            scored_memories = []
            
            for memory in all_memories:
                score = 0
                
                # Check content
                content_str = str(memory.content).lower()
                if query_lower in content_str:
                    score += 1.0
                
                # Check tags
                for tag in memory.tags:
                    if query_lower in tag.lower():
                        score += 0.5
                
                # Check context
                context_str = json.dumps(memory.context).lower()
                if query_lower in context_str:
                    score += 0.3
                
                if score > 0:
                    scored_memories.append((score * memory.importance, memory))
            
            # Sort by score
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            results = [mem for _, mem in scored_memories[:limit]]
        else:
            # Sort by importance and recency
            all_memories.sort(
                key=lambda m: (m.importance, m.timestamp),
                reverse=True
            )
            results = all_memories[:limit]
        
        logger.info(f"Memory search returned {len(results)} results")
        return results
    
    def create_conversation(self, initial_context: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation"""
        import uuid
        conversation_id = str(uuid.uuid4())
        
        conversation = ConversationMemory(
            conversation_id=conversation_id,
            context=initial_context or {}
        )
        
        self.conversations[conversation_id] = conversation
        logger.info(f"Created conversation {conversation_id}")
        
        return conversation_id
    
    def add_conversation_turn(self, conversation_id: str, role: str, 
                            content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a turn to a conversation"""
        if conversation_id not in self.conversations:
            logger.error(f"Conversation {conversation_id} not found")
            return False
        
        import uuid
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        conversation = self.conversations[conversation_id]
        conversation.turns.append(turn)
        conversation.last_updated = datetime.now()
        
        # Update conversation summary if needed
        if len(conversation.turns) % 10 == 0:
            self._update_conversation_summary(conversation)
        
        # Store important turns as memories
        if metadata and metadata.get("important", False):
            self.store_memory(
                content=content,
                context={
                    "conversation_id": conversation_id,
                    "role": role,
                    "turn_number": len(conversation.turns)
                },
                tags=["conversation", f"conv_{conversation_id}", role],
                importance=0.8
            )
        
        logger.debug(f"Added turn to conversation {conversation_id}")
        return True
    
    def get_conversation_context(self, conversation_id: str, 
                                max_turns: int = 10) -> Optional[Dict[str, Any]]:
        """Get conversation context with recent turns"""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        recent_turns = conversation.turns[-max_turns:] if conversation.turns else []
        
        return {
            "conversation_id": conversation_id,
            "context": conversation.context,
            "summary": conversation.summary,
            "recent_turns": [
                {
                    "role": turn.role,
                    "content": turn.content,
                    "timestamp": turn.timestamp.isoformat(),
                    "metadata": turn.metadata
                }
                for turn in recent_turns
            ],
            "total_turns": len(conversation.turns),
            "created_at": conversation.created_at.isoformat(),
            "last_updated": conversation.last_updated.isoformat() if conversation.last_updated else None
        }
    
    def forget_memory(self, memory_id: str) -> bool:
        """Remove a memory"""
        removed = False
        
        # Remove from long-term memory
        if memory_id in self.long_term_memory:
            memory = self.long_term_memory[memory_id]
            del self.long_term_memory[memory_id]
            removed = True
        else:
            # Remove from short-term memory
            for i, mem in enumerate(self.short_term_memory):
                if mem.memory_id == memory_id:
                    memory = mem
                    del self.short_term_memory[i]
                    removed = True
                    break
        
        if removed:
            # Update semantic index
            for tag in memory.tags:
                if tag in self.semantic_index and memory_id in self.semantic_index[tag]:
                    self.semantic_index[tag].remove(memory_id)
            
            # Remove from statistics
            if memory_id in self.access_patterns:
                del self.access_patterns[memory_id]
            if memory_id in self.memory_scores:
                del self.memory_scores[memory_id]
            
            logger.info(f"Forgot memory {memory_id}")
        
        return removed
    
    def _promote_to_long_term(self, memory: MemoryEntry):
        """Promote a memory from short-term to long-term storage"""
        self.long_term_memory[memory.memory_id] = memory
        logger.debug(f"Promoted memory {memory.memory_id} to long-term storage")
    
    def _update_memory_score(self, memory_id: str, base_importance: float, 
                           access_boost: float = 0.0):
        """Update the score of a memory based on various factors"""
        # Calculate recency factor
        memory = self.retrieve_memory(memory_id)
        if not memory:
            return
        
        age = (datetime.now() - memory.timestamp).total_seconds() / 86400  # Days
        recency_factor = 1.0 / (1.0 + age * 0.1)  # Decay over time
        
        # Calculate access frequency factor
        access_factor = min(1.0, memory.access_count * 0.1)
        
        # Combined score
        score = (base_importance * 0.5 + 
                recency_factor * 0.3 + 
                access_factor * 0.2 + 
                access_boost)
        
        self.memory_scores[memory_id] = min(1.0, score)
    
    def _update_conversation_summary(self, conversation: ConversationMemory):
        """Generate a summary of the conversation"""
        # Simple summary: extract key points from recent turns
        recent_turns = conversation.turns[-20:]
        
        key_points = []
        for turn in recent_turns:
            if turn.role == "user":
                # Extract questions or requests
                if "?" in turn.content or any(word in turn.content.lower() 
                                             for word in ["please", "can you", "help"]):
                    key_points.append(f"User asked: {turn.content[:100]}...")
            elif turn.role == "assistant":
                # Extract actions or conclusions
                if any(word in turn.content.lower() 
                      for word in ["processed", "completed", "found", "created"]):
                    key_points.append(f"Assistant: {turn.content[:100]}...")
        
        conversation.summary = " | ".join(key_points[-5:])  # Last 5 key points
    
    def _cleanup_memory(self):
        """Remove old or expired memories"""
        now = datetime.now()
        
        # Check TTL in long-term memory
        expired_ids = []
        for memory_id, memory in self.long_term_memory.items():
            if memory.ttl and (now - memory.timestamp).total_seconds() > memory.ttl:
                expired_ids.append(memory_id)
        
        for memory_id in expired_ids:
            self.forget_memory(memory_id)
        
        # Remove least important memories if over limit
        if len(self.long_term_memory) > self.max_memory_size * 0.8:
            # Sort by score
            scored_memories = [
                (self.memory_scores.get(mid, 0), mid) 
                for mid in self.long_term_memory.keys()
            ]
            scored_memories.sort()
            
            # Remove bottom 20%
            to_remove = int(len(scored_memories) * 0.2)
            for _, memory_id in scored_memories[:to_remove]:
                self.forget_memory(memory_id)
        
        logger.debug(f"Cleaned up {len(expired_ids)} expired memories")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        total_memories = len(self.long_term_memory) + len(self.short_term_memory)
        
        tag_distribution = {}
        for tag, memory_ids in self.semantic_index.items():
            tag_distribution[tag] = len(memory_ids)
        
        # Calculate average access patterns
        total_accesses = sum(len(accesses) for accesses in self.access_patterns.values())
        
        return {
            "total_memories": total_memories,
            "long_term_count": len(self.long_term_memory),
            "short_term_count": len(self.short_term_memory),
            "conversation_count": len(self.conversations),
            "tag_distribution": tag_distribution,
            "total_accesses": total_accesses,
            "average_importance": sum(self.memory_scores.values()) / len(self.memory_scores) if self.memory_scores else 0,
            "memory_usage_percentage": (total_memories / self.max_memory_size) * 100
        }
    
    def save_memory(self):
        """Persist memory to disk"""
        if not self.persistence_path:
            return
        
        try:
            data = {
                "long_term_memory": self.long_term_memory,
                "short_term_memory": list(self.short_term_memory),
                "conversations": self.conversations,
                "semantic_index": dict(self.semantic_index),
                "memory_scores": self.memory_scores
            }
            
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            with open(self.persistence_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Saved memory to {self.persistence_path}")
            
        except Exception as e:
            logger.error(f"Failed to save memory: {str(e)}")
    
    def _load_memory(self):
        """Load memory from disk"""
        try:
            with open(self.persistence_path, 'rb') as f:
                data = pickle.load(f)
            
            self.long_term_memory = data.get("long_term_memory", {})
            self.short_term_memory = deque(data.get("short_term_memory", []), maxlen=1000)
            self.conversations = data.get("conversations", {})
            self.semantic_index = defaultdict(list, data.get("semantic_index", {}))
            self.memory_scores = data.get("memory_scores", {})
            
            logger.info(f"Loaded memory from {self.persistence_path}")
            
        except Exception as e:
            logger.error(f"Failed to load memory: {str(e)}")