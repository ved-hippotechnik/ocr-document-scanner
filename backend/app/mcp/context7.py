"""
Context7 MCP Server

Advanced context management with 7 layers of contextual understanding for document processing.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class ContextLayer(Enum):
    """The 7 layers of context"""
    IMMEDIATE = "immediate"      # Current task/document
    SESSION = "session"          # Current processing session
    HISTORICAL = "historical"    # Past interactions/documents
    DOMAIN = "domain"           # Domain-specific knowledge
    BEHAVIORAL = "behavioral"    # User behavior patterns
    ENVIRONMENTAL = "environmental"  # System/environment state
    GLOBAL = "global"           # Global settings/preferences


@dataclass
class ContextEntry:
    """An entry in a context layer"""
    key: str
    value: Any
    layer: ContextLayer
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextState:
    """Current state of all context layers"""
    layers: Dict[ContextLayer, Dict[str, ContextEntry]] = field(default_factory=lambda: {
        layer: {} for layer in ContextLayer
    })
    relationships: List[Tuple[str, str, str]] = field(default_factory=list)  # (from_key, to_key, relation_type)
    version: int = 1
    last_updated: datetime = field(default_factory=datetime.now)


class Context7MCP:
    """
    Context7 MCP Server
    
    Provides advanced 7-layer context management for intelligent document processing.
    """
    
    def __init__(self):
        self.context_states: Dict[str, ContextState] = {}
        self.layer_weights = {
            ContextLayer.IMMEDIATE: 1.0,
            ContextLayer.SESSION: 0.8,
            ContextLayer.HISTORICAL: 0.6,
            ContextLayer.DOMAIN: 0.7,
            ContextLayer.BEHAVIORAL: 0.5,
            ContextLayer.ENVIRONMENTAL: 0.4,
            ContextLayer.GLOBAL: 0.3
        }
        
        # Context processing strategies
        self.layer_processors = {
            ContextLayer.IMMEDIATE: self._process_immediate_context,
            ContextLayer.SESSION: self._process_session_context,
            ContextLayer.HISTORICAL: self._process_historical_context,
            ContextLayer.DOMAIN: self._process_domain_context,
            ContextLayer.BEHAVIORAL: self._process_behavioral_context,
            ContextLayer.ENVIRONMENTAL: self._process_environmental_context,
            ContextLayer.GLOBAL: self._process_global_context
        }
        
        # Context influence tracking
        self.influence_matrix = defaultdict(lambda: defaultdict(float))
        
        logger.info("Context7MCP initialized with 7 context layers")
    
    def create_context(self, context_id: Optional[str] = None) -> str:
        """Create a new context state"""
        if not context_id:
            import uuid
            context_id = str(uuid.uuid4())
        
        self.context_states[context_id] = ContextState()
        
        # Initialize with default values
        self._initialize_default_context(context_id)
        
        logger.info(f"Created context7 state: {context_id}")
        return context_id
    
    def set_context(self, context_id: str, layer: ContextLayer, 
                   key: str, value: Any, confidence: float = 1.0,
                   source: str = "system", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set a value in a specific context layer"""
        if context_id not in self.context_states:
            logger.error(f"Context {context_id} not found")
            return False
        
        entry = ContextEntry(
            key=key,
            value=value,
            layer=layer,
            confidence=confidence,
            source=source,
            metadata=metadata or {}
        )
        
        state = self.context_states[context_id]
        state.layers[layer][key] = entry
        state.last_updated = datetime.now()
        state.version += 1
        
        # Update influence tracking
        self._update_influence(context_id, layer, key)
        
        logger.debug(f"Set context {layer.value}.{key} = {value} in {context_id}")
        return True
    
    def get_context(self, context_id: str, layer: Optional[ContextLayer] = None,
                   key: Optional[str] = None) -> Optional[Any]:
        """Get context value(s)"""
        if context_id not in self.context_states:
            return None
        
        state = self.context_states[context_id]
        
        # Get specific value
        if layer and key:
            entry = state.layers[layer].get(key)
            return entry.value if entry else None
        
        # Get all values in a layer
        elif layer:
            return {
                k: entry.value 
                for k, entry in state.layers[layer].items()
            }
        
        # Get all context
        else:
            return {
                layer.value: {
                    k: entry.value 
                    for k, entry in entries.items()
                }
                for layer, entries in state.layers.items()
            }
    
    def analyze_context(self, context_id: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context to make intelligent decisions"""
        if context_id not in self.context_states:
            return {"error": "Context not found"}
        
        state = self.context_states[context_id]
        analysis = {
            "recommendations": [],
            "confidence_scores": {},
            "relevant_context": {},
            "conflicts": [],
            "insights": []
        }
        
        # Analyze each layer
        for layer in ContextLayer:
            layer_analysis = self.layer_processors[layer](state, query)
            
            # Aggregate recommendations
            if "recommendations" in layer_analysis:
                for rec in layer_analysis["recommendations"]:
                    weighted_rec = {
                        **rec,
                        "weight": rec.get("confidence", 1.0) * self.layer_weights[layer]
                    }
                    analysis["recommendations"].append(weighted_rec)
            
            # Collect relevant context
            if "relevant" in layer_analysis:
                analysis["relevant_context"][layer.value] = layer_analysis["relevant"]
            
            # Track confidence
            if "confidence" in layer_analysis:
                analysis["confidence_scores"][layer.value] = layer_analysis["confidence"]
        
        # Sort recommendations by weight
        analysis["recommendations"].sort(key=lambda x: x["weight"], reverse=True)
        
        # Detect conflicts between layers
        analysis["conflicts"] = self._detect_conflicts(state)
        
        # Generate insights
        analysis["insights"] = self._generate_insights(state, query)
        
        return analysis
    
    def merge_contexts(self, context_ids: List[str], strategy: str = "weighted") -> str:
        """Merge multiple contexts into a new context"""
        new_context_id = self.create_context()
        new_state = self.context_states[new_context_id]
        
        if strategy == "weighted":
            # Weight by recency and confidence
            for context_id in context_ids:
                if context_id not in self.context_states:
                    continue
                
                state = self.context_states[context_id]
                age_factor = 1.0 / (1.0 + (datetime.now() - state.last_updated).total_seconds() / 3600)
                
                for layer, entries in state.layers.items():
                    for key, entry in entries.items():
                        existing = new_state.layers[layer].get(key)
                        
                        if not existing or (entry.confidence * age_factor > existing.confidence):
                            new_state.layers[layer][key] = ContextEntry(
                                key=key,
                                value=entry.value,
                                layer=layer,
                                confidence=entry.confidence * age_factor,
                                source=f"merged:{entry.source}",
                                metadata={**entry.metadata, "original_context": context_id}
                            )
        
        elif strategy == "union":
            # Keep all unique values
            for context_id in context_ids:
                if context_id not in self.context_states:
                    continue
                
                state = self.context_states[context_id]
                for layer, entries in state.layers.items():
                    for key, entry in entries.items():
                        if key not in new_state.layers[layer]:
                            new_state.layers[layer][key] = entry
        
        logger.info(f"Merged {len(context_ids)} contexts into {new_context_id}")
        return new_context_id
    
    def _initialize_default_context(self, context_id: str):
        """Initialize context with default values"""
        # Set default environmental context
        self.set_context(context_id, ContextLayer.ENVIRONMENTAL, 
                        "system_time", datetime.now().isoformat())
        self.set_context(context_id, ContextLayer.ENVIRONMENTAL,
                        "system_version", "2.0")
        
        # Set default global context
        self.set_context(context_id, ContextLayer.GLOBAL,
                        "processing_mode", "standard")
        self.set_context(context_id, ContextLayer.GLOBAL,
                        "quality_threshold", 0.7)
    
    def _process_immediate_context(self, state: ContextState, query: Dict[str, Any]) -> Dict[str, Any]:
        """Process immediate context layer"""
        result = {
            "recommendations": [],
            "relevant": {},
            "confidence": 1.0
        }
        
        # Check current document type
        doc_type = state.layers[ContextLayer.IMMEDIATE].get("document_type")
        if doc_type:
            result["relevant"]["document_type"] = doc_type.value
            
            # Recommend specific processors
            if doc_type.value == "passport":
                result["recommendations"].append({
                    "action": "use_mrz_extraction",
                    "reason": "Passport detected",
                    "confidence": 0.9
                })
        
        # Check image quality
        quality = state.layers[ContextLayer.IMMEDIATE].get("image_quality")
        if quality and quality.value < 0.5:
            result["recommendations"].append({
                "action": "enhance_image_quality",
                "reason": "Low image quality detected",
                "confidence": 0.8
            })
        
        return result
    
    def _process_session_context(self, state: ContextState, query: Dict[str, Any]) -> Dict[str, Any]:
        """Process session context layer"""
        result = {
            "recommendations": [],
            "relevant": {},
            "confidence": 0.8
        }
        
        # Check session patterns
        error_count = state.layers[ContextLayer.SESSION].get("error_count")
        if error_count and error_count.value > 3:
            result["recommendations"].append({
                "action": "switch_processing_mode",
                "reason": "Multiple errors in session",
                "confidence": 0.7
            })
        
        # Check processing speed
        avg_time = state.layers[ContextLayer.SESSION].get("avg_processing_time")
        if avg_time and avg_time.value > 5.0:
            result["recommendations"].append({
                "action": "enable_fast_mode",
                "reason": "Slow processing detected",
                "confidence": 0.6
            })
        
        return result
    
    def _process_historical_context(self, state: ContextState, query: Dict[str, Any]) -> Dict[str, Any]:
        """Process historical context layer"""
        result = {
            "recommendations": [],
            "relevant": {},
            "confidence": 0.6
        }
        
        # Check historical success rates
        success_rate = state.layers[ContextLayer.HISTORICAL].get("success_rate")
        if success_rate:
            result["relevant"]["historical_success_rate"] = success_rate.value
            
            if success_rate.value < 0.5:
                result["recommendations"].append({
                    "action": "use_alternative_processor",
                    "reason": "Low historical success rate",
                    "confidence": 0.5
                })
        
        return result
    
    def _process_domain_context(self, state: ContextState, query: Dict[str, Any]) -> Dict[str, Any]:
        """Process domain context layer"""
        result = {
            "recommendations": [],
            "relevant": {},
            "confidence": 0.7
        }
        
        # Check domain-specific rules
        domain = state.layers[ContextLayer.DOMAIN].get("document_domain")
        if domain:
            result["relevant"]["domain"] = domain.value
            
            # Apply domain-specific recommendations
            if domain.value == "government_id":
                result["recommendations"].append({
                    "action": "enable_security_validation",
                    "reason": "Government ID requires security checks",
                    "confidence": 0.9
                })
        
        return result
    
    def _process_behavioral_context(self, state: ContextState, query: Dict[str, Any]) -> Dict[str, Any]:
        """Process behavioral context layer"""
        result = {
            "recommendations": [],
            "relevant": {},
            "confidence": 0.5
        }
        
        # Check user preferences
        preferred_format = state.layers[ContextLayer.BEHAVIORAL].get("preferred_output_format")
        if preferred_format:
            result["relevant"]["preferred_format"] = preferred_format.value
            result["recommendations"].append({
                "action": f"format_output_as_{preferred_format.value}",
                "reason": "User preference",
                "confidence": 0.8
            })
        
        return result
    
    def _process_environmental_context(self, state: ContextState, query: Dict[str, Any]) -> Dict[str, Any]:
        """Process environmental context layer"""
        result = {
            "recommendations": [],
            "relevant": {},
            "confidence": 0.4
        }
        
        # Check system resources
        cpu_usage = state.layers[ContextLayer.ENVIRONMENTAL].get("cpu_usage")
        if cpu_usage and cpu_usage.value > 0.8:
            result["recommendations"].append({
                "action": "use_lightweight_processor",
                "reason": "High CPU usage",
                "confidence": 0.7
            })
        
        return result
    
    def _process_global_context(self, state: ContextState, query: Dict[str, Any]) -> Dict[str, Any]:
        """Process global context layer"""
        result = {
            "recommendations": [],
            "relevant": {},
            "confidence": 0.3
        }
        
        # Check global settings
        mode = state.layers[ContextLayer.GLOBAL].get("processing_mode")
        if mode:
            result["relevant"]["global_mode"] = mode.value
        
        return result
    
    def _detect_conflicts(self, state: ContextState) -> List[Dict[str, Any]]:
        """Detect conflicts between context layers"""
        conflicts = []
        
        # Check for quality vs speed conflicts
        quality_req = state.layers[ContextLayer.IMMEDIATE].get("quality_requirement")
        speed_req = state.layers[ContextLayer.SESSION].get("speed_requirement")
        
        if quality_req and speed_req:
            if quality_req.value == "high" and speed_req.value == "fast":
                conflicts.append({
                    "type": "quality_vs_speed",
                    "layers": ["immediate", "session"],
                    "severity": "medium",
                    "resolution": "balance_quality_speed"
                })
        
        return conflicts
    
    def _generate_insights(self, state: ContextState, query: Dict[str, Any]) -> List[str]:
        """Generate insights from context analysis"""
        insights = []
        
        # Analyze patterns across layers
        doc_types = []
        for layer in [ContextLayer.IMMEDIATE, ContextLayer.HISTORICAL]:
            doc_type = state.layers[layer].get("document_type")
            if doc_type:
                doc_types.append(doc_type.value)
        
        if len(set(doc_types)) == 1:
            insights.append(f"Consistent document type: {doc_types[0]}")
        elif len(set(doc_types)) > 1:
            insights.append("Multiple document types detected across contexts")
        
        # Check for optimization opportunities
        total_entries = sum(len(entries) for entries in state.layers.values())
        if total_entries > 100:
            insights.append("Large context size - consider context pruning")
        
        return insights
    
    def _update_influence(self, context_id: str, layer: ContextLayer, key: str):
        """Update influence tracking between context elements"""
        # Track which keys influence each other
        state = self.context_states[context_id]
        
        # Simple heuristic: keys set close in time influence each other
        recent_keys = []
        now = datetime.now()
        
        for l, entries in state.layers.items():
            for k, entry in entries.items():
                if (now - entry.timestamp).total_seconds() < 60:  # Within last minute
                    recent_keys.append((l, k))
        
        # Update influence matrix
        for l, k in recent_keys:
            if (l, k) != (layer, key):
                self.influence_matrix[f"{layer.value}.{key}"][f"{l.value}.{k}"] += 0.1
    
    def export_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Export context state for analysis or persistence"""
        if context_id not in self.context_states:
            return None
        
        state = self.context_states[context_id]
        
        return {
            "context_id": context_id,
            "version": state.version,
            "last_updated": state.last_updated.isoformat(),
            "layers": {
                layer.value: {
                    key: {
                        "value": entry.value,
                        "confidence": entry.confidence,
                        "source": entry.source,
                        "timestamp": entry.timestamp.isoformat(),
                        "metadata": entry.metadata
                    }
                    for key, entry in entries.items()
                }
                for layer, entries in state.layers.items()
            },
            "relationships": [
                {"from": f, "to": t, "type": r}
                for f, t, r in state.relationships
            ]
        }
    
    def get_context_summary(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the context state"""
        if context_id not in self.context_states:
            return None
        
        state = self.context_states[context_id]
        
        summary = {
            "context_id": context_id,
            "version": state.version,
            "last_updated": state.last_updated.isoformat(),
            "layer_stats": {},
            "total_entries": 0,
            "avg_confidence": 0.0
        }
        
        total_confidence = 0.0
        total_entries = 0
        
        for layer in ContextLayer:
            entries = state.layers[layer]
            layer_confidence = sum(e.confidence for e in entries.values()) / len(entries) if entries else 0
            
            summary["layer_stats"][layer.value] = {
                "entry_count": len(entries),
                "avg_confidence": layer_confidence,
                "weight": self.layer_weights[layer]
            }
            
            total_confidence += sum(e.confidence for e in entries.values())
            total_entries += len(entries)
        
        summary["total_entries"] = total_entries
        summary["avg_confidence"] = total_confidence / total_entries if total_entries > 0 else 0
        
        return summary