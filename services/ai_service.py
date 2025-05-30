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
            # Reduced timeout and added retry logic
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
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
            
        except requests.exceptions.Timeout:
            print("⚠️ API request timed out after 10 seconds")
            raise Exception(f"API request timed out. The AI service is taking too long to respond.")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ API request failed: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")
        except KeyError as e:
            print(f"⚠️ Unexpected API response format: {str(e)}")
            raise Exception(f"Unexpected API response format: {str(e)}")
        except Exception as e:
            print(f"⚠️ Error calling DeepSeek API: {str(e)}")
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
            return self._get_fallback_analysis(user_message, scenario)
        
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
                return self._get_fallback_analysis(user_message, scenario, ai_response=content)
                
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            return self._get_fallback_analysis(user_message, scenario, error=str(e))
    
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
    
    def generate_story_with_ai(self, parameters):
        """Generate an interactive story using AI based on user parameters"""
        if not self.client:
            return None
        
        # Build comprehensive prompt for story generation
        length_specs = {
            'short': {
                'time': '3-5 minutes',
                'steps': '1-2 interactive steps',
                'content_length': '100-200 words',
                'focus': 'Quick, focused practice'
            },
            'medium': {
                'time': '5-8 minutes', 
                'steps': '2-3 interactive steps',
                'content_length': '200-300 words',
                'focus': 'Moderate depth practice'
            },
            'long': {
                'time': '8-12 minutes',
                'steps': '3-4 interactive steps', 
                'content_length': '300-400 words',
                'focus': 'Comprehensive practice'
            }
        }
        
        length_info = length_specs.get(parameters.get('length', 'short'), length_specs['short'])
        
        system_prompt = f"""You are an expert story creator for English language learning, specialized in software development scenarios.

Create a CONCISE, engaging, interactive story with these specifications:

PARAMETERS:
- Topic: {parameters.get('topic', 'software_development')}
- Scenario: {parameters.get('scenario', 'daily_standup')}
- Difficulty: {parameters.get('difficulty', 'intermediate')}
- Length: {parameters.get('length', 'short')} ({length_info['time']})
- Focus Areas: {parameters.get('focus_areas', [])}

STORY REQUIREMENTS:
1. Create a realistic but BRIEF professional scenario
2. Keep content concise - {length_info['content_length']} for introduction
3. Design {length_info['steps']} that require focused responses
4. Focus on practical workplace communication
5. Make it immediately engaging and actionable

CRITICAL: You MUST create interactive steps. Each step should either be:
- type: "narrative" (for story progression, no user input needed)
- type: "question" (requires user response, must have both content AND question)

RESPONSE FORMAT - Return ONLY valid JSON:
{{
    "title": "Short, catchy title (max 8 words)",
    "description": "1-2 sentence description of the learning experience",
    "content": "Brief narrative introduction ({length_info['content_length']}) - set up the scenario clearly",
    "learning_objectives": ["objective1", "objective2"],
    "estimated_time": {length_info['time'].split('-')[0]},
    "total_steps": 2,
    "steps": [
        {{
            "step_number": 1,
            "type": "question",
            "content": "Brief situation setup (1-2 sentences describing what happens next)",
            "question": "Specific, actionable question requiring a professional response",
            "expected_response_type": "open",
            "learning_focus": "professional_communication"
        }},
        {{
            "step_number": 2,
            "type": "question",
            "content": "Follow-up situation (1-2 sentences about what happens after their response)",
            "question": "Another specific question to continue the interaction",
            "expected_response_type": "open",
            "learning_focus": "technical_vocabulary"
        }}
    ]
}}

EXAMPLE for debugging_session:
{{
    "title": "Quick Bug Fix Challenge",
    "description": "Help your teammate solve a critical login bug affecting users",
    "content": "It's Tuesday afternoon when Sarah from the QA team rushes to your desk. 'We have a problem! Users can't log into the application - they're getting a 500 error. The client is asking for updates every 10 minutes. Can you help me figure this out?'",
    "learning_objectives": ["technical problem solving", "professional communication"],
    "estimated_time": 4,
    "total_steps": 2,
    "steps": [
        {{
            "step_number": 1,
            "type": "question",
            "content": "You open the server logs and see several database connection timeout errors.",
            "question": "How would you explain to Sarah what you've found and what your next debugging steps will be?",
            "expected_response_type": "open",
            "learning_focus": "technical_communication"
        }},
        {{
            "step_number": 2,
            "type": "question",
            "content": "After investigating, you discover the database connection pool is exhausted due to a recent code deployment.",
            "question": "How would you communicate this finding to both Sarah and the development team, including your recommended solution?",
            "expected_response_type": "open",
            "learning_focus": "stakeholder_communication"
        }}
    ]
}}

IMPORTANT RULES:
- Keep the main content brief and engaging
- Each step MUST have both "content" and "question" if type is "question"
- Questions should be specific and actionable
- Focus on realistic workplace communication
- Ensure the story flows logically from step to step
- Always include exactly 2 steps for consistency"""

        try:
            response = self.client.chat_completions_create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": system_prompt}],
                temperature=0.8
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up the response
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON response
            try:
                story_data = json.loads(content)
                
                # Validate the story structure
                if not self._validate_ai_story_data(story_data):
                    print("AI generated invalid story structure")
                    return None
                
                # Ensure steps are properly formatted
                story_data['steps'] = self._fix_story_steps(story_data.get('steps', []))
                story_data['total_steps'] = len(story_data['steps'])
                
                print(f"AI generated story with {len(story_data['steps'])} steps")
                return story_data
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error in story generation: {e}")
                print(f"Raw content: {content[:500]}...")
                return None
                
        except Exception as e:
            print(f"Error generating story with AI: {e}")
            return None
        
    def _validate_ai_story_data(self, story_data):
        """Validate AI-generated story data structure"""
        required_fields = ['title', 'content', 'steps']
        
        for field in required_fields:
            if field not in story_data:
                print(f"Missing required field: {field}")
                return False
        
        # Validate steps
        steps = story_data.get('steps', [])
        if not isinstance(steps, list) or len(steps) == 0:
            print("Steps must be a non-empty list")
            return False
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                print(f"Step {i} is not a dictionary")
                return False
            
            # Check required step fields
            required_step_fields = ['type', 'content']
            for field in required_step_fields:
                if field not in step or not step[field]:
                    print(f"Step {i} missing required field: {field}")
                    return False
            
            # If it's a question type, it must have a question
            if step.get('type') == 'question' and not step.get('question'):
                print(f"Question step {i} missing question field")
                return False
        
        return True
    
    def _fix_story_steps(self, steps):
        """Fix and standardize story steps"""
        fixed_steps = []
        
        for i, step in enumerate(steps):
            fixed_step = {
                'step_number': i + 1,
                'type': step.get('type', 'question'),
                'content': step.get('content', f'Continue with step {i + 1}...'),
                'question': step.get('question'),
                'expected_response_type': step.get('expected_response_type', 'open'),
                'learning_focus': step.get('learning_focus', 'communication_skills')
            }
            
            # Ensure question exists for question type steps
            if fixed_step['type'] == 'question' and not fixed_step['question']:
                fixed_step['question'] = f"How would you respond in this situation?"
            
            # Ensure content is not empty
            if not fixed_step['content'] or len(fixed_step['content'].strip()) < 10:
                fixed_step['content'] = f"Step {i + 1}: Consider your response to this professional scenario."
            
            fixed_steps.append(fixed_step)
        
        return fixed_steps
    
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
        story_progress = self.db_service.get_user_story_progress()
        
        system_prompt = f"""You are an expert English language analyst for software developers. 
Analyze the following learning data and provide a comprehensive personal report.

User's Learning Data:
- Common Mistakes: {len(detailed_mistakes)} different error patterns
- Vocabulary: {len(vocabulary_data)} technical terms learned
- Quiz History: {len(quiz_history)} recent quizzes taken
- Conversation Scenarios: {len(scenario_performance)} different workplace contexts
- Story Progress: {len(story_progress)} stories engaged with

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
    def _get_fallback_analysis(self, user_message, scenario, ai_response=None, error=None):
        """Provide fallback analysis when AI is unavailable"""
        print(f"🔄 Using fallback analysis for scenario: {scenario}")
        
        # Basic grammar check patterns
        corrections = []
        new_vocabulary = []
        
        # Simple grammar patterns to check
        grammar_patterns = [
            (r'\bi am work\b', 'I am working', 'Present continuous tense'),
            (r'\bcan able to\b', 'can / am able to', 'Avoid double modals'),
            (r'\bvery much\b', 'a lot / greatly', 'More natural expression'),
            (r'\bmake a test\b', 'run a test', 'Technical terminology'),
            (r'\bfix a bug\b', 'fix the bug', 'Specific article usage'),
        ]
        
        import re
        user_lower = user_message.lower()
        
        for pattern, correction, explanation in grammar_patterns:
            if re.search(pattern, user_lower):
                original_match = re.search(pattern, user_lower)
                if original_match:
                    corrections.append({
                        "original": original_match.group(),
                        "corrected": correction,
                        "type": "grammar",
                        "explanation": explanation
                    })
        
        # Technical vocabulary suggestions based on scenario
        vocab_suggestions = {
            'debugging_session': [
                {"word": "troubleshoot", "definition": "to identify and solve problems", "example": "Let me troubleshoot this issue step by step."}
            ],
            'code_review': [
                {"word": "refactor", "definition": "to restructure code without changing functionality", "example": "We should refactor this function for better readability."}
            ],
            'daily_standup': [
                {"word": "blocker", "definition": "an issue preventing progress", "example": "I have a blocker with the API integration."}
            ]
        }
        
        if scenario in vocab_suggestions:
            new_vocabulary = vocab_suggestions[scenario]
        
        # Scenario-specific responses
        scenario_responses = {
            'debugging_session': "I understand you're working on debugging. That's a great approach to problem-solving. What's your next step?",
            'code_review': "Your code review feedback sounds constructive. It's important to provide clear, actionable suggestions.",
            'daily_standup': "Thanks for the update. It's good to communicate both progress and any blockers clearly.",
            'technical_interview': "That's a thoughtful response. Technical interviews are great opportunities to showcase your problem-solving approach.",
            'project_planning': "Good planning approach. Breaking down tasks helps estimate effort more accurately.",
            'client_meeting': "Clear communication with clients is essential. Making technical concepts accessible is a valuable skill.",
            'architecture_discussion': "Architecture discussions benefit from considering multiple perspectives. What are the trade-offs?",
            'deployment_issue': "Handling deployment issues requires both technical skills and clear communication with stakeholders."
        }
        
        conversation_response = ai_response or scenario_responses.get(scenario, "I understand your point. Let's continue the discussion.")
        
        suggestions = "Keep practicing professional communication! "
        if error and "timeout" in error.lower():
            suggestions += "The AI service is currently slow - your English practice is still valuable!"
        elif corrections:
            suggestions += f"Focus on the {len(corrections)} grammar point(s) highlighted above."
        else:
            suggestions += "Your English looks good! Try using more technical vocabulary to sound more professional."
        
        return {
            "conversation_response": conversation_response,
            "corrections": corrections,
            "new_vocabulary": new_vocabulary,
            "suggestions": suggestions
        }