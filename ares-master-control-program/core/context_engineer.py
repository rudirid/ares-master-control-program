"""
ARES Context Engineering Module - 2025 Best Practice
Manages context for long-horizon tasks through compression, selection, and isolation

Pattern: Context Engineering (not just prompt engineering)
Reference: Multi-agent systems 2025 (#1 job of agent builders)

Four key aspects:
1. Writing context outside the window (scratchpads, memories)
2. Selecting relevant context (RAG, memory retrieval)
3. Compressing context (summarization, trimming)
4. Isolating context (multi-agent systems, sandboxing)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class CompressionStrategy(Enum):
    """Context compression strategies"""
    SUMMARIZE = "summarize"  # Summarize content
    TRIM_OLDEST = "trim_oldest"  # Remove oldest content
    TRIM_LEAST_RELEVANT = "trim_least_relevant"  # Remove least relevant
    HIERARCHICAL = "hierarchical"  # Keep hierarchy, compress details


class RelevanceScore(Enum):
    """Relevance scoring for context selection"""
    CRITICAL = 1.0  # Must include
    HIGH = 0.8  # Very relevant
    MEDIUM = 0.5  # Somewhat relevant
    LOW = 0.2  # Optional
    IRRELEVANT = 0.0  # Exclude


@dataclass
class ContextChunk:
    """Single chunk of context"""
    content: str
    chunk_type: str  # 'code', 'docs', 'conversation', 'memory'
    relevance: float  # 0-1
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def get_length(self) -> int:
        """Get chunk length in characters"""
        return len(self.content)


class ContextEngineer:
    """
    Manages context for ARES agents

    Responsibilities:
    - Compress context when approaching limits
    - Select most relevant context for task
    - Isolate agent contexts (sandboxing)
    - Track context usage and optimize

    Usage:
        engineer = ContextEngineer(max_context_length=100000)

        # Add various context
        engineer.add_context("code", code_content, relevance=0.9)
        engineer.add_context("docs", docs, relevance=0.6)

        # Get optimized context
        optimized = engineer.get_optimized_context(target_length=50000)
    """

    def __init__(
        self,
        max_context_length: int = 100000,
        compression_threshold: float = 0.8  # Compress when 80% full
    ):
        """
        Initialize context engineer

        Args:
            max_context_length: Maximum context length in characters
            compression_threshold: When to trigger compression (0-1)
        """
        self.max_context_length = max_context_length
        self.compression_threshold = compression_threshold

        self.context_chunks: List[ContextChunk] = []
        self.total_length = 0

    def add_context(
        self,
        chunk_type: str,
        content: str,
        relevance: float = 0.5,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add context chunk

        Args:
            chunk_type: Type of context (code, docs, conversation, memory)
            content: The content
            relevance: Relevance score (0-1)
            timestamp: Optional timestamp
            metadata: Optional metadata
        """
        chunk = ContextChunk(
            content=content,
            chunk_type=chunk_type,
            relevance=relevance,
            timestamp=timestamp,
            metadata=metadata or {}
        )

        self.context_chunks.append(chunk)
        self.total_length += chunk.get_length()

        # Auto-compress if needed
        if self._should_compress():
            self._auto_compress()

    def get_optimized_context(
        self,
        target_length: Optional[int] = None,
        min_relevance: float = 0.0,
        chunk_types: Optional[List[str]] = None
    ) -> str:
        """
        Get optimized context for task

        Args:
            target_length: Target length (uses max if None)
            min_relevance: Minimum relevance to include
            chunk_types: Filter to specific chunk types

        Returns:
            Optimized context string
        """
        target = target_length or self.max_context_length

        # Filter chunks
        filtered = self.context_chunks

        if min_relevance > 0:
            filtered = [c for c in filtered if c.relevance >= min_relevance]

        if chunk_types:
            filtered = [c for c in filtered if c.chunk_type in chunk_types]

        # Sort by relevance (high to low)
        sorted_chunks = sorted(filtered, key=lambda c: c.relevance, reverse=True)

        # Build context within target length
        result_chunks = []
        current_length = 0

        for chunk in sorted_chunks:
            chunk_length = chunk.get_length()

            if current_length + chunk_length <= target:
                result_chunks.append(chunk)
                current_length += chunk_length
            else:
                # Try to compress this chunk to fit
                remaining = target - current_length
                if remaining > 100:  # Only if reasonable space left
                    compressed = self._compress_chunk(chunk, remaining)
                    if compressed:
                        result_chunks.append(compressed)
                        current_length += compressed.get_length()
                break

        # Combine chunks into context string
        context_parts = []
        for chunk in result_chunks:
            context_parts.append(f"[{chunk.chunk_type.upper()}]")
            context_parts.append(chunk.content)
            context_parts.append("")  # Blank line separator

        return "\n".join(context_parts)

    def compress_context(
        self,
        strategy: CompressionStrategy = CompressionStrategy.TRIM_LEAST_RELEVANT,
        target_ratio: float = 0.5
    ) -> int:
        """
        Compress existing context

        Args:
            strategy: Compression strategy to use
            target_ratio: Target compression ratio (0-1)

        Returns:
            Number of characters saved
        """
        original_length = self.total_length
        target_length = int(original_length * target_ratio)

        if strategy == CompressionStrategy.TRIM_LEAST_RELEVANT:
            self._trim_least_relevant(target_length)

        elif strategy == CompressionStrategy.TRIM_OLDEST:
            self._trim_oldest(target_length)

        elif strategy == CompressionStrategy.SUMMARIZE:
            self._summarize_context(target_length)

        elif strategy == CompressionStrategy.HIERARCHICAL:
            self._hierarchical_compress(target_length)

        new_length = sum(c.get_length() for c in self.context_chunks)
        self.total_length = new_length

        return original_length - new_length

    def isolate_agent_context(
        self,
        agent_id: str,
        shared_context: Optional[str] = None
    ) -> str:
        """
        Create isolated context for specific agent

        Args:
            agent_id: Agent identifier
            shared_context: Optional shared context (read-only)

        Returns:
            Isolated context for agent
        """
        # Get agent-specific chunks
        agent_chunks = [
            c for c in self.context_chunks
            if c.metadata.get('agent_id') == agent_id or c.metadata.get('shared', False)
        ]

        # Build isolated context
        parts = []

        if shared_context:
            parts.append("[SHARED CONTEXT - READ ONLY]")
            parts.append(shared_context)
            parts.append("")

        parts.append(f"[AGENT: {agent_id} - PRIVATE CONTEXT]")
        for chunk in agent_chunks:
            parts.append(chunk.content)

        return "\n".join(parts)

    def select_relevant_context(
        self,
        query: str,
        top_k: int = 5
    ) -> List[ContextChunk]:
        """
        Select most relevant context for query

        Args:
            query: Query or task description
            top_k: Number of top chunks to return

        Returns:
            List of most relevant chunks
        """
        # Simple relevance scoring (keyword matching)
        # In production, use embeddings and semantic search

        query_lower = query.lower()
        query_keywords = set(re.findall(r'\w+', query_lower))

        scored_chunks = []
        for chunk in self.context_chunks:
            content_lower = chunk.content.lower()
            content_keywords = set(re.findall(r'\w+', content_lower))

            # Keyword overlap score
            overlap = len(query_keywords & content_keywords)
            overlap_score = overlap / len(query_keywords) if query_keywords else 0

            # Combine with existing relevance
            combined_score = (chunk.relevance * 0.5) + (overlap_score * 0.5)

            scored_chunks.append((combined_score, chunk))

        # Sort by score and return top k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:top_k]]

    def get_context_stats(self) -> Dict[str, Any]:
        """Get context statistics"""
        chunk_types_count = {}
        for chunk in self.context_chunks:
            chunk_types_count[chunk.chunk_type] = chunk_types_count.get(chunk.chunk_type, 0) + 1

        avg_relevance = (
            sum(c.relevance for c in self.context_chunks) / len(self.context_chunks)
            if self.context_chunks else 0
        )

        return {
            'total_chunks': len(self.context_chunks),
            'total_length': self.total_length,
            'max_length': self.max_context_length,
            'utilization': self.total_length / self.max_context_length if self.max_context_length > 0 else 0,
            'average_relevance': avg_relevance,
            'chunk_types': chunk_types_count,
            'compression_needed': self._should_compress()
        }

    def clear(self) -> None:
        """Clear all context"""
        self.context_chunks = []
        self.total_length = 0

    # Private methods

    def _should_compress(self) -> bool:
        """Check if compression is needed"""
        if self.max_context_length == 0:
            return False
        utilization = self.total_length / self.max_context_length
        return utilization >= self.compression_threshold

    def _auto_compress(self) -> None:
        """Automatically compress context"""
        # Use trim least relevant strategy by default
        target_length = int(self.max_context_length * 0.7)  # Target 70% utilization
        self._trim_least_relevant(target_length)

    def _trim_least_relevant(self, target_length: int) -> None:
        """Trim least relevant chunks to reach target length"""
        # Sort by relevance (low to high)
        sorted_chunks = sorted(self.context_chunks, key=lambda c: c.relevance)

        current_length = self.total_length
        removed_chunks = []

        for chunk in sorted_chunks:
            if current_length <= target_length:
                break

            current_length -= chunk.get_length()
            removed_chunks.append(chunk)

        # Remove least relevant chunks
        for chunk in removed_chunks:
            self.context_chunks.remove(chunk)

    def _trim_oldest(self, target_length: int) -> None:
        """Trim oldest chunks to reach target length"""
        # Sort by timestamp (oldest first)
        sorted_chunks = sorted(
            self.context_chunks,
            key=lambda c: c.timestamp or ""
        )

        current_length = self.total_length
        removed_chunks = []

        for chunk in sorted_chunks:
            if current_length <= target_length:
                break

            current_length -= chunk.get_length()
            removed_chunks.append(chunk)

        for chunk in removed_chunks:
            self.context_chunks.remove(chunk)

    def _summarize_context(self, target_length: int) -> None:
        """
        Summarize context to fit target length

        Note: This is a placeholder. In production, use LLM to summarize.
        """
        # Group chunks by type
        by_type: Dict[str, List[ContextChunk]] = {}
        for chunk in self.context_chunks:
            if chunk.chunk_type not in by_type:
                by_type[chunk.chunk_type] = []
            by_type[chunk.chunk_type].append(chunk)

        # Create summary chunks
        summarized_chunks = []
        for chunk_type, chunks in by_type.items():
            combined = "\n".join(c.content for c in chunks)

            # Simple summarization: take first portion
            # In production: use LLM summarization
            max_per_type = target_length // len(by_type)
            if len(combined) > max_per_type:
                summarized = combined[:max_per_type] + "\n...[content summarized]..."
            else:
                summarized = combined

            summary_chunk = ContextChunk(
                content=summarized,
                chunk_type=chunk_type,
                relevance=max(c.relevance for c in chunks),
                metadata={'summarized': True, 'original_chunks': len(chunks)}
            )
            summarized_chunks.append(summary_chunk)

        self.context_chunks = summarized_chunks

    def _hierarchical_compress(self, target_length: int) -> None:
        """
        Hierarchical compression: keep structure, compress details

        Keep headers, high-level structure, compress detailed content
        """
        compressed_chunks = []

        for chunk in self.context_chunks:
            lines = chunk.content.split('\n')
            compressed_lines = []

            for line in lines:
                # Keep headers, bullet points, important markers
                if (line.strip().startswith('#') or
                    line.strip().startswith('-') or
                    line.strip().startswith('*') or
                    len(line.strip()) < 100):
                    compressed_lines.append(line)
                else:
                    # Compress detailed lines (take first portion)
                    if line.strip():
                        compressed_lines.append(line[:100] + "...")

            compressed_content = '\n'.join(compressed_lines)

            compressed_chunk = ContextChunk(
                content=compressed_content,
                chunk_type=chunk.chunk_type,
                relevance=chunk.relevance,
                timestamp=chunk.timestamp,
                metadata={**chunk.metadata, 'hierarchically_compressed': True}
            )
            compressed_chunks.append(compressed_chunk)

        self.context_chunks = compressed_chunks

        # If still too large, trim least relevant
        current_length = sum(c.get_length() for c in compressed_chunks)
        if current_length > target_length:
            self._trim_least_relevant(target_length)

    def _compress_chunk(
        self,
        chunk: ContextChunk,
        max_length: int
    ) -> Optional[ContextChunk]:
        """
        Compress a single chunk to fit max_length

        Args:
            chunk: Chunk to compress
            max_length: Maximum length for compressed chunk

        Returns:
            Compressed chunk or None if can't compress sufficiently
        """
        if chunk.get_length() <= max_length:
            return chunk

        # Simple compression: truncate and add marker
        compressed_content = chunk.content[:max_length - 30]
        compressed_content += "\n...[truncated for space]..."

        return ContextChunk(
            content=compressed_content,
            chunk_type=chunk.chunk_type,
            relevance=chunk.relevance,
            timestamp=chunk.timestamp,
            metadata={**chunk.metadata, 'compressed': True}
        )


def create_context_engineer(
    max_context_length: int = 100000,
    compression_threshold: float = 0.8
) -> ContextEngineer:
    """
    Create context engineer instance

    Args:
        max_context_length: Maximum context length
        compression_threshold: When to auto-compress

    Returns:
        ContextEngineer instance
    """
    return ContextEngineer(max_context_length, compression_threshold)
