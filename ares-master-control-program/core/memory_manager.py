"""
ARES Agent Lifecycle System - Memory Manager
Loads and manages agent memory (episodic, semantic, procedural)

Responsibilities:
- Load similar past tasks (episodic memory)
- Query relevant knowledge (semantic memory)
- Access learned skills (procedural memory)
- Format memory for agent context injection
"""

import json
import yaml
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class EpisodicMemory:
    """A single episodic memory (past task execution)"""
    task_id: str
    timestamp: datetime
    task_description: str
    execution_time_seconds: float
    success: bool
    patterns_used: List[str]
    reflection_text: str
    reflection_depth: str  # 'shallow' or 'deep'
    correction_made: bool
    user_rating: Optional[float] = None
    similarity_score: float = 0.0  # How similar to current task


@dataclass
class SemanticKnowledge:
    """Knowledge from semantic memory"""
    knowledge_id: str
    content: str
    source: str  # 'learned', 'configured', 'external'
    confidence: float
    last_validated: datetime


@dataclass
class ProceduralSkill:
    """A learned skill or workflow"""
    skill_id: str
    name: str
    description: str
    success_count: int
    total_uses: int
    effectiveness: float  # success_count / total_uses
    template: Optional[str] = None


@dataclass
class MemoryContext:
    """Complete memory context for agent execution"""
    episodic_memories: List[EpisodicMemory]
    semantic_knowledge: List[SemanticKnowledge]
    procedural_skills: List[ProceduralSkill]
    total_token_count: int = 0

    def to_prompt_text(self, max_tokens: int = 2000) -> str:
        """
        Format memory context for injection into agent prompt

        Args:
            max_tokens: Maximum tokens to include

        Returns:
            Formatted prompt text
        """
        sections = []

        # Episodic Memory Section
        if self.episodic_memories:
            sections.append("## Past Experience (Similar Tasks)\n")
            for i, mem in enumerate(self.episodic_memories[:5], 1):
                outcome = "✓ Success" if mem.success else "✗ Failed"
                corrected = " (self-corrected)" if mem.correction_made else ""
                sections.append(
                    f"**Task {i}** ({mem.timestamp.strftime('%Y-%m-%d')}): {mem.task_description}\n"
                    f"- Outcome: {outcome}{corrected}\n"
                    f"- Time: {mem.execution_time_seconds:.0f}s\n"
                    f"- Patterns: {', '.join(mem.patterns_used)}\n"
                    f"- Reflection: {mem.reflection_text[:200]}...\n"
                )

        # Semantic Knowledge Section
        if self.semantic_knowledge:
            sections.append("\n## Relevant Knowledge\n")
            for know in self.semantic_knowledge[:10]:
                sections.append(
                    f"- **{know.knowledge_id}**: {know.content} "
                    f"(confidence: {know.confidence:.0f}%)\n"
                )

        # Procedural Skills Section
        if self.procedural_skills:
            sections.append("\n## Learned Skills\n")
            for skill in self.procedural_skills[:5]:
                sections.append(
                    f"- **{skill.name}**: {skill.description} "
                    f"(effectiveness: {skill.effectiveness:.0f}%, used {skill.total_uses}x)\n"
                )
                if skill.template:
                    sections.append(f"  Template: {skill.template[:100]}...\n")

        full_text = "".join(sections)

        # Rough token estimation (1 token ≈ 4 characters)
        estimated_tokens = len(full_text) // 4

        # If exceeds max, truncate
        if estimated_tokens > max_tokens:
            char_limit = max_tokens * 4
            full_text = full_text[:char_limit] + "\n\n[Memory truncated to fit context limit]"

        return full_text


