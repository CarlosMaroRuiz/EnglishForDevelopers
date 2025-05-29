from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
from datetime import datetime
import requests
import os
import re
from collections import Counter
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# DeepSeek API Client Class
class DeepSeekClient:
    def __init__(self, api_key=None, base_url="https://api.deepseek.com"):
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completions_create(self, model="deepseek-chat", messages=None, temperature=1.0, stream=False):
        """Create a chat completion using DeepSeek API"""
        if not self.api_key or self.api_key == "sk-dummy-key-replace-with-real-key":
            raise Exception("Invalid or missing API key. Please set DEEPSEEK_API_KEY in your .env file")
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages or [],
            "temperature": temperature,
            "stream": stream
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Create a simple response object similar to OpenAI's format
            class Choice:
                def __init__(self, message_content):
                    self.message = type('Message', (), {'content': message_content})()
            
            class ChatCompletion:
                def __init__(self, choices):
                    self.choices = choices
            
            return ChatCompletion([Choice(data['choices'][0]['message']['content'])])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling DeepSeek API: {str(e)}")

# Configure DeepSeek API
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
if not DEEPSEEK_API_KEY:
    print("⚠️  WARNING: DEEPSEEK_API_KEY not found in environment variables!")
    print("Please create a .env file with your DeepSeek API key.")
    print("Example: DEEPSEEK_API_KEY=your_actual_api_key_here")

try:
    client = DeepSeekClient()
    print("✅ DeepSeek API client initialized successfully")
except Exception as e:
    print(f"❌ Error initializing DeepSeek API client: {e}")
    client = None

# Database setup
def init_db():
    conn = sqlite3.connect('english_tutor.db')
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

# Work scenarios for practice
WORK_SCENARIOS = [
    "daily_standup",
    "code_review", 
    "technical_interview",
    "debugging_session",
    "project_planning",
    "client_meeting",
    "architecture_discussion",
    "deployment_issue"
]

def get_scenario_prompt(scenario):
    prompts = {
        "daily_standup": "You're in a daily standup meeting. Discuss what you worked on yesterday, what you're working on today, and any blockers.",
        "code_review": "You're reviewing a colleague's pull request. Discuss the code quality, suggest improvements, and ask questions.",
        "technical_interview": "You're in a technical interview. Answer questions about your experience, solve coding problems, and ask about the role.",
        "debugging_session": "You're helping debug a production issue. Explain the problem, discuss potential causes, and propose solutions.",
        "project_planning": "You're planning a new feature. Discuss requirements, technical approach, and timeline estimates.",
        "client_meeting": "You're meeting with a client to discuss their software requirements and provide technical recommendations.",
        "architecture_discussion": "You're discussing system architecture with your team. Talk about design patterns, scalability, and best practices.",
        "deployment_issue": "There's a deployment problem in production. Communicate the issue, impact, and resolution steps."
    }
    return prompts.get(scenario, "General technical discussion")

