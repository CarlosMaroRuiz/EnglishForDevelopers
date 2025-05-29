import json
import requests
from config import Config

class DeepSeekClient:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.base_url = (base_url or Config.DEEPSEEK_BASE_URL).rstrip('/')
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

class AIService:
    def __init__(self, db_service):
        self.db_service = db_service
        try:
            self.client = DeepSeekClient()
            print("✅ DeepSeek API client initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing DeepSeek API client: {e}")
            self.client = None
    
    def analyze_english_with_deepseek(self, user_message, scenario):
        """Analyze user's English and provide corrections and suggestions"""
        if not self.client:
            return {
                "conversation_response": "Sorry, the AI service is not properly configured. Please check your API key.",
                "corrections": [],
                "new_vocabulary": [],
                "suggestions": "Please configure your DeepSeek API key to use this feature."
            }
        
        system_prompt = f"""You are an English tutor specialized in helping software developers improve their technical English communication. 

Current scenario: {Config.get_scenario_prompt(scenario)}

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
            response = self.client.chat_completions_create(
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
    
    def generate_quiz_questions(self, user_mistakes, num_questions=5):
        """Generate quiz questions based on user's common mistakes"""
        if not self.client:
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
            response = self.client.chat_completions_create(
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
            if questions:
                self.db_service.save_quiz_questions(questions)
            
            return questions
            
        except Exception as e:
            print(f"Error generating quiz questions: {e}")
            return []
    
    def generate_ai_personal_report(self):
        """Generate a comprehensive AI analysis report of the user's English skills"""
        if not self.client:
            return {
                "strengths": ["Unable to analyze - AI service not available"],
                "weaknesses": ["Please check your API configuration"],
                "grammar_mastered": [],
                "grammar_needs_work": [],
                "focus_areas": [],
                "recommendations": [],
                "overall_assessment": "AI analysis unavailable",
                "learning_path": [],
                "personality_insights": []
            }
        
        # Get comprehensive user data
        detailed_mistakes = self.db_service.get_detailed_mistakes_for_report()
        vocabulary_data = self.db_service.get_vocabulary_for_report()
        quiz_history = self.db_service.get_quiz_history_for_report()
        scenario_performance = self.db_service.get_scenario_performance_for_report()
        
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
            response = self.client.chat_completions_create(
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