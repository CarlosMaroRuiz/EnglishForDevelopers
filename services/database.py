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
        
        conn.commit()
        conn.close()
    
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
        
        conn.close()
        
        return {
            'mistake_patterns': mistake_patterns,
            'today_conversations': today_conversations,
            'vocabulary_count': vocabulary_count,
            'problem_areas': problem_areas,
            'quiz_stats': {
                'avg_score': quiz_stats[0] or 0,
                'total_quizzes': quiz_stats[1] or 0
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