def analyze_english_with_deepseek(user_message, scenario):
    if not client:
        return {
            "conversation_response": "Sorry, the AI service is not properly configured. Please check your API key.",
            "corrections": [],
            "new_vocabulary": [],
            "suggestions": "Please configure your DeepSeek API key to use this feature."
        }
    
    system_prompt = f"""You are an English tutor specialized in helping software developers improve their technical English communication. 

Current scenario: {get_scenario_prompt(scenario)}

Your role:
1. Respond naturally to continue the work conversation in the given scenario
2. Identify and correct any grammar, vocabulary, or communication errors
3. Suggest better ways to express technical concepts
4. Introduce new technical vocabulary when appropriate
5. Ask follow-up questions to keep the conversation engaging

IMPORTANT: You MUST respond with valid JSON in exactly this format:
{{
    "conversation_response": "Your natural response to continue the work scenario",
    "corrections": [
        {{
            "original": "incorrect text",
            "corrected": "corrected text", 
            "type": "grammar/vocabulary/style",
            "explanation": "why this is better"
        }}
    ],
    "new_vocabulary": [
        {{
            "word": "technical term",
            "definition": "definition",
            "example": "usage example"
        }}
    ],
    "suggestions": "Additional tips for improvement"
}}

Do NOT include any other text before or after the JSON. Only return the JSON object."""

    try:
        response = client.chat_completions_create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=1.0
        )
        
        # Get the response content
        content = response.choices[0].message.content.strip()
        
        # Clean up the response - remove any markdown formatting
        if content.startswith('```json'):
            content = content[7:]  # Remove ```json
        if content.endswith('```'):
            content = content[:-3]  # Remove ```
        
        content = content.strip()
        
        # Try to parse JSON response
        try:
            parsed_response = json.loads(content)
            
            # Validate the response structure
            if not isinstance(parsed_response, dict):
                raise ValueError("Response is not a dictionary")
            
            # Set defaults for missing keys
            result = {
                "conversation_response": parsed_response.get("conversation_response", "I understand. Let's continue our conversation."),
                "corrections": parsed_response.get("corrections", []),
                "new_vocabulary": parsed_response.get("new_vocabulary", []),
                "suggestions": parsed_response.get("suggestions", "")
            }
            
            # Ensure corrections is a list
            if not isinstance(result["corrections"], list):
                result["corrections"] = []
            
            # Ensure new_vocabulary is a list  
            if not isinstance(result["new_vocabulary"], list):
                result["new_vocabulary"] = []
                
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw content: {content}")
            
            # Fallback if JSON parsing fails
            return {
                "conversation_response": content,
                "corrections": [],
                "new_vocabulary": [],
                "suggestions": "The AI provided a response but in an unexpected format."
            }
            
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return {
            "conversation_response": "I'm sorry, I'm having trouble connecting to the AI service right now. Please try again later.",
            "corrections": [],
            "new_vocabulary": [],
            "suggestions": f"Error details: {str(e)}"
        }

def generate_quiz_questions(user_mistakes, num_questions=5):
    """Generate quiz questions based on user's common mistakes"""
    if not client:
        return []
    
    # Get user's most common mistake types
    mistake_types = [mistake[0] for mistake in user_mistakes[:3]]  # Top 3 mistake types
    
    system_prompt = f"""You are an English grammar quiz generator for software developers. 

Based on the user's common mistakes in these areas: {', '.join(mistake_types)}, generate {num_questions} multiple choice questions to help them practice.

Focus on technical English and workplace communication scenarios.

IMPORTANT: You MUST respond with valid JSON in exactly this format:
{{
    "questions": [
        {{
            "question": "Choose the correct sentence for a daily standup:",
            "option_a": "I worked on API integration yesterday",
            "option_b": "I work on API integration yesterday", 
            "option_c": "I working on API integration yesterday",
            "correct_answer": "a",
            "explanation": "Past tense 'worked' is correct when describing completed actions",
            "category": "verb_tense"
        }}
    ]
}}

Generate questions that are:
1. Relevant to software development contexts
2. Focus on the user's problem areas: {', '.join(mistake_types)}
3. Have clear explanations 
4. Use realistic workplace scenarios

Do NOT include any other text before or after the JSON."""

    try:
        response = client.chat_completions_create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up the response
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON response
        parsed_response = json.loads(content)
        questions = parsed_response.get("questions", [])
        
        # Save questions to database
        conn = sqlite3.connect('english_tutor.db')
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
        
        return questions
        
    except Exception as e:
        print(f"Error generating quiz questions: {e}")
        return []

def save_conversation(user_message, ai_response, corrections, scenario):
    conn = sqlite3.connect('english_tutor.db')
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

def save_vocabulary(vocabulary_list):
    conn = sqlite3.connect('english_tutor.db')
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

def save_quiz_result(quiz_type, total_questions, correct_answers, detailed_results, focused_areas):
    conn = sqlite3.connect('english_tutor.db')
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

def get_user_analytics():
    conn = sqlite3.connect('english_tutor.db')
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

