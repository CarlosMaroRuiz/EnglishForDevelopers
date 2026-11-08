"""SQLite persistence layer.

Refactored from the original ``services/database.py``:

* connections are always closed via a context manager (no leaked handles),
* rows are returned as ``dict`` (``sqlite3.Row`` -> ``dict``) for clean access,
* the schema is unchanged so existing databases keep working.
"""
import json
import sqlite3
from contextlib import contextmanager


class DatabaseService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------ setup
    def init_db(self):
        with self._connection() as conn:
            c = conn.cursor()

            c.execute("""CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                corrections TEXT,
                scenario TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS grammar_mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                corrected_text TEXT NOT NULL,
                mistake_type TEXT NOT NULL,
                explanation TEXT,
                conversation_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                definition TEXT NOT NULL,
                example TEXT,
                category TEXT DEFAULT 'technical',
                difficulty_level INTEGER DEFAULT 1,
                times_encountered INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_area TEXT NOT NULL,
                current_level INTEGER DEFAULT 1,
                mistakes_count INTEGER DEFAULT 0,
                improvements_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_type TEXT NOT NULL,
                content TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_type TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                incorrect_answers INTEGER NOT NULL,
                score_percentage REAL NOT NULL,
                focused_areas TEXT,
                detailed_results TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT NOT NULL,
                grammar_category TEXT NOT NULL,
                difficulty_level INTEGER DEFAULT 1,
                based_on_user_mistake BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                content TEXT NOT NULL,
                story_type TEXT DEFAULT 'generated',
                scenario TEXT DEFAULT 'general',
                difficulty_level TEXT DEFAULT 'intermediate',
                topic TEXT DEFAULT 'software_development',
                estimated_time INTEGER DEFAULT 10,
                total_steps INTEGER DEFAULT 1,
                learning_objectives TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS story_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                step_type TEXT DEFAULT 'narrative',
                content TEXT NOT NULL,
                question TEXT,
                expected_response_type TEXT DEFAULT 'open',
                learning_focus TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS user_story_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                current_step INTEGER DEFAULT 1,
                is_completed BOOLEAN DEFAULT FALSE,
                total_interactions INTEGER DEFAULT 0,
                completion_percentage REAL DEFAULT 0.0,
                time_spent INTEGER DEFAULT 0,
                last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS story_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                user_response TEXT NOT NULL,
                ai_feedback TEXT,
                corrections TEXT,
                new_vocabulary TEXT,
                interaction_score REAL DEFAULT 0.0,
                response_time INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories (id)
            )""")

            c.execute("""CREATE TABLE IF NOT EXISTS story_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                scenario TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                template_structure TEXT NOT NULL,
                variables TEXT,
                learning_objectives TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )""")

            self._insert_default_story_templates(c)

    def _insert_default_story_templates(self, cursor):
        default_templates = [
            {
                "name": "Bug Hunt Adventure",
                "scenario": "debugging_session",
                "difficulty_level": "intermediate",
                "template_structure": json.dumps({
                    "intro": "A critical bug has been discovered in production...",
                    "steps": [
                        {"type": "narrative", "content": "Describe the bug symptoms"},
                        {"type": "question", "content": "What would be your first debugging step?"},
                        {"type": "narrative", "content": "Investigation process"},
                        {"type": "question", "content": "How would you communicate this to stakeholders?"},
                        {"type": "resolution", "content": "Bug resolution and lessons learned"},
                    ],
                }),
                "variables": json.dumps(["bug_type", "system_component", "urgency_level"]),
                "learning_objectives": json.dumps(["technical vocabulary", "problem-solving communication", "stakeholder updates"]),
            },
            {
                "name": "Code Review Drama",
                "scenario": "code_review",
                "difficulty_level": "advanced",
                "template_structure": json.dumps({
                    "intro": "You need to review a complex pull request...",
                    "steps": [
                        {"type": "narrative", "content": "Analyzing the code changes"},
                        {"type": "question", "content": "How would you provide constructive feedback?"},
                        {"type": "dialogue", "content": "Discussion with the developer"},
                        {"type": "question", "content": "How do you handle disagreements?"},
                        {"type": "conclusion", "content": "Reaching consensus and approval"},
                    ],
                }),
                "variables": json.dumps(["code_complexity", "team_member", "review_type"]),
                "learning_objectives": json.dumps(["diplomatic language", "technical feedback", "conflict resolution"]),
            },
            {
                "name": "Interview Challenge",
                "scenario": "technical_interview",
                "difficulty_level": "beginner",
                "template_structure": json.dumps({
                    "intro": "You are interviewing for a software developer position...",
                    "steps": [
                        {"type": "question", "content": "Tell me about yourself"},
                        {"type": "technical", "content": "Explain a technical concept"},
                        {"type": "behavioral", "content": "Describe a challenging project"},
                        {"type": "scenario", "content": "How would you handle a difficult situation?"},
                        {"type": "closing", "content": "Questions for the interviewer"},
                    ],
                }),
                "variables": json.dumps(["company_type", "position_level", "technology_stack"]),
                "learning_objectives": json.dumps(["self-presentation", "technical explanations", "question asking"]),
            },
        ]

        for template in default_templates:
            cursor.execute(
                """INSERT OR IGNORE INTO story_templates
                   (name, scenario, difficulty_level, template_structure, variables, learning_objectives)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    template["name"],
                    template["scenario"],
                    template["difficulty_level"],
                    template["template_structure"],
                    template["variables"],
                    template["learning_objectives"],
                ),
            )

    # ------------------------------------------------------------ conversations
    def save_conversation(self, user_message, ai_response, corrections, scenario) -> int:
        corrections = corrections or []
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO conversations (user_message, ai_response, corrections, scenario)
                   VALUES (?, ?, ?, ?)""",
                (user_message, ai_response, json.dumps(corrections), scenario),
            )
            conversation_id = c.lastrowid

            for correction in corrections:
                c.execute(
                    """INSERT INTO grammar_mistakes
                       (original_text, corrected_text, mistake_type, explanation, conversation_id)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        correction.get("original", ""),
                        correction.get("corrected", ""),
                        correction.get("type", ""),
                        correction.get("explanation", ""),
                        conversation_id,
                    ),
                )
            return conversation_id

    def save_vocabulary(self, vocabulary_list):
        vocabulary_list = vocabulary_list or []
        with self._connection() as conn:
            c = conn.cursor()
            for vocab in vocabulary_list:
                word = vocab.get("word", "")
                c.execute(
                    """INSERT OR IGNORE INTO vocabulary (word, definition, example)
                       VALUES (?, ?, ?)""",
                    (word, vocab.get("definition", ""), vocab.get("example", "")),
                )
                c.execute(
                    """UPDATE vocabulary SET times_encountered = times_encountered + 1
                       WHERE word = ?""",
                    (word,),
                )

    # ------------------------------------------------------------------- quiz
    def save_quiz_result(self, quiz_type, total_questions, correct_answers, detailed_results, focused_areas):
        total = int(total_questions)
        correct = int(correct_answers)
        incorrect = total - correct
        score = (correct / total * 100) if total > 0 else 0
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO quiz_results
                   (quiz_type, total_questions, correct_answers, incorrect_answers,
                    score_percentage, focused_areas, detailed_results)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    quiz_type,
                    total,
                    correct,
                    incorrect,
                    score,
                    json.dumps(focused_areas),
                    json.dumps(detailed_results),
                ),
            )

    def save_quiz_questions(self, questions):
        questions = questions or []
        with self._connection() as conn:
            c = conn.cursor()
            for q in questions:
                c.execute(
                    """INSERT INTO quiz_questions
                       (question_text, option_a, option_b, option_c, correct_answer,
                        explanation, grammar_category, based_on_user_mistake)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        q.get("question", ""),
                        q.get("option_a", ""),
                        q.get("option_b", ""),
                        q.get("option_c", ""),
                        q.get("correct_answer", "a"),
                        q.get("explanation", ""),
                        q.get("category", "general"),
                        True,
                    ),
                )

    # ----------------------------------------------------------------- stories
    def save_story(self, title, description, content, story_type="generated", scenario="general",
                   difficulty_level="intermediate", topic="software_development", estimated_time=10,
                   learning_objectives=None) -> int:
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO stories
                   (title, description, content, story_type, scenario, difficulty_level,
                    topic, estimated_time, learning_objectives)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    description,
                    content,
                    story_type,
                    scenario,
                    difficulty_level,
                    topic,
                    estimated_time,
                    json.dumps(learning_objectives) if learning_objectives else None,
                ),
            )
            return c.lastrowid

    def save_story_steps(self, story_id, steps):
        steps = steps or []
        with self._connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM story_steps WHERE story_id = ?", (story_id,))

            for i, step in enumerate(steps, 1):
                step_number = step.get("step_number", i)
                step_type = step.get("type", "narrative")
                content = step.get("content", "")
                question = step.get("question")
                expected_response_type = step.get("expected_response_type", "open")
                learning_focus = step.get("learning_focus", "communication_skills")

                if not content or len(content.strip()) < 5:
                    content = f"Continue with step {step_number}..."

                c.execute(
                    """INSERT INTO story_steps
                       (story_id, step_number, step_type, content, question,
                        expected_response_type, learning_focus)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (story_id, step_number, step_type, content, question,
                     expected_response_type, learning_focus),
                )

            c.execute("UPDATE stories SET total_steps = ? WHERE id = ?", (len(steps), story_id))

    def get_stories_list(self, limit=20):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT id, title, description, scenario, difficulty_level, topic,
                          estimated_time, total_steps, created_at
                   FROM stories
                   WHERE is_active = TRUE
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,),
            )
            return [dict(row) for row in c.fetchall()]

    def get_story_by_id(self, story_id):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM stories WHERE id = ? AND is_active = TRUE", (story_id,))
            row = c.fetchone()
            if not row:
                return None

            story = dict(row)

            learning_objectives = story.get("learning_objectives")
            if learning_objectives:
                try:
                    story["learning_objectives"] = json.loads(learning_objectives)
                except (json.JSONDecodeError, TypeError):
                    story["learning_objectives"] = []
            else:
                story["learning_objectives"] = []

            c.execute("SELECT * FROM story_steps WHERE story_id = ? ORDER BY step_number", (story_id,))
            story["steps"] = [dict(r) for r in c.fetchall()]

            if story["steps"]:
                actual = len(story["steps"])
                if story.get("total_steps") != actual:
                    story["total_steps"] = actual
                    c.execute("UPDATE stories SET total_steps = ? WHERE id = ?", (actual, story_id))

            return story

    def save_story_interaction(self, story_id, step_number, user_response, ai_feedback=None,
                               corrections=None, new_vocabulary=None, interaction_score=0.0,
                               response_time=0) -> int:
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO story_interactions
                   (story_id, step_number, user_response, ai_feedback, corrections,
                    new_vocabulary, interaction_score, response_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    story_id,
                    step_number,
                    user_response,
                    ai_feedback,
                    json.dumps(corrections) if corrections else None,
                    json.dumps(new_vocabulary) if new_vocabulary else None,
                    interaction_score,
                    response_time,
                ),
            )
            interaction_id = c.lastrowid
            self._update_story_progress(c, story_id, step_number)
            return interaction_id

    def _update_story_progress(self, cursor, story_id, current_step):
        cursor.execute(
            "SELECT id FROM user_story_progress WHERE story_id = ?",
            (story_id,),
        )
        progress = cursor.fetchone()
        if progress:
            cursor.execute(
                """UPDATE user_story_progress
                   SET current_step = ?, total_interactions = total_interactions + 1,
                       last_interaction = CURRENT_TIMESTAMP
                   WHERE story_id = ?""",
                (current_step, story_id),
            )
        else:
            cursor.execute(
                """INSERT INTO user_story_progress (story_id, current_step, total_interactions)
                   VALUES (?, ?, 1)""",
                (story_id, current_step),
            )

        cursor.execute("SELECT total_steps FROM stories WHERE id = ?", (story_id,))
        total_steps = cursor.fetchone()[0]
        completion = (current_step / total_steps * 100) if total_steps > 0 else 0
        cursor.execute(
            "UPDATE user_story_progress SET completion_percentage = ? WHERE story_id = ?",
            (completion, story_id),
        )

    def get_user_story_progress(self):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT story_id, current_step, is_completed, completion_percentage,
                          total_interactions, last_interaction
                   FROM user_story_progress""",
            )
            return {row["story_id"]: dict(row) for row in c.fetchall()}

    def get_story_progress(self, story_id):
        default = {
            "story_id": story_id,
            "current_step": 1,
            "is_completed": False,
            "completion_percentage": 0.0,
            "total_interactions": 0,
            "started_at": None,
            "completed_at": None,
        }
        with self._connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM user_story_progress WHERE story_id = ?", (story_id,))
            row = c.fetchone()
            return dict(row) if row else default

    def get_story_interactions(self, story_id, limit=50):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT * FROM story_interactions
                   WHERE story_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (story_id, limit),
            )
            interactions = []
            for row in c.fetchall():
                interaction = dict(row)
                for field in ("corrections", "new_vocabulary"):
                    value = interaction.get(field)
                    if value:
                        try:
                            interaction[field] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            interaction[field] = []
                    else:
                        interaction[field] = []
                if interaction.get("interaction_score") is None:
                    interaction["interaction_score"] = 0
                interactions.append(interaction)
            return interactions

    def complete_story(self, story_id):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM user_story_progress WHERE story_id = ?", (story_id,))
            exists = c.fetchone()
            if exists:
                c.execute(
                    """UPDATE user_story_progress
                       SET is_completed = TRUE, completion_percentage = 100.0,
                           completed_at = CURRENT_TIMESTAMP
                       WHERE story_id = ?""",
                    (story_id,),
                )
            else:
                c.execute(
                    """INSERT INTO user_story_progress
                       (story_id, is_completed, completion_percentage, completed_at, started_at)
                       VALUES (?, TRUE, 100.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                    (story_id,),
                )

    def get_story_templates(self, scenario=None, difficulty_level=None):
        query = "SELECT * FROM story_templates WHERE is_active = TRUE"
        params = []
        if scenario:
            query += " AND scenario = ?"
            params.append(scenario)
        if difficulty_level:
            query += " AND difficulty_level = ?"
            params.append(difficulty_level)
        query += " ORDER BY created_at DESC"

        with self._connection() as conn:
            c = conn.cursor()
            c.execute(query, params)
            templates = []
            for row in c.fetchall():
                template = dict(row)
                template["template_structure"] = json.loads(template["template_structure"])
                template["variables"] = json.loads(template["variables"]) if template["variables"] else []
                template["learning_objectives"] = json.loads(template["learning_objectives"]) if template["learning_objectives"] else []
                templates.append(template)
            return templates

    # --------------------------------------------------------------- analytics
    def get_user_analytics(self):
        with self._connection() as conn:
            c = conn.cursor()

            c.execute(
                """SELECT mistake_type, COUNT(*) as count
                   FROM grammar_mistakes
                   GROUP BY mistake_type
                   ORDER BY count DESC""",
            )
            mistake_patterns = [dict(r) for r in c.fetchall()]

            c.execute("SELECT COUNT(*) FROM conversations WHERE date(timestamp) = date('now')")
            today_conversations = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM vocabulary")
            vocabulary_count = c.fetchone()[0]

            c.execute(
                """SELECT scenario, COUNT(*) as count
                   FROM conversations c
                   JOIN grammar_mistakes g ON c.id = g.conversation_id
                   GROUP BY scenario
                   ORDER BY count DESC
                   LIMIT 3""",
            )
            problem_areas = [dict(r) for r in c.fetchall()]

            c.execute(
                """SELECT AVG(score_percentage), COUNT(*)
                   FROM quiz_results
                   WHERE date(timestamp) >= date('now', '-7 days')""",
            )
            quiz_stats = c.fetchone()

            c.execute("SELECT COUNT(*) FROM user_story_progress WHERE is_completed = TRUE")
            completed_stories = c.fetchone()[0]

            c.execute("SELECT AVG(completion_percentage) FROM user_story_progress")
            avg_story_completion = c.fetchone()[0] or 0

        return {
            "mistake_patterns": mistake_patterns,
            "today_conversations": today_conversations,
            "vocabulary_count": vocabulary_count,
            "problem_areas": problem_areas,
            "quiz_stats": {
                "avg_score": (quiz_stats[0] or 0) if quiz_stats else 0,
                "total_quizzes": (quiz_stats[1] or 0) if quiz_stats else 0,
            },
            "story_stats": {
                "completed_stories": completed_stories,
                "avg_completion": avg_story_completion,
            },
        }

    def get_user_mistakes(self, limit=5):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT mistake_type, COUNT(*) as count
                   FROM grammar_mistakes
                   GROUP BY mistake_type
                   ORDER BY count DESC
                   LIMIT ?""",
                (limit,),
            )
            return [dict(r) for r in c.fetchall()]

    def get_detailed_mistakes_for_report(self, limit=20):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT gm.mistake_type, gm.original_text, gm.corrected_text,
                          gm.explanation, c.scenario, COUNT(*) as frequency
                   FROM grammar_mistakes gm
                   JOIN conversations c ON gm.conversation_id = c.id
                   GROUP BY gm.mistake_type, gm.original_text
                   ORDER BY frequency DESC
                   LIMIT ?""",
                (limit,),
            )
            return [dict(r) for r in c.fetchall()]

    def get_vocabulary_for_report(self, limit=15):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT word, definition, times_encountered, category
                   FROM vocabulary
                   ORDER BY times_encountered DESC
                   LIMIT ?""",
                (limit,),
            )
            return [dict(r) for r in c.fetchall()]

    def get_quiz_history_for_report(self, limit=10):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT detailed_results FROM quiz_results ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return [r["detailed_results"] for r in c.fetchall()]

    def get_scenario_performance_for_report(self):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT scenario, COUNT(*) as total,
                          SUM(CASE WHEN corrections = '[]' THEN 1 ELSE 0 END) as perfect
                   FROM conversations
                   GROUP BY scenario
                   ORDER BY total DESC""",
            )
            return [dict(r) for r in c.fetchall()]

    def get_vocabulary_list(self):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT word, definition, example, times_encountered
                   FROM vocabulary
                   ORDER BY times_encountered DESC, timestamp DESC""",
            )
            return [dict(r) for r in c.fetchall()]

    def get_conversation_history(self, limit=20):
        with self._connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT user_message, ai_response, corrections, scenario, timestamp
                   FROM conversations
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (limit,),
            )
            return [dict(r) for r in c.fetchall()]