class MemoryManager:
    """
    Manages agent memory loading and storage

    Memory Types:
    - Episodic: SQLite database with task execution history
    - Semantic: JSON with facts, concepts, principles
    - Procedural: YAML with skills, workflows, templates
    """

    def __init__(self, agent_id: str, agents_dir: Optional[Path] = None):
        """
        Initialize memory manager

        Args:
            agent_id: Agent identifier
            agents_dir: Path to agents directory
        """
        self.agent_id = agent_id
        self.project_root = Path(__file__).parent.parent
        self.agents_dir = agents_dir or self.project_root / "agents"
        self.agent_dir = self.agents_dir / agent_id
        self.memory_dir = self.agent_dir / "memory"

        # Memory file paths
        self.episodic_db = self.memory_dir / "episodic.db"
        self.semantic_json = self.memory_dir / "semantic.json"
        self.procedural_yaml = self.memory_dir / "procedural.yaml"

    def load_context(
        self,
        task_description: str,
        episodic_limit: int = 5,
        semantic_limit: int = 10,
        max_context_tokens: int = 2000
    ) -> MemoryContext:
        """
        Load complete memory context for task execution

        Args:
            task_description: Current task description
            episodic_limit: Max episodic memories to load
            semantic_limit: Max semantic knowledge items
            max_context_tokens: Maximum tokens for context

        Returns:
            MemoryContext with all loaded memories
        """
        episodic = self._load_episodic_memories(task_description, episodic_limit)
        semantic = self._load_semantic_knowledge(task_description, semantic_limit)
        procedural = self._load_procedural_skills()

        context = MemoryContext(
            episodic_memories=episodic,
            semantic_knowledge=semantic,
            procedural_skills=procedural
        )

        return context

    def _load_episodic_memories(
        self,
        task_description: str,
        limit: int
    ) -> List[EpisodicMemory]:
        """
        Load similar past tasks from episodic memory

        Uses SQLite FTS (full-text search) for similarity matching

        Args:
            task_description: Current task
            limit: Max memories to return

        Returns:
            List of similar episodic memories
        """
        if not self.episodic_db.exists():
            return []

        memories = []

        try:
            conn = sqlite3.connect(self.episodic_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Full-text search query
            # Extract keywords from task description
            keywords = self._extract_keywords(task_description)
            search_query = " ".join(keywords[:5])  # Top 5 keywords

            # Query using FTS
            cursor.execute("""
                SELECT
                    em.*,
                    fts.rank as similarity
                FROM episodic_memory em
                JOIN episodic_memory_fts fts ON em.task_id = fts.task_id
                WHERE episodic_memory_fts MATCH ?
                ORDER BY similarity DESC
                LIMIT ?
            """, (search_query, limit))

            rows = cursor.fetchall()

            for row in rows:
                memories.append(EpisodicMemory(
                    task_id=row['task_id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    task_description=row['task_description'],
                    execution_time_seconds=row['execution_time_seconds'] or 0.0,
                    success=bool(row['success']),
                    patterns_used=json.loads(row['patterns_used']) if row['patterns_used'] else [],
                    reflection_text=row['reflection_text'] or "",
                    reflection_depth=row['reflection_depth'] or 'shallow',
                    correction_made=bool(row['correction_made']),
                    user_rating=row['user_rating'],
                    similarity_score=abs(row['similarity'])  # FTS rank (negative, so abs)
                ))

            conn.close()

        except Exception as e:
            print(f"Warning: Could not load episodic memories: {e}")

        return memories

    def _load_semantic_knowledge(
        self,
        task_description: str,
        limit: int
    ) -> List[SemanticKnowledge]:
        """
        Load relevant knowledge from semantic memory

        Args:
            task_description: Current task
            limit: Max knowledge items

        Returns:
            List of relevant semantic knowledge
        """
        if not self.semantic_json.exists():
            return []

        knowledge_items = []

        try:
            with open(self.semantic_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Simple keyword matching (Phase 2 - no vector embeddings yet)
            task_keywords = set(self._extract_keywords(task_description))

            for item in data.get('knowledge_items', []):
                # Calculate simple overlap score
                item_text = f"{item['title']} {item['content']}".lower()
                item_keywords = set(self._extract_keywords(item_text))
                overlap = len(task_keywords & item_keywords)

                if overlap > 0:
                    knowledge_items.append((overlap, item))

            # Sort by overlap (descending) and take top N
            knowledge_items.sort(key=lambda x: x[0], reverse=True)

            result = []
            for _, item in knowledge_items[:limit]:
                result.append(SemanticKnowledge(
                    knowledge_id=item['id'],
                    content=f"{item['title']}: {item['content']}",
                    source=item.get('source', 'unknown'),
                    confidence=item.get('confidence', 50.0),
                    last_validated=datetime.fromisoformat(item['last_updated'])
                ))

            return result

        except Exception as e:
            print(f"Warning: Could not load semantic knowledge: {e}")
            return []

    def _load_procedural_skills(self) -> List[ProceduralSkill]:
        """
        Load learned skills and workflows

        Returns:
            List of procedural skills
        """
        if not self.procedural_yaml.exists():
            return []

        skills = []

        try:
            with open(self.procedural_yaml, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            for skill in data.get('skills', []):
                success = skill.get('success_count', 0)
                total = skill.get('total_uses', 1)
                effectiveness = (success / total * 100) if total > 0 else 0.0

                skills.append(ProceduralSkill(
                    skill_id=skill['id'],
                    name=skill['name'],
                    description=skill['description'],
                    success_count=success,
                    total_uses=total,
                    effectiveness=effectiveness,
                    template=skill.get('template')
                ))

            # Sort by effectiveness
            skills.sort(key=lambda s: s.effectiveness, reverse=True)

            return skills

        except Exception as e:
            print(f"Warning: Could not load procedural skills: {e}")
            return []

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for similarity matching

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        import re

        # Lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())

        # Remove stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }

        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        return keywords

    def store_task_execution(
        self,
        task_id: str,
        task_description: str,
        execution_time_seconds: float,
        success: bool,
        patterns_used: List[str],
        reflection_text: str,
        reflection_depth: str,
        correction_made: bool,
        user_rating: Optional[float] = None,
        intermediate_steps: Optional[List[Dict]] = None
    ) -> bool:
        """
        Store task execution in episodic memory

        Args:
            task_id: Unique task identifier
            task_description: Task description
            execution_time_seconds: How long it took
            success: Whether task succeeded
            patterns_used: Which patterns were applied
            reflection_text: Self-reflection on execution
            reflection_depth: 'shallow' or 'deep'
            correction_made: Whether agent self-corrected
            user_rating: Optional user feedback rating
            intermediate_steps: Optional detailed execution steps

        Returns:
            True if stored successfully
        """
        if not self.episodic_db.exists():
            print(f"Warning: Episodic database not found: {self.episodic_db}")
            return False

        try:
            conn = sqlite3.connect(self.episodic_db)
            cursor = conn.cursor()

            # Insert into main table (intermediate_steps stored as JSON)
            cursor.execute("""
                INSERT INTO episodic_memory (
                    task_id, timestamp, task_description, execution_time_seconds,
                    success, patterns_used, reflection_text, reflection_depth,
                    correction_made, user_rating, intermediate_steps
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                datetime.now().isoformat(),
                task_description,
                execution_time_seconds,
                1 if success else 0,
                json.dumps(patterns_used),
                reflection_text,
                reflection_depth,
                1 if correction_made else 0,
                user_rating,
                json.dumps(intermediate_steps) if intermediate_steps else None
            ))

            # FTS index is auto-updated by trigger

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"Error storing task execution: {e}")
            return False

    def update_semantic_knowledge(
        self,
        knowledge_id: str,
        title: str,
        content: str,
        source: str = 'learned',
        confidence: float = 80.0
    ) -> bool:
        """
        Add or update semantic knowledge

        Args:
            knowledge_id: Unique knowledge identifier
            title: Knowledge title
            content: Knowledge content
            source: Source ('learned', 'configured', 'external')
            confidence: Confidence in this knowledge (0-100)

        Returns:
            True if updated successfully
        """
        if not self.semantic_json.exists():
            return False

        try:
            with open(self.semantic_json, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if exists
            existing_idx = None
            for idx, item in enumerate(data.get('knowledge_items', [])):
                if item['id'] == knowledge_id:
                    existing_idx = idx
                    break

            new_item = {
                'id': knowledge_id,
                'title': title,
                'content': content,
                'source': source,
                'confidence': confidence,
                'last_updated': datetime.now().isoformat()
            }

            if existing_idx is not None:
                data['knowledge_items'][existing_idx] = new_item
            else:
                data['knowledge_items'].append(new_item)

            # Update metadata
            data['last_updated'] = datetime.now().isoformat()
            data['total_items'] = len(data['knowledge_items'])

            with open(self.semantic_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error updating semantic knowledge: {e}")
            return False

    def update_procedural_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        success: bool,
        template: Optional[str] = None
    ) -> bool:
        """
        Update procedural skill based on usage

        Args:
            skill_id: Skill identifier
            name: Skill name
            description: What this skill does
            success: Whether this use was successful
            template: Optional template text

        Returns:
            True if updated successfully
        """
        if not self.procedural_yaml.exists():
            return False

        try:
            with open(self.procedural_yaml, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Find existing skill
            existing_idx = None
            for idx, skill in enumerate(data.get('skills', [])):
                if skill['id'] == skill_id:
                    existing_idx = idx
                    break

            if existing_idx is not None:
                # Update existing
                skill = data['skills'][existing_idx]
                skill['total_uses'] += 1
                if success:
                    skill['success_count'] += 1
                skill['last_used'] = datetime.now().isoformat()
                if template:
                    skill['template'] = template
            else:
                # Create new
                data['skills'].append({
                    'id': skill_id,
                    'name': name,
                    'description': description,
                    'success_count': 1 if success else 0,
                    'total_uses': 1,
                    'template': template,
                    'created': datetime.now().isoformat(),
                    'last_used': datetime.now().isoformat()
                })

            # Update metadata
            data['last_updated'] = datetime.now().isoformat()

            with open(self.procedural_yaml, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

            return True

        except Exception as e:
            print(f"Error updating procedural skill: {e}")
            return False


def load_memory_context(agent_id: str, task_description: str) -> MemoryContext:
    """
    Convenience function to load memory context for an agent

    Args:
        agent_id: Agent identifier
        task_description: Current task

    Returns:
        MemoryContext with loaded memories
    """
    manager = MemoryManager(agent_id)
    return manager.load_context(task_description)