def generate_ai_personal_report():
    """Generate a comprehensive AI analysis report of the user's English skills"""
    if not client:
        return {
            "strengths": ["Unable to analyze - AI service not available"],
            "weaknesses": ["Please check your API configuration"],
            "grammar_mastered": [],
            "grammar_needs_work": [],
            "focus_areas": [],
            "recommendations": [],
            "overall_assessment": "AI analysis unavailable",
            "learning_path": []
        }
    
    # Get comprehensive user data
    conn = sqlite3.connect('english_tutor.db')
    c = conn.cursor()
    
    # Get mistake patterns with context
    c.execute('''SELECT gm.mistake_type, gm.original_text, gm.corrected_text, 
                        gm.explanation, c.scenario, COUNT(*) as frequency
                 FROM grammar_mistakes gm
                 JOIN conversations c ON gm.conversation_id = c.id
                 GROUP BY gm.mistake_type, gm.original_text
                 ORDER BY frequency DESC
                 LIMIT 20''')
    detailed_mistakes = c.fetchall()
    
    # Get vocabulary progress
    c.execute('''SELECT word, definition, times_encountered, category
                 FROM vocabulary 
                 ORDER BY times_encountered DESC
                 LIMIT 15''')
    vocabulary_data = c.fetchall()
    
    # Get quiz performance by category
    c.execute('''SELECT detailed_results FROM quiz_results 
                 ORDER BY timestamp DESC LIMIT 10''')
    quiz_history = c.fetchall()
    
    # Get conversation scenarios performance
    c.execute('''SELECT scenario, COUNT(*) as total, 
                        SUM(CASE WHEN corrections = '[]' THEN 1 ELSE 0 END) as perfect
                 FROM conversations 
                 GROUP BY scenario
                 ORDER BY total DESC''')
    scenario_performance = c.fetchall()
    
    conn.close()
    
    # Prepare data for AI analysis
    analysis_data = {
        "mistakes": detailed_mistakes,
        "vocabulary": vocabulary_data,
        "quiz_history": quiz_history,
        "scenarios": scenario_performance
    }
    
    system_prompt = f"""You are an expert English language analyst for software developers. 
Analyze the following learning data and provide a comprehensive personal report.

User's Learning Data:
- Common Mistakes: {len(detailed_mistakes)} different error patterns
- Vocabulary: {len(vocabulary_data)} technical terms learned
- Quiz History: {len(quiz_history)} recent quizzes taken
- Conversation Scenarios: {len(scenario_performance)} different workplace contexts

Based on this data, provide a detailed analysis in JSON format:

{{
    "strengths": [
        "List 3-5 specific areas where the user excels",
        "Include grammar topics they handle well",
        "Mention vocabulary strengths"
    ],
    "weaknesses": [
        "List 3-5 specific areas needing improvement", 
        "Focus on recurring mistake patterns",
        "Include challenging grammar concepts"
    ],
    "grammar_mastered": [
        "Grammar topics the user demonstrates proficiency in",
        "Based on few/no mistakes in these areas"
    ],
    "grammar_needs_work": [
        "Grammar topics with frequent mistakes",
        "Areas requiring focused practice"
    ],
    "focus_areas": [
        "Top 3 priority areas for improvement",
        "Most impactful areas to work on next"
    ],
    "recommendations": [
        "Specific, actionable recommendations",
        "Include study strategies and practice methods"
    ],
    "overall_assessment": "2-3 sentence summary of current English level and progress",
    "learning_path": [
        "Step-by-step learning plan for next 2-4 weeks",
        "Ordered by priority and logical progression"
    ],
    "personality_insights": [
        "Learning style observations",
        "Communication patterns noticed"
    ]
}}

Focus on software development communication contexts. Be specific and constructive.
Do NOT include any text before or after the JSON object."""

    try:
        response = client.chat_completions_create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up the response
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON response
        report = json.loads(content)
        
        # Validate and set defaults
        default_report = {
            "strengths": [],
            "weaknesses": [],
            "grammar_mastered": [],
            "grammar_needs_work": [],
            "focus_areas": [],
            "recommendations": [],
            "overall_assessment": "",
            "learning_path": [],
            "personality_insights": []
        }
        
        for key in default_report:
            if key not in report:
                report[key] = default_report[key]
        
        return report
        
    except Exception as e:
        print(f"Error generating AI report: {e}")
        return {
            "strengths": ["You're actively practicing English with AI feedback"],
            "weaknesses": ["Unable to generate detailed analysis due to technical issues"],
            "grammar_mastered": [],
            "grammar_needs_work": [],
            "focus_areas": ["Continue practicing conversations", "Take more quizzes"],
            "recommendations": ["Keep using the chat feature", "Try different scenarios"],
            "overall_assessment": "Keep practicing! Your dedication to learning is your biggest strength.",
            "learning_path": ["Practice daily conversations", "Focus on grammar quizzes"],
            "personality_insights": ["Shows commitment to learning"]
        }

