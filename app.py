from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
from datetime import datetime
import requests
import os
import re
from collections import Counter
from dotenv import load_dotenv

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
    
    conn.close()
    
    return {
        'mistake_patterns': mistake_patterns,
        'today_conversations': today_conversations,
        'vocabulary_count': vocabulary_count,
        'problem_areas': problem_areas
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