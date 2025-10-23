"""
Database schema for Business Brain
Stores discovered workflows, automation suggestions, and learning data
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiosqlite

DATABASE_PATH = Path(__file__).parent.parent / "data" / "business_brain.db"


class Database:
    """Async database manager for Business Brain"""

    def __init__(self, db_path: str = str(DATABASE_PATH)):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Create all necessary tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Discovered workflows table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS discovered_workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_type TEXT NOT NULL,
                    pattern_description TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    frequency TEXT,
                    example_data TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'discovered'
                )
            """)

            # Automation suggestions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS automation_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id INTEGER,
                    suggestion_title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    estimated_time_saved_hours REAL,
                    estimated_cost_saved REAL,
                    implementation_complexity TEXT,
                    suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (workflow_id) REFERENCES discovered_workflows (id)
                )
            """)

            # Active agents table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS active_agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    configuration TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_run TIMESTAMP,
                    total_executions INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0
                )
            """)

            # Agent execution logs
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id INTEGER,
                    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action_taken TEXT,
                    success BOOLEAN,
                    time_saved_minutes REAL,
                    details TEXT,
                    FOREIGN KEY (agent_id) REFERENCES active_agents (id)
                )
            """)

            # Business metrics
            await db.execute("""
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_date DATE NOT NULL,
                    total_time_saved_hours REAL DEFAULT 0.0,
                    total_cost_saved REAL DEFAULT 0.0,
                    active_automations INTEGER DEFAULT 0,
                    workflows_discovered INTEGER DEFAULT 0,
                    agent_executions INTEGER DEFAULT 0
                )
            """)

            # Email patterns (for learning)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS email_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    sender_domain TEXT,
                    subject_pattern TEXT,
                    body_keywords TEXT,
                    typical_response TEXT,
                    frequency_per_week REAL,
                    avg_response_time_hours REAL,
                    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def add_discovered_workflow(self, workflow_type: str, description: str,
                                     confidence: float, frequency: str,
                                     example_data: Dict) -> int:
        """Add a newly discovered workflow pattern"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO discovered_workflows
                (workflow_type, pattern_description, confidence_score, frequency, example_data)
                VALUES (?, ?, ?, ?, ?)
            """, (workflow_type, description, confidence, frequency, json.dumps(example_data)))
            await db.commit()
            return cursor.lastrowid

    async def add_automation_suggestion(self, workflow_id: int, title: str,
                                       description: str, time_saved: float,
                                       cost_saved: float, complexity: str) -> int:
        """Add an automation suggestion for a workflow"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO automation_suggestions
                (workflow_id, suggestion_title, description, estimated_time_saved_hours,
                 estimated_cost_saved, implementation_complexity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (workflow_id, title, description, time_saved, cost_saved, complexity))
            await db.commit()
            return cursor.lastrowid

    async def create_agent(self, name: str, agent_type: str,
                          config: Dict) -> int:
        """Register a new agent"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO active_agents (agent_name, agent_type, configuration)
                VALUES (?, ?, ?)
            """, (name, agent_type, json.dumps(config)))
            await db.commit()
            return cursor.lastrowid

    async def log_agent_execution(self, agent_id: int, action: str,
                                  success: bool, time_saved: float,
                                  details: Dict):
        """Log an agent execution"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO agent_logs
                (agent_id, action_taken, success, time_saved_minutes, details)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_id, action, success, time_saved, json.dumps(details)))

            # Update agent stats
            await db.execute("""
                UPDATE active_agents
                SET last_run = CURRENT_TIMESTAMP,
                    total_executions = total_executions + 1
                WHERE id = ?
            """, (agent_id,))

            await db.commit()

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get stats for dashboard display"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get workflow counts
            cursor = await db.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'discovered' THEN 1 ELSE 0 END) as new
                FROM discovered_workflows
            """)
            workflows = await cursor.fetchone()

            # Get automation suggestions
            cursor = await db.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                       SUM(estimated_time_saved_hours) as total_time_potential,
                       SUM(estimated_cost_saved) as total_cost_potential
                FROM automation_suggestions
            """)
            suggestions = await cursor.fetchone()

            # Get agent stats
            cursor = await db.execute("""
                SELECT COUNT(*) as total,
                       SUM(total_executions) as total_runs
                FROM active_agents WHERE status = 'active'
            """)
            agents = await cursor.fetchone()

            # Get actual time saved from logs
            cursor = await db.execute("""
                SELECT SUM(time_saved_minutes) / 60.0 as hours_saved
                FROM agent_logs WHERE success = 1
            """)
            savings = await cursor.fetchone()

            return {
                "workflows_discovered": workflows["total"] if workflows else 0,
                "new_workflows": workflows["new"] if workflows else 0,
                "suggestions_total": suggestions["total"] if suggestions else 0,
                "suggestions_pending": suggestions["pending"] if suggestions else 0,
                "potential_time_savings": suggestions["total_time_potential"] or 0,
                "potential_cost_savings": suggestions["total_cost_potential"] or 0,
                "active_agents": agents["total"] if agents else 0,
                "agent_executions": agents["total_runs"] if agents else 0,
                "actual_hours_saved": savings["hours_saved"] or 0
            }

    async def get_recent_workflows(self, limit: int = 10) -> List[Dict]:
        """Get recently discovered workflows"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM discovered_workflows
                ORDER BY discovered_at DESC LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_suggestions_for_workflow(self, workflow_id: int) -> List[Dict]:
        """Get automation suggestions for a specific workflow"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM automation_suggestions
                WHERE workflow_id = ?
                ORDER BY estimated_time_saved_hours DESC
            """, (workflow_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