def generate_recommendations():
    analytics = get_user_analytics()
    recommendations = []
    
    # Recommend based on most common mistakes
    if analytics['mistake_patterns']:
        top_mistake = analytics['mistake_patterns'][0]
        recommendations.append({
            'type': 'grammar_focus',
            'content': f"Focus on improving {top_mistake[0]} - you've made {top_mistake[1]} mistakes in this area",
            'priority': 3
        })
    
    # Recommend practice scenarios
    if analytics['problem_areas']:
        top_problem = analytics['problem_areas'][0]
        recommendations.append({
            'type': 'scenario_practice',
            'content': f"Practice more {top_problem[0].replace('_', ' ')} scenarios - this is where you make most mistakes",
            'priority': 2
        })
    
    # Vocabulary building
    if analytics['vocabulary_count'] < 50:
        recommendations.append({
            'type': 'vocabulary',
            'content': "Build your technical vocabulary - aim to learn 5 new terms this week",
            'priority': 1
        })
    
    # Quiz recommendations
    if analytics['quiz_stats']['avg_score'] < 70:
        recommendations.append({
            'type': 'quiz_practice',
            'content': "Your quiz average is below 70%. Take more grammar quizzes to improve!",
            'priority': 3
        })
    
    return recommendations

# Routes
@app.route('/')
def index():
    return render_template('index.html', scenarios=WORK_SCENARIOS)

