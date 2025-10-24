"""
ARES Agent Memory System - Long-Horizon Task Memory
Implements 2025 best practice: persistent memory for multi-phase tasks

Pattern: Context Engineering - Writing context outside the window
Reference: Multi-agent research systems (Anthropic 2025)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class MemoryType(Enum):
    """Types of memory storage"""
    SCRATCHPAD = "scratchpad"  # Working memory for current phase
    COMPLETED_PHASE = "completed_phase"  # Finished work summaries
    KEY_DECISION = "key_decision"  # Important choices made
    CONTEXT_SUMMARY = "context_summary"  # Compressed context
    TOOL_RESULT = "tool_result"  # Tool execution results
    VALIDATION_RESULT = "validation_result"  # ARES validation outputs


@dataclass
class MemoryEntry:
    """Single memory entry"""
    memory_type: MemoryType
    timestamp: datetime
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    phase_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'memory_type': self.memory_type.value,
            'timestamp': self.timestamp.isoformat(),
            'content': self.content,
            'metadata': self.metadata,
            'confidence': self.confidence,
            'phase_id': self.phase_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Deserialize from dictionary"""
        return cls(
            memory_type=MemoryType(data['memory_type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            content=data['content'],
            metadata=data.get('metadata', {}),
            confidence=data.get('confidence', 1.0),
            phase_id=data.get('phase_id')
        )


class AgentMemory:
    """
    Long-horizon memory for ARES agents

    Enables agents to handle tasks spanning 100+ turns by:
    - Storing working memory (scratchpad)
    - Summarizing completed phases
    - Preserving key decisions
    - Compressing context when needed

    Usage:
        memory = AgentMemory(agent_id="frontend-architect", task_id="build-dashboard")
        memory.add_scratchpad("Working on component hierarchy...")
        memory.complete_phase("Phase 1: Component Design", summary="...")
        context = memory.get_active_context()  # For next phase
    """

    def __init__(
        self,
        agent_id: str,
        task_id: str,
        persistence_path: Optional[Path] = None
    ):
        """
        Initialize agent memory

        Args:
            agent_id: ID of the agent using this memory
            task_id: ID of the task this memory is for
            persistence_path: Path to save memory (optional, for persistence)
        """
        self.agent_id = agent_id
        self.task_id = task_id
        self.persistence_path = persistence_path

        self.memories: List[MemoryEntry] = []
        self.current_phase_id: Optional[str] = None
        self.completed_phases: List[str] = []

        # Load from disk if persistence enabled
        if persistence_path and persistence_path.exists():
            self.load()

    def add_scratchpad(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add working memory for current phase

        Args:
            content: Scratchpad content (thoughts, progress, notes)
            metadata: Optional metadata
        """
        entry = MemoryEntry(
            memory_type=MemoryType.SCRATCHPAD,
            timestamp=datetime.now(),
            content=content,
            metadata=metadata or {},
            phase_id=self.current_phase_id
        )
        self.memories.append(entry)
        self._auto_save()

    def complete_phase(
        self,
        phase_name: str,
        summary: str,
        confidence: float = 1.0
    ) -> None:
        """
        Mark current phase as complete with summary

        Args:
            phase_name: Name of completed phase
            summary: Summary of work done
            confidence: Confidence in phase completion (0-1)
        """
        entry = MemoryEntry(
            memory_type=MemoryType.COMPLETED_PHASE,
            timestamp=datetime.now(),
            content=summary,
            metadata={'phase_name': phase_name},
            confidence=confidence,
            phase_id=self.current_phase_id
        )
        self.memories.append(entry)

        if self.current_phase_id:
            self.completed_phases.append(self.current_phase_id)

        self._auto_save()

    def record_decision(
        self,
        decision: str,
        reasoning: str,
        confidence: float,
        alternatives_considered: Optional[List[str]] = None
    ) -> None:
        """
        Record key decision made during task

        Args:
            decision: The decision made
            reasoning: Why this decision was made
            confidence: Confidence in decision (0-1)
            alternatives_considered: Other options considered
        """
        entry = MemoryEntry(
            memory_type=MemoryType.KEY_DECISION,
            timestamp=datetime.now(),
            content=decision,
            metadata={
                'reasoning': reasoning,
                'alternatives': alternatives_considered or []
            },
            confidence=confidence,
            phase_id=self.current_phase_id
        )
        self.memories.append(entry)
        self._auto_save()

    def add_context_summary(
        self,
        summary: str,
        original_length: int,
        compressed_length: int
    ) -> None:
        """
        Add compressed context summary

        Args:
            summary: Compressed context
            original_length: Original context length (chars)
            compressed_length: Compressed length (chars)
        """
        compression_ratio = compressed_length / original_length if original_length > 0 else 0

        entry = MemoryEntry(
            memory_type=MemoryType.CONTEXT_SUMMARY,
            timestamp=datetime.now(),
            content=summary,
            metadata={
                'original_length': original_length,
                'compressed_length': compressed_length,
                'compression_ratio': compression_ratio
            },
            phase_id=self.current_phase_id
        )
        self.memories.append(entry)
        self._auto_save()

    def record_tool_result(
        self,
        tool_name: str,
        result: str,
        success: bool
    ) -> None:
        """
        Record tool execution result

        Args:
            tool_name: Name of tool executed
            result: Tool output
            success: Whether execution succeeded
        """
        entry = MemoryEntry(
            memory_type=MemoryType.TOOL_RESULT,
            timestamp=datetime.now(),
            content=result,
            metadata={
                'tool_name': tool_name,
                'success': success
            },
            phase_id=self.current_phase_id
        )
        self.memories.append(entry)
        self._auto_save()

    def record_validation(
        self,
        validation_type: str,
        result: str,
        passed: bool,
        confidence: float
    ) -> None:
        """
        Record ARES validation result

        Args:
            validation_type: Type of validation (challenge, simplify, etc.)
            result: Validation output
            passed: Whether validation passed
            confidence: Confidence level (0-1)
        """
        entry = MemoryEntry(
            memory_type=MemoryType.VALIDATION_RESULT,
            timestamp=datetime.now(),
            content=result,
            metadata={
                'validation_type': validation_type,
                'passed': passed
            },
            confidence=confidence,
            phase_id=self.current_phase_id
        )
        self.memories.append(entry)
        self._auto_save()

    def start_new_phase(self, phase_id: str) -> None:
        """
        Start a new phase of work

        Args:
            phase_id: Identifier for new phase
        """
        self.current_phase_id = phase_id

    def get_active_context(
        self,
        max_length: Optional[int] = None,
        include_types: Optional[List[MemoryType]] = None
    ) -> str:
        """
        Get active context for current work

        Args:
            max_length: Maximum context length (chars)
            include_types: Filter to specific memory types

        Returns:
            Formatted context string
        """
        # Filter memories
        relevant_memories = self.memories

        if include_types:
            relevant_memories = [
                m for m in relevant_memories
                if m.memory_type in include_types
            ]

        # Build context string
        context_parts = []

        # Add completed phases
        for phase_id in self.completed_phases:
            phase_memories = [m for m in relevant_memories if m.phase_id == phase_id]
            if phase_memories:
                context_parts.append(f"\n## Completed Phase: {phase_id}")
                for memory in phase_memories:
                    if memory.memory_type == MemoryType.COMPLETED_PHASE:
                        context_parts.append(f"Summary: {memory.content}")

        # Add current phase
        if self.current_phase_id:
            context_parts.append(f"\n## Current Phase: {self.current_phase_id}")
            current_memories = [
                m for m in relevant_memories
                if m.phase_id == self.current_phase_id
            ]
            for memory in current_memories:
                context_parts.append(f"[{memory.memory_type.value}] {memory.content}")

        # Add key decisions
        decisions = [m for m in relevant_memories if m.memory_type == MemoryType.KEY_DECISION]
        if decisions:
            context_parts.append("\n## Key Decisions Made:")
            for decision in decisions:
                context_parts.append(f"- {decision.content} (confidence: {decision.confidence:.0%})")
                context_parts.append(f"  Reasoning: {decision.metadata.get('reasoning', 'N/A')}")

        context = "\n".join(context_parts)

        # Compress if needed
        if max_length and len(context) > max_length:
            context = self._compress_context(context, max_length)

        return context

    def get_phase_summary(self, phase_id: str) -> Optional[str]:
        """Get summary of a completed phase"""
        for memory in self.memories:
            if (memory.phase_id == phase_id and
                memory.memory_type == MemoryType.COMPLETED_PHASE):
                return memory.content
        return None

    def get_all_decisions(self) -> List[MemoryEntry]:
        """Get all key decisions made"""
        return [m for m in self.memories if m.memory_type == MemoryType.KEY_DECISION]

    def get_validation_history(self) -> List[MemoryEntry]:
        """Get all validation results"""
        return [m for m in self.memories if m.memory_type == MemoryType.VALIDATION_RESULT]

    def _compress_context(self, context: str, max_length: int) -> str:
        """
        Compress context to fit within max_length

        Strategy: Keep most recent and most important memories
        """
        # Simple compression: truncate and add summary
        if len(context) <= max_length:
            return context

        compressed = context[:max_length - 100]
        compressed += "\n\n[...Context compressed to fit within limits...]"

        return compressed

    def _auto_save(self) -> None:
        """Auto-save memory if persistence enabled"""
        if self.persistence_path:
            self.save()

    def save(self, path: Optional[Path] = None) -> bool:
        """
        Save memory to disk

        Args:
            path: Path to save to (uses self.persistence_path if None)

        Returns:
            True if saved successfully
        """
        save_path = path or self.persistence_path
        if not save_path:
            return False

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'agent_id': self.agent_id,
                'task_id': self.task_id,
                'current_phase_id': self.current_phase_id,
                'completed_phases': self.completed_phases,
                'memories': [m.to_dict() for m in self.memories],
                'saved_at': datetime.now().isoformat()
            }

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving memory: {e}")
            return False

    def load(self, path: Optional[Path] = None) -> bool:
        """
        Load memory from disk

        Args:
            path: Path to load from (uses self.persistence_path if None)

        Returns:
            True if loaded successfully
        """
        load_path = path or self.persistence_path
        if not load_path or not load_path.exists():
            return False

        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.agent_id = data['agent_id']
            self.task_id = data['task_id']
            self.current_phase_id = data.get('current_phase_id')
            self.completed_phases = data.get('completed_phases', [])
            self.memories = [MemoryEntry.from_dict(m) for m in data.get('memories', [])]

            return True

        except Exception as e:
            print(f"Error loading memory: {e}")
            return False

    def clear(self) -> None:
        """Clear all memory"""
        self.memories = []
        self.current_phase_id = None
        self.completed_phases = []

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'total_memories': len(self.memories),
            'current_phase': self.current_phase_id,
            'completed_phases': len(self.completed_phases),
            'scratchpad_entries': len([m for m in self.memories if m.memory_type == MemoryType.SCRATCHPAD]),
            'decisions_made': len([m for m in self.memories if m.memory_type == MemoryType.KEY_DECISION]),
            'validations_run': len([m for m in self.memories if m.memory_type == MemoryType.VALIDATION_RESULT]),
            'oldest_memory': min((m.timestamp for m in self.memories), default=None),
            'newest_memory': max((m.timestamp for m in self.memories), default=None),
        }


def create_memory(
    agent_id: str,
    task_id: str,
    persistence_dir: Optional[Path] = None
) -> AgentMemory:
    """
    Create agent memory instance

    Args:
        agent_id: Agent identifier
        task_id: Task identifier
        persistence_dir: Directory to save memory files

    Returns:
        AgentMemory instance
    """
    persistence_path = None
    if persistence_dir:
        persistence_path = persistence_dir / f"{agent_id}_{task_id}_memory.json"

    return AgentMemory(agent_id, task_id, persistence_path)
