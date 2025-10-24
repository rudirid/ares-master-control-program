"""
ARES Knowledge Base RAG - Retrieval Augmented Generation
Retrieves relevant patterns, best practices, and knowledge for agents

Pattern: Context Engineering - Selecting relevant context (RAG)
Reference: 2025 best practice for agent context management
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class KnowledgeChunk:
    """Single chunk of knowledge from knowledge base"""
    content: str
    source_file: str
    chunk_type: str  # 'pattern', 'anti_pattern', 'tech_matrix', 'decision'
    tier: Optional[str] = None  # 'tier_1', 'tier_2', 'tier_3' for patterns
    relevance_score: float = 0.0
    metadata: Dict[str, any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KnowledgeBaseRAG:
    """
    Retrieves relevant knowledge from ARES knowledge base

    Knowledge sources:
    - proven-patterns.md (Tier 1/2/3 patterns)
    - tech-success-matrix.md (technology success rates)
    - decision-causality.md (past decisions and reasoning)
    - anti-patterns (what to avoid)

    Usage:
        rag = KnowledgeBaseRAG(base_path="/path/to/ares-master-control-program")
        patterns = rag.retrieve_patterns("frontend", "React component design")
        tech_advice = rag.retrieve_tech_recommendations("database", "PostgreSQL vs MySQL")
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize RAG system

        Args:
            base_path: Path to ARES knowledge base directory
        """
        if base_path is None:
            # Default to current location
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)

        # Knowledge base file paths
        self.patterns_file = self.base_path / "proven-patterns.md"
        self.tech_matrix_file = self.base_path / "tech-success-matrix.md"
        self.decision_file = self.base_path / "decision-causality.md"

        # Loaded knowledge
        self.knowledge_chunks: List[KnowledgeChunk] = []
        self.loaded = False

    def load_knowledge_base(self) -> bool:
        """
        Load all knowledge base files

        Returns:
            True if loaded successfully
        """
        try:
            self.knowledge_chunks = []

            # Load proven patterns
            if self.patterns_file.exists():
                self._load_patterns()

            # Load tech matrix
            if self.tech_matrix_file.exists():
                self._load_tech_matrix()

            # Load decision causality
            if self.decision_file.exists():
                self._load_decisions()

            self.loaded = True
            return True

        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            return False

    def retrieve_patterns(
        self,
        domain: str,
        query: str,
        top_k: int = 3,
        tier_filter: Optional[List[str]] = None
    ) -> List[KnowledgeChunk]:
        """
        Retrieve relevant patterns for a task

        Args:
            domain: Domain (frontend, backend, database, etc.)
            query: Task description or query
            top_k: Number of top patterns to return
            tier_filter: Filter by tiers (e.g., ['tier_1', 'tier_2'])

        Returns:
            List of relevant pattern chunks
        """
        if not self.loaded:
            self.load_knowledge_base()

        # Filter to patterns
        pattern_chunks = [
            c for c in self.knowledge_chunks
            if c.chunk_type in ['pattern', 'anti_pattern']
        ]

        # Apply tier filter
        if tier_filter:
            pattern_chunks = [
                c for c in pattern_chunks
                if c.tier in tier_filter
            ]

        # Score relevance
        scored_chunks = []
        for chunk in pattern_chunks:
            score = self._calculate_relevance(chunk, domain, query)
            chunk.relevance_score = score
            scored_chunks.append(chunk)

        # Sort by relevance and return top k
        scored_chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        return scored_chunks[:top_k]

    def retrieve_tech_recommendations(
        self,
        domain: str,
        query: str,
        top_k: int = 3
    ) -> List[KnowledgeChunk]:
        """
        Retrieve technology recommendations

        Args:
            domain: Domain (database, language, framework, etc.)
            query: Technology question or query
            top_k: Number of recommendations

        Returns:
            List of tech recommendation chunks
        """
        if not self.loaded:
            self.load_knowledge_base()

        # Filter to tech matrix chunks
        tech_chunks = [
            c for c in self.knowledge_chunks
            if c.chunk_type == 'tech_matrix'
        ]

        # Score and sort
        scored_chunks = []
        for chunk in tech_chunks:
            score = self._calculate_relevance(chunk, domain, query)
            chunk.relevance_score = score
            scored_chunks.append(chunk)

        scored_chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        return scored_chunks[:top_k]

    def retrieve_decisions(
        self,
        domain: str,
        query: str,
        top_k: int = 3
    ) -> List[KnowledgeChunk]:
        """
        Retrieve past decision history

        Args:
            domain: Domain of decision
            query: Decision question or context
            top_k: Number of decisions to return

        Returns:
            List of decision chunks
        """
        if not self.loaded:
            self.load_knowledge_base()

        decision_chunks = [
            c for c in self.knowledge_chunks
            if c.chunk_type == 'decision'
        ]

        scored_chunks = []
        for chunk in decision_chunks:
            score = self._calculate_relevance(chunk, domain, query)
            chunk.relevance_score = score
            scored_chunks.append(chunk)

        scored_chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        return scored_chunks[:top_k]

    def retrieve_anti_patterns(
        self,
        domain: str,
        query: str,
        top_k: int = 3
    ) -> List[KnowledgeChunk]:
        """
        Retrieve anti-patterns to avoid

        Args:
            domain: Domain
            query: Context or query
            top_k: Number of anti-patterns

        Returns:
            List of anti-pattern chunks
        """
        if not self.loaded:
            self.load_knowledge_base()

        anti_pattern_chunks = [
            c for c in self.knowledge_chunks
            if c.chunk_type == 'anti_pattern'
        ]

        scored_chunks = []
        for chunk in anti_pattern_chunks:
            score = self._calculate_relevance(chunk, domain, query)
            chunk.relevance_score = score
            scored_chunks.append(chunk)

        scored_chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        return scored_chunks[:top_k]

    def get_comprehensive_context(
        self,
        domain: str,
        query: str,
        include_patterns: int = 2,
        include_tech: int = 2,
        include_decisions: int = 1,
        include_anti_patterns: int = 1
    ) -> str:
        """
        Get comprehensive context including all knowledge types

        Args:
            domain: Domain
            query: Task or question
            include_patterns: Number of patterns to include
            include_tech: Number of tech recommendations
            include_decisions: Number of past decisions
            include_anti_patterns: Number of anti-patterns

        Returns:
            Formatted context string
        """
        context_parts = []

        # Retrieve all knowledge types
        patterns = self.retrieve_patterns(domain, query, top_k=include_patterns)
        tech = self.retrieve_tech_recommendations(domain, query, top_k=include_tech)
        decisions = self.retrieve_decisions(domain, query, top_k=include_decisions)
        anti_patterns = self.retrieve_anti_patterns(domain, query, top_k=include_anti_patterns)

        # Format patterns
        if patterns:
            context_parts.append("## RELEVANT PATTERNS FROM KNOWLEDGE BASE\n")
            for i, pattern in enumerate(patterns, 1):
                tier_info = f" ({pattern.tier.upper()})" if pattern.tier else ""
                context_parts.append(f"### Pattern {i}{tier_info}")
                context_parts.append(pattern.content)
                context_parts.append("")

        # Format tech recommendations
        if tech:
            context_parts.append("## TECHNOLOGY RECOMMENDATIONS\n")
            for i, tech_chunk in enumerate(tech, 1):
                context_parts.append(f"### Recommendation {i}")
                context_parts.append(tech_chunk.content)
                context_parts.append("")

        # Format past decisions
        if decisions:
            context_parts.append("## PAST DECISION HISTORY\n")
            for i, decision in enumerate(decisions, 1):
                context_parts.append(f"### Related Decision {i}")
                context_parts.append(decision.content)
                context_parts.append("")

        # Format anti-patterns
        if anti_patterns:
            context_parts.append("## ANTI-PATTERNS TO AVOID\n")
            for i, anti_pattern in enumerate(anti_patterns, 1):
                context_parts.append(f"### Anti-Pattern {i}")
                context_parts.append(anti_pattern.content)
                context_parts.append("")

        return "\n".join(context_parts)

    # Private methods

    def _load_patterns(self) -> None:
        """Load patterns from proven-patterns.md"""
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split into sections by ## headers
            sections = re.split(r'\n## ', content)

            for section in sections:
                # Detect tier (⭐⭐⭐ TIER 1, etc.)
                tier = None
                if 'TIER 1' in section or '⭐⭐⭐' in section:
                    tier = 'tier_1'
                elif 'TIER 2' in section or '⭐⭐' in section:
                    tier = 'tier_2'
                elif 'TIER 3' in section or '⭐' in section:
                    tier = 'tier_3'

                # Detect anti-patterns
                chunk_type = 'anti_pattern' if '❌ Anti-Pattern' in section else 'pattern'

                # Create chunk (limit to reasonable size)
                if len(section) > 100:  # Skip very small sections
                    chunk = KnowledgeChunk(
                        content=section[:2000],  # Limit chunk size
                        source_file='proven-patterns.md',
                        chunk_type=chunk_type,
                        tier=tier,
                        metadata={'full_content_available': len(section) > 2000}
                    )
                    self.knowledge_chunks.append(chunk)

        except Exception as e:
            print(f"Error loading patterns: {e}")

    def _load_tech_matrix(self) -> None:
        """Load tech matrix from tech-success-matrix.md"""
        try:
            with open(self.tech_matrix_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by ## headers
            sections = re.split(r'\n## ', content)

            for section in sections:
                if len(section) > 100:
                    chunk = KnowledgeChunk(
                        content=section[:2000],
                        source_file='tech-success-matrix.md',
                        chunk_type='tech_matrix',
                        metadata=self._extract_tech_metadata(section)
                    )
                    self.knowledge_chunks.append(chunk)

        except Exception as e:
            print(f"Error loading tech matrix: {e}")

    def _load_decisions(self) -> None:
        """Load decisions from decision-causality.md"""
        try:
            with open(self.decision_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by ### headers (decisions)
            sections = re.split(r'\n### ', content)

            for section in sections:
                if len(section) > 100:
                    chunk = KnowledgeChunk(
                        content=section[:2000],
                        source_file='decision-causality.md',
                        chunk_type='decision'
                    )
                    self.knowledge_chunks.append(chunk)

        except Exception as e:
            print(f"Error loading decisions: {e}")

    def _extract_tech_metadata(self, content: str) -> Dict[str, any]:
        """Extract metadata from tech matrix section"""
        metadata = {}

        # Extract success rate
        success_match = re.search(r'Success Rate:\s*(\d+)%', content)
        if success_match:
            metadata['success_rate'] = int(success_match.group(1))

        # Extract usage info
        usage_match = re.search(r'Usage:\s*(.+)', content)
        if usage_match:
            metadata['usage'] = usage_match.group(1).strip()

        return metadata

    def _calculate_relevance(
        self,
        chunk: KnowledgeChunk,
        domain: str,
        query: str
    ) -> float:
        """
        Calculate relevance score for chunk

        Simple keyword matching. In production, use embeddings and cosine similarity.

        Args:
            chunk: Knowledge chunk
            domain: Domain string
            query: Query string

        Returns:
            Relevance score (0-1)
        """
        content_lower = chunk.content.lower()
        domain_lower = domain.lower()
        query_lower = query.lower()

        # Extract keywords from query
        query_keywords = set(re.findall(r'\w+', query_lower))

        # Scoring factors
        score = 0.0

        # Domain match (high weight)
        if domain_lower in content_lower:
            score += 0.4

        # Keyword overlap
        content_keywords = set(re.findall(r'\w+', content_lower))
        overlap = len(query_keywords & content_keywords)
        if query_keywords:
            overlap_ratio = overlap / len(query_keywords)
            score += 0.4 * overlap_ratio

        # Tier bonus (Tier 1 patterns preferred)
        if chunk.tier == 'tier_1':
            score += 0.2
        elif chunk.tier == 'tier_2':
            score += 0.1

        # Success rate bonus (for tech matrix)
        if 'success_rate' in chunk.metadata:
            success_rate = chunk.metadata['success_rate']
            score += 0.1 * (success_rate / 100)

        return min(1.0, score)  # Cap at 1.0


def create_rag(base_path: Optional[Path] = None) -> KnowledgeBaseRAG:
    """
    Create RAG instance

    Args:
        base_path: Path to knowledge base directory

    Returns:
        KnowledgeBaseRAG instance
    """
    rag = KnowledgeBaseRAG(base_path)
    rag.load_knowledge_base()
    return rag