@app.route('/chat')
def chat():
    scenario = request.args.get('scenario', 'daily_standup')
    return render_template('chat.html', scenario=scenario)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    user_message = data.get('message', '')
    scenario = data.get('scenario', 'daily_standup')
    
    # Analyze with DeepSeek
    analysis = analyze_english_with_deepseek(user_message, scenario)
    
    # Save to database
    save_conversation(
        user_message,
        analysis.get('conversation_response', ''),
        analysis.get('corrections', []),
        scenario
    )
    
    # Save new vocabulary
    if analysis.get('new_vocabulary'):
        save_vocabulary(analysis.get('new_vocabulary', []))
    
    return jsonify(analysis)

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    try:
        # Get user's mistake patterns
        conn = sqlite3.connect('english_tutor.db')
        c = conn.cursor()
        c.execute('''SELECT mistake_type, COUNT(*) as count 
                     FROM grammar_mistakes 
                     GROUP BY mistake_type 
                     ORDER BY count DESC
                     LIMIT 5''')
        user_mistakes = c.fetchall()
        conn.close()
        
        if not user_mistakes:
            # If no mistakes found, create default questions
            default_questions = [
                {
                    "question": "Choose the correct sentence for a code review:",
                    "option_a": "This function works good",
                    "option_b": "This function works well",
                    "option_c": "This function work well",
                    "correct_answer": "b",
                    "explanation": "'Well' is the correct adverb to describe how something works",
                    "category": "grammar"
                },
                {
                    "question": "Which is the correct way to report a bug?",
                    "option_a": "I found a bug in the login system",
                    "option_b": "I finded a bug in the login system",
                    "option_c": "I find a bug in the login system",
                    "correct_answer": "a",
                    "explanation": "'Found' is the correct past tense of 'find'",
                    "category": "verb_tense"
                }
            ]
            return jsonify({"questions": default_questions})
        
        # Generate questions based on user mistakes
        questions = generate_quiz_questions(user_mistakes, 5)
        
        if not questions:
            return jsonify({"error": "Failed to generate quiz questions"}), 500
        
        return jsonify({"questions": questions})
        
    except Exception as e:
        print(f"Error in generate_quiz: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        answers = data.get('answers', {})
        questions = data.get('questions', [])
        
        if not answers or not questions:
            return jsonify({"error": "Missing quiz data"}), 400
        
        # Calculate results
        correct_count = 0
        total_questions = len(questions)
        detailed_results = []
        focused_areas = []
        
        for i, question in enumerate(questions):
            user_answer = answers.get(str(i))
            correct_answer = question.get('correct_answer')
            is_correct = user_answer == correct_answer
            
            if is_correct:
                correct_count += 1
            else:
                focused_areas.append(question.get('category', 'general'))
            
            detailed_results.append({
                'question': question.get('question'),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation'),
                'category': question.get('category')
            })
        
        # Calculate score
        score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Save results to database
        save_quiz_result('grammar_practice', total_questions, correct_count, detailed_results, focused_areas)
        
        # Generate feedback message
        if score_percentage >= 90:
            feedback = "¡Excelente! Your English grammar is very strong."
        elif score_percentage >= 70:
            feedback = "¡Buen trabajo! You have a good understanding, but there's room for improvement."
        elif score_percentage >= 50:
            feedback = "Not bad, but you should focus more on the areas where you made mistakes."
        else:
            feedback = "Keep practicing! Focus on the grammar areas highlighted in your results."
        
        return jsonify({
            "score": score_percentage,
            "correct": correct_count,
            "total": total_questions,
            "feedback": feedback,
            "detailed_results": detailed_results,
            "focused_areas": list(set(focused_areas))
        })
        
    except Exception as e:
        print(f"Error in submit_quiz: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/report')
def personal_report():
    """Generate and display comprehensive AI analysis report"""
    try:
        # Generate AI report
        ai_report = generate_ai_personal_report()
        
        # Get additional analytics data
        analytics = get_user_analytics()
        
        return render_template('report.html', 
                             report=ai_report, 
                             analytics=analytics)
        
    except Exception as e:
        print(f"Error generating report: {e}")
        # Fallback data
        fallback_report = {
            "strengths": ["You're committed to learning"],
            "weaknesses": ["Continue practicing regularly"],
            "grammar_mastered": [],
            "grammar_needs_work": [],
            "focus_areas": ["Daily practice", "Grammar quizzes"],
            "recommendations": ["Keep practicing conversations"],
            "overall_assessment": "Keep up the great work with your English practice!",
            "learning_path": ["Daily conversations", "Weekly quizzes"],
            "personality_insights": ["Dedicated learner"]
        }
        analytics = get_user_analytics()
        return render_template('report.html', 
                             report=fallback_report, 
                             analytics=analytics)

@app.route('/analytics')
def analytics():
    data = get_user_analytics()
    recommendations = generate_recommendations()
    return render_template('analytics.html', analytics=data, recommendations=recommendations)

@app.route('/vocabulary')
def vocabulary():
    conn = sqlite3.connect('english_tutor.db')
    c = conn.cursor()
    c.execute('''SELECT word, definition, example, times_encountered 
                 FROM vocabulary 
                 ORDER BY times_encountered DESC, timestamp DESC''')
    vocab_list = c.fetchall()
    conn.close()
    
    return render_template('vocabulary.html', vocabulary=vocab_list)

@app.route('/history')
def history():
    conn = sqlite3.connect('english_tutor.db')
    c = conn.cursor()
    c.execute('''SELECT user_message, ai_response, corrections, scenario, timestamp 
                 FROM conversations 
                 ORDER BY timestamp DESC 
                 LIMIT 20''')
    conversations = c.fetchall()
    conn.close()
    
    return render_template('history.html', conversations=conversations)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)