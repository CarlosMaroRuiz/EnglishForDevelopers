import sqlite3
import json
from config import Config

class DatabaseService:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Initialize the database with all required tables"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Conversations table
        c.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            corrections TEXT,
            scenario TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Grammar mistakes table
        c.execute('''CREATE TABLE IF NOT EXISTS grammar_mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            corrected_text TEXT NOT NULL,
            mistake_type TEXT NOT NULL,
            explanation TEXT,
            conversation_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )''')
        
        # Vocabulary table
        c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            example TEXT,
            category TEXT DEFAULT 'technical',
            difficulty_level INTEGER DEFAULT 1,
            times_encountered INTEGER DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # User progress table
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_area TEXT NOT NULL,
            current_level INTEGER DEFAULT 1,
            mistakes_count INTEGER DEFAULT 0,
            improvements_count INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Learning recommendations table
        c.execute('''CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_type TEXT NOT NULL,
            content TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            is_completed BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Quiz results table
        c.execute('''CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_type TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL,
            incorrect_answers INTEGER NOT NULL,
            score_percentage REAL NOT NULL,
            focused_areas TEXT,
            detailed_results TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Quiz questions table
        c.execute('''CREATE TABLE IF NOT EXISTS quiz_questions (
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
        )''')
        
        # NEW: Stories table
        c.execute('''CREATE TABLE IF NOT EXISTS stories (
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
        )''')
        
        # NEW: Story steps table (for interactive stories)
        c.execute('''CREATE TABLE IF NOT EXISTS story_steps (
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
        )''')
        
        # NEW: User story progress table
        c.execute('''CREATE TABLE IF NOT EXISTS user_story_progress (
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
        )''')
        
        # NEW: Story interactions table
        c.execute('''CREATE TABLE IF NOT EXISTS story_interactions (
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
        )''')
        
        # NEW: Story templates table (for AI generation)
        c.execute('''CREATE TABLE IF NOT EXISTS story_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            scenario TEXT NOT NULL,
            difficulty_level TEXT NOT NULL,
            template_structure TEXT NOT NULL,
            variables TEXT,
            learning_objectives TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )''')
        
        conn.commit()
        
        # Insert default story templates if they don't exist
        self._insert_default_story_templates(c)
        conn.commit()
        conn.close()
    
    def _insert_default_story_templates(self, cursor):
        """Insert default story templates for AI generation"""
        default_templates = [
            {
                'name': 'Bug Hunt Adventure',
                'scenario': 'debugging_session',
                'difficulty_level': 'intermediate',
                'template_structure': json.dumps({
                    'intro': 'A critical bug has been discovered in production...',
                    'steps': [
                        {'type': 'narrative', 'content': 'Describe the bug symptoms'},
                        {'type': 'question', 'content': 'What would be your first debugging step?'},
                        {'type': 'narrative', 'content': 'Investigation process'},
                        {'type': 'question', 'content': 'How would you communicate this to stakeholders?'},
                        {'type': 'resolution', 'content': 'Bug resolution and lessons learned'}
                    ]
                }),
                'variables': json.dumps(['bug_type', 'system_component', 'urgency_level']),
                'learning_objectives': json.dumps(['technical vocabulary', 'problem-solving communication', 'stakeholder updates'])
            },
            {
                'name': 'Code Review Drama',
                'scenario': 'code_review',
                'difficulty_level': 'advanced',
                'template_structure': json.dumps({
                    'intro': 'You need to review a complex pull request...',
                    'steps': [
                        {'type': 'narrative', 'content': 'Analyzing the code changes'},
                        {'type': 'question', 'content': 'How would you provide constructive feedback?'},
                        {'type': 'dialogue', 'content': 'Discussion with the developer'},
                        {'type': 'question', 'content': 'How do you handle disagreements?'},
                        {'type': 'conclusion', 'content': 'Reaching consensus and approval'}
                    ]
                }),
                'variables': json.dumps(['code_complexity', 'team_member', 'review_type']),
                'learning_objectives': json.dumps(['diplomatic language', 'technical feedback', 'conflict resolution'])
            },
            {
                'name': 'Interview Challenge',
                'scenario': 'technical_interview',
                'difficulty_level': 'beginner',
                'template_structure': json.dumps({
                    'intro': 'You are interviewing for a software developer position...',
                    'steps': [
                        {'type': 'question', 'content': 'Tell me about yourself'},
                        {'type': 'technical', 'content': 'Explain a technical concept'},
                        {'type': 'behavioral', 'content': 'Describe a challenging project'},
                        {'type': 'scenario', 'content': 'How would you handle a difficult situation?'},
                        {'type': 'closing', 'content': 'Questions for the interviewer'}
                    ]
                }),
                'variables': json.dumps(['company_type', 'position_level', 'technology_stack']),
                'learning_objectives': json.dumps(['self-presentation', 'technical explanations', 'question asking'])
            }
        ]
        
        for template in default_templates:
            cursor.execute('''INSERT OR IGNORE INTO story_templates 
                             (name, scenario, difficulty_level, template_structure, variables, learning_objectives)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (template['name'], template['scenario'], template['difficulty_level'],
                           template['template_structure'], template['variables'], template['learning_objectives']))
    
    def save_conversation(self, user_message, ai_response, corrections, scenario):
        """Save a conversation with corrections to the database"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''INSERT INTO conversations (user_message, ai_response, corrections, scenario)
                     VALUES (?, ?, ?, ?)''',
                  (user_message, ai_response, json.dumps(corrections), scenario))
        
        conversation_id = c.lastrowid
        
        # Save grammar mistakes
        for correction in corrections:
            c.execute('''INSERT INTO grammar_mistakes 
                         (original_text, corrected_text, mistake_type, explanation, conversation_id)
                         VALUES (?, ?, ?, ?, ?)''',
                      (correction.get('original', ''),
                       correction.get('corrected', ''),
                       correction.get('type', ''),
                       correction.get('explanation', ''),
                       conversation_id))
        
        conn.commit()
        conn.close()
        return conversation_id
    
    def save_vocabulary(self, vocabulary_list):
        """Save new vocabulary words to the database"""
        conn = self.get_connection()
        c = conn.cursor()
        
        for vocab in vocabulary_list:
            c.execute('''INSERT OR IGNORE INTO vocabulary (word, definition, example)
                         VALUES (?, ?, ?)''',
                      (vocab.get('word', ''),
                       vocab.get('definition', ''),
                       vocab.get('example', '')))
            
            # Update encounter count if word already exists
            c.execute('''UPDATE vocabulary SET times_encountered = times_encountered + 1
                         WHERE word = ?''', (vocab.get('word', ''),))
        
        conn.commit()
        conn.close()
    
    def save_quiz_result(self, quiz_type, total_questions, correct_answers, detailed_results, focused_areas):
        """Save quiz results to the database"""
        conn = self.get_connection()
        c = conn.cursor()
        
        incorrect_answers = total_questions - correct_answers
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        c.execute('''INSERT INTO quiz_results 
                     (quiz_type, total_questions, correct_answers, incorrect_answers, 
                      score_percentage, focused_areas, detailed_results)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (quiz_type, total_questions, correct_answers, incorrect_answers,
                   score_percentage, json.dumps(focused_areas), json.dumps(detailed_results)))
        
        conn.commit()
        conn.close()
    
    def save_quiz_questions(self, questions):
        """Save generated quiz questions to the database"""
        conn = self.get_connection()
        c = conn.cursor()
        
        for q in questions:
            c.execute('''INSERT INTO quiz_questions 
                         (question_text, option_a, option_b, option_c, correct_answer, 
                          explanation, grammar_category, based_on_user_mistake)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (q.get('question', ''),
                       q.get('option_a', ''),
                       q.get('option_b', ''),
                       q.get('option_c', ''),
                       q.get('correct_answer', 'a'),
                       q.get('explanation', ''),
                       q.get('category', 'general'),
                       True))
        
        conn.commit()
        conn.close()
    
    # NEW: Stories database methods
    def save_story(self, title, description, content, story_type='generated', scenario='general', 
                   difficulty_level='intermediate', topic='software_development', estimated_time=10,
                   learning_objectives=None):
        """Save a new story to the database"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''INSERT INTO stories 
                     (title, description, content, story_type, scenario, difficulty_level, 
                      topic, estimated_time, learning_objectives)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (title, description, content, story_type, scenario, difficulty_level,
                   topic, estimated_time, json.dumps(learning_objectives) if learning_objectives else None))
        
        story_id = c.lastrowid
        conn.commit()
        conn.close()
        return story_id
    
    def save_story_steps(self, story_id, steps):
        """Save story steps for interactive stories"""
        conn = self.get_connection()
        c = conn.cursor()
        
        for i, step in enumerate(steps, 1):
            c.execute('''INSERT INTO story_steps 
                         (story_id, step_number, step_type, content, question, 
                          expected_response_type, learning_focus)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (story_id, i, step.get('type', 'narrative'), step.get('content', ''),
                       step.get('question', ''), step.get('expected_response_type', 'open'),
                       step.get('learning_focus', '')))
        
        # Update total steps in stories table
        c.execute('''UPDATE stories SET total_steps = ? WHERE id = ?''', (len(steps), story_id))
        
        conn.commit()
        conn.close()
    
    def get_stories_list(self, limit=20):
        """Get list of available stories"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT id, title, description, scenario, difficulty_level, topic, 
                            estimated_time, total_steps, created_at
                     FROM stories 
                     WHERE is_active = TRUE
                     ORDER BY created_at DESC 
                     LIMIT ?''', (limit,))
        
        stories = c.fetchall()
        conn.close()
        return stories
    
    def get_story_by_id(self, story_id):
        """Get a specific story by ID"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT * FROM stories WHERE id = ? AND is_active = TRUE''', (story_id,))
        story_row = c.fetchone()
        
        if not story_row:
            conn.close()
            return None
        
        # Convert to dictionary
        story = dict(zip([col[0] for col in c.description], story_row))
        
        # Parse learning_objectives JSON if it exists
        if story.get('learning_objectives'):
            try:
                story['learning_objectives'] = json.loads(story['learning_objectives'])
            except (json.JSONDecodeError, TypeError):
                story['learning_objectives'] = []
        else:
            story['learning_objectives'] = []
        
        # Get story steps
        c.execute('''SELECT * FROM story_steps WHERE story_id = ? ORDER BY step_number''', (story_id,))
        steps_rows = c.fetchall()
        
        story['steps'] = []
        for step_row in steps_rows:
            step = dict(zip([col[0] for col in c.description], step_row))
            story['steps'].append(step)
        
        conn.close()
        return story
    
    def save_story_interaction(self, story_id, step_number, user_response, ai_feedback=None, 
                              corrections=None, new_vocabulary=None, interaction_score=0.0, response_time=0):
        """Save user interaction with a story step"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''INSERT INTO story_interactions 
                     (story_id, step_number, user_response, ai_feedback, corrections, 
                      new_vocabulary, interaction_score, response_time)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (story_id, step_number, user_response, ai_feedback,
                   json.dumps(corrections) if corrections else None,
                   json.dumps(new_vocabulary) if new_vocabulary else None,
                   interaction_score, response_time))
        
        interaction_id = c.lastrowid
        
        # Update user progress
        self._update_story_progress(c, story_id, step_number)
        
        conn.commit()
        conn.close()
        return interaction_id
    
    def _update_story_progress(self, cursor, story_id, current_step):
        """Update user progress for a story"""
        # Check if progress record exists
        cursor.execute('''SELECT id, total_interactions FROM user_story_progress 
                         WHERE story_id = ?''', (story_id,))
        progress = cursor.fetchone()
        
        if progress:
            # Update existing progress
            cursor.execute('''UPDATE user_story_progress 
                             SET current_step = ?, total_interactions = total_interactions + 1,
                                 last_interaction = CURRENT_TIMESTAMP
                             WHERE story_id = ?''', (current_step, story_id))
        else:
            # Create new progress record
            cursor.execute('''INSERT INTO user_story_progress 
                             (story_id, current_step, total_interactions)
                             VALUES (?, ?, 1)''', (story_id, current_step))
        
        # Calculate completion percentage
        cursor.execute('''SELECT total_steps FROM stories WHERE id = ?''', (story_id,))
        total_steps = cursor.fetchone()[0]
        completion_percentage = (current_step / total_steps) * 100 if total_steps > 0 else 0
        
        cursor.execute('''UPDATE user_story_progress 
                         SET completion_percentage = ? WHERE story_id = ?''', 
                      (completion_percentage, story_id))
    
    def get_user_story_progress(self):
        """Get user progress for all stories"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT story_id, current_step, is_completed, completion_percentage,
                            total_interactions, last_interaction
                     FROM user_story_progress''')
        
        progress_data = {}
        for row in c.fetchall():
            progress_data[row[0]] = {
                'current_step': row[1],
                'is_completed': row[2],
                'completion_percentage': row[3],
                'total_interactions': row[4],
                'last_interaction': row[5]
            }
        
        conn.close()
        return progress_data
    
    def get_story_progress(self, story_id):
        """Get user progress for a specific story"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT * FROM user_story_progress WHERE story_id = ?''', (story_id,))
        progress_row = c.fetchone()
        
        progress = None
        if progress_row:
            progress = dict(zip([col[0] for col in c.description], progress_row))
        
        conn.close()
        return progress
    
    def get_story_interactions(self, story_id, limit=50):
        """Get user interactions for a specific story"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT * FROM story_interactions 
                     WHERE story_id = ? 
                     ORDER BY timestamp DESC 
                     LIMIT ?''', (story_id, limit))
        
        interactions = []
        for row in c.fetchall():
            interaction = dict(zip([col[0] for col in c.description], row))
            # Parse JSON fields
            if interaction['corrections']:
                interaction['corrections'] = json.loads(interaction['corrections'])
            if interaction['new_vocabulary']:
                interaction['new_vocabulary'] = json.loads(interaction['new_vocabulary'])
            interactions.append(interaction)
        
        conn.close()
        return interactions
    
    def complete_story(self, story_id):
        """Mark a story as completed"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''UPDATE user_story_progress 
                     SET is_completed = TRUE, completion_percentage = 100.0,
                         completed_at = CURRENT_TIMESTAMP
                     WHERE story_id = ?''', (story_id,))
        
        conn.commit()
        conn.close()
    
    def get_story_templates(self, scenario=None, difficulty_level=None):
        """Get story templates for AI generation"""
        conn = self.get_connection()
        c = conn.cursor()
        
        query = '''SELECT * FROM story_templates WHERE is_active = TRUE'''
        params = []
        
        if scenario:
            query += ' AND scenario = ?'
            params.append(scenario)
        
        if difficulty_level:
            query += ' AND difficulty_level = ?'
            params.append(difficulty_level)
        
        query += ' ORDER BY created_at DESC'
        
        c.execute(query, params)
        templates = []
        for row in c.fetchall():
            template = dict(zip([col[0] for col in c.description], row))
            # Parse JSON fields
            template['template_structure'] = json.loads(template['template_structure'])
            template['variables'] = json.loads(template['variables']) if template['variables'] else []
            template['learning_objectives'] = json.loads(template['learning_objectives']) if template['learning_objectives'] else []
            templates.append(template)
        
        conn.close()
        return templates
    
    def get_user_analytics(self):
        """Get comprehensive user analytics"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Get mistake patterns
        c.execute('''SELECT mistake_type, COUNT(*) as count 
                     FROM grammar_mistakes 
                     GROUP BY mistake_type 
                     ORDER BY count DESC''')
        mistake_patterns = c.fetchall()
        
        # Get recent conversations count
        c.execute('''SELECT COUNT(*) FROM conversations 
                     WHERE date(timestamp) = date('now')''')
        today_conversations = c.fetchone()[0]
        
        # Get vocabulary progress
        c.execute('''SELECT COUNT(*) FROM vocabulary''')
        vocabulary_count = c.fetchone()[0]
        
        # Most problematic areas
        c.execute('''SELECT scenario, COUNT(*) as count
                     FROM conversations c
                     JOIN grammar_mistakes g ON c.id = g.conversation_id
                     GROUP BY scenario
                     ORDER BY count DESC
                     LIMIT 3''')
        problem_areas = c.fetchall()
        
        # Quiz statistics
        c.execute('''SELECT AVG(score_percentage), COUNT(*) 
                     FROM quiz_results 
                     WHERE date(timestamp) >= date('now', '-7 days')''')
        quiz_stats = c.fetchone()
        
        # NEW: Story statistics
        c.execute('''SELECT COUNT(*) FROM user_story_progress WHERE is_completed = TRUE''')
        completed_stories = c.fetchone()[0]
        
        c.execute('''SELECT AVG(completion_percentage) FROM user_story_progress''')
        avg_story_completion = c.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'mistake_patterns': mistake_patterns,
            'today_conversations': today_conversations,
            'vocabulary_count': vocabulary_count,
            'problem_areas': problem_areas,
            'quiz_stats': {
                'avg_score': quiz_stats[0] or 0,
                'total_quizzes': quiz_stats[1] or 0
            },
            'story_stats': {
                'completed_stories': completed_stories,
                'avg_completion': avg_story_completion
            }
        }
    
    def get_user_mistakes(self, limit=5):
        """Get user's most common mistake patterns"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT mistake_type, COUNT(*) as count 
                     FROM grammar_mistakes 
                     GROUP BY mistake_type 
                     ORDER BY count DESC
                     LIMIT ?''', (limit,))
        user_mistakes = c.fetchall()
        conn.close()
        return user_mistakes
    
    def get_detailed_mistakes_for_report(self, limit=20):
        """Get detailed mistake patterns for AI report generation"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT gm.mistake_type, gm.original_text, gm.corrected_text, 
                            gm.explanation, c.scenario, COUNT(*) as frequency
                     FROM grammar_mistakes gm
                     JOIN conversations c ON gm.conversation_id = c.id
                     GROUP BY gm.mistake_type, gm.original_text
                     ORDER BY frequency DESC
                     LIMIT ?''', (limit,))
        detailed_mistakes = c.fetchall()
        
        conn.close()
        return detailed_mistakes
    
    def get_vocabulary_for_report(self, limit=15):
        """Get vocabulary data for AI report generation"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT word, definition, times_encountered, category
                     FROM vocabulary 
                     ORDER BY times_encountered DESC
                     LIMIT ?''', (limit,))
        vocabulary_data = c.fetchall()
        conn.close()
        return vocabulary_data
    
    def get_quiz_history_for_report(self, limit=10):
        """Get recent quiz history for AI report generation"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT detailed_results FROM quiz_results 
                     ORDER BY timestamp DESC LIMIT ?''', (limit,))
        quiz_history = c.fetchall()
        conn.close()
        return quiz_history
    
    def get_scenario_performance_for_report(self):
        """Get conversation scenarios performance for AI report generation"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT scenario, COUNT(*) as total, 
                            SUM(CASE WHEN corrections = '[]' THEN 1 ELSE 0 END) as perfect
                     FROM conversations 
                     GROUP BY scenario
                     ORDER BY total DESC''')
        scenario_performance = c.fetchall()
        conn.close()
        return scenario_performance
    
    def get_vocabulary_list(self):
        """Get complete vocabulary list"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT word, definition, example, times_encountered 
                     FROM vocabulary 
                     ORDER BY times_encountered DESC, timestamp DESC''')
        vocab_list = c.fetchall()
        conn.close()
        return vocab_list
    
    def get_conversation_history(self, limit=20):
        """Get recent conversation history"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT user_message, ai_response, corrections, scenario, timestamp 
                     FROM conversations 
                     ORDER BY timestamp DESC 
                     LIMIT ?''', (limit,))
        conversations = c.fetchall()
        conn.close()
        return conversations