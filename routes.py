from flask import render_template, request, jsonify
from config import Config

class Routes:
    def __init__(self, app, business_service):
        self.app = app
        self.business_service = business_service
        self.register_routes()
    
    def register_routes(self):
        """Register all application routes"""
        # Home routes
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        
        # Chat routes
        self.app.add_url_rule('/chat', 'chat', self.chat, methods=['GET'])
        self.app.add_url_rule('/send_message', 'send_message', self.send_message, methods=['POST'])
        
        # Quiz routes
        self.app.add_url_rule('/quiz', 'quiz', self.quiz, methods=['GET'])
        self.app.add_url_rule('/generate_quiz', 'generate_quiz', self.generate_quiz, methods=['POST'])
        self.app.add_url_rule('/submit_quiz', 'submit_quiz', self.submit_quiz, methods=['POST'])
        
        # Report routes
        self.app.add_url_rule('/report', 'personal_report', self.personal_report, methods=['GET'])
        
        # Analytics routes
        self.app.add_url_rule('/analytics', 'analytics', self.analytics, methods=['GET'])
        
        # Vocabulary routes
        self.app.add_url_rule('/vocabulary', 'vocabulary', self.vocabulary, methods=['GET'])
        
        # History routes
        self.app.add_url_rule('/history', 'history', self.history, methods=['GET'])
        
        # NEW: Stories routes
        self.app.add_url_rule('/stories', 'stories_list', self.stories_list, methods=['GET'])
        self.app.add_url_rule('/stories/<int:story_id>', 'story_detail', self.story_detail, methods=['GET'])
        self.app.add_url_rule('/stories/create', 'create_story', self.create_story, methods=['GET', 'POST'])
        self.app.add_url_rule('/stories/<int:story_id>/interact', 'story_interact', self.story_interact, methods=['POST'])
        self.app.add_url_rule('/stories/generate', 'generate_story', self.generate_story, methods=['POST'])
        self.app.add_url_rule('/stories/<int:story_id>/complete', 'complete_story', self.complete_story, methods=['POST'])
    
    def index(self):
        """Home page with scenario selection"""
        return render_template('index.html', scenarios=Config.WORK_SCENARIOS)
    
    def chat(self):
        """Chat interface for specific scenarios"""
        scenario = request.args.get('scenario', 'daily_standup')
        return render_template('chat.html', scenario=scenario)
    
    def send_message(self):
        """Process chat messages and return AI analysis"""
        try:
            data = request.json
            user_message = data.get('message', '')
            scenario = data.get('scenario', 'daily_standup')
            
            if not user_message.strip():
                return jsonify({"error": "Message cannot be empty"}), 400
            
            # Process conversation through business service
            analysis = self.business_service.process_conversation(user_message, scenario)
            
            return jsonify(analysis)
            
        except Exception as e:
            print(f"Error in send_message: {e}")
            return jsonify({
                "error": "Failed to process message",
                "conversation_response": "I'm sorry, there was an error processing your message. Please try again.",
                "corrections": [],
                "new_vocabulary": [],
                "suggestions": ""
            }), 500
    
    def quiz(self):
        """Quiz interface page"""
        return render_template('quiz.html')
    
    def generate_quiz(self):
        """Generate personalized quiz questions"""
        try:
            quiz_data = self.business_service.generate_personalized_quiz()
            return jsonify(quiz_data)
            
        except Exception as e:
            print(f"Error in generate_quiz: {e}")
            return jsonify({"error": str(e)}), 500
    
    def submit_quiz(self):
        """Submit quiz answers and get results"""
        try:
            data = request.json
            answers = data.get('answers', {})
            questions = data.get('questions', [])
            
            results = self.business_service.process_quiz_submission(answers, questions)
            return jsonify(results)
            
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            print(f"Error in submit_quiz: {e}")
            return jsonify({"error": "Failed to process quiz submission"}), 500
    
    def personal_report(self):
        """Generate and display comprehensive AI analysis report"""
        try:
            report_data = self.business_service.generate_personal_report()
            return render_template('report.html', 
                                 report=report_data['report'], 
                                 analytics=report_data['analytics'])
            
        except Exception as e:
            print(f"Error generating report: {e}")
            # Return error page or fallback
            return render_template('report.html', 
                                 report={
                                     "strengths": ["Error generating report"],
                                     "weaknesses": ["Please try again later"],
                                     "grammar_mastered": [],
                                     "grammar_needs_work": [],
                                     "focus_areas": [],
                                     "recommendations": [],
                                     "overall_assessment": "Unable to generate report at this time.",
                                     "learning_path": [],
                                     "personality_insights": []
                                 }, 
                                 analytics={
                                     'mistake_patterns': [],
                                     'today_conversations': 0,
                                     'vocabulary_count': 0,
                                     'problem_areas': [],
                                     'quiz_stats': {'avg_score': 0, 'total_quizzes': 0}
                                 })
    
    def analytics(self):
        """Analytics dashboard with progress tracking"""
        try:
            analytics_data = self.business_service.get_analytics_data()
            return render_template('analytics.html', 
                                 analytics=analytics_data['analytics'], 
                                 recommendations=analytics_data['recommendations'])
            
        except Exception as e:
            print(f"Error in analytics: {e}")
            return render_template('analytics.html', 
                                 analytics={
                                     'mistake_patterns': [],
                                     'today_conversations': 0,
                                     'vocabulary_count': 0,
                                     'problem_areas': [],
                                     'quiz_stats': {'avg_score': 0, 'total_quizzes': 0}
                                 },
                                 recommendations=[])
    
    def vocabulary(self):
        """Vocabulary management page"""
        try:
            vocab_list = self.business_service.get_vocabulary_data()
            return render_template('vocabulary.html', vocabulary=vocab_list)
            
        except Exception as e:
            print(f"Error in vocabulary: {e}")
            return render_template('vocabulary.html', vocabulary=[])
    
    def history(self):
        """Conversation history page"""
        try:
            conversations = self.business_service.get_conversation_history()
            return render_template('history.html', conversations=conversations)
            
        except Exception as e:
            print(f"Error in history: {e}")
            return render_template('history.html', conversations=[])
    
    # NEW: Stories routes
    def stories_list(self):
        """Display list of available stories"""
        try:
            stories = self.business_service.get_stories_list()
            user_progress = self.business_service.get_user_story_progress()
            return render_template('stories/list.html', stories=stories, user_progress=user_progress)
            
        except Exception as e:
            print(f"Error in stories_list: {e}")
            return render_template('stories/list.html', stories=[], user_progress={})
    
    def story_detail(self, story_id):
        """Display individual story with interaction"""
        try:
            story = self.business_service.get_story_by_id(story_id)
            if not story:
                return render_template('stories/not_found.html'), 404
            
            # Validate story has steps
            if not story.get('steps') or len(story['steps']) == 0:
                print(f"Story {story_id} has no steps, creating default steps")
                # Create default steps for this story
                default_steps = self._create_emergency_steps(story.get('scenario', 'general'))
                self.business_service.db_service.save_story_steps(story_id, default_steps)
                # Reload story
                story = self.business_service.get_story_by_id(story_id)
            
            user_progress = self.business_service.get_story_progress(story_id)
            interactions = self.business_service.get_story_interactions(story_id)
            
            return render_template('stories/detail.html', 
                                 story=story, 
                                 user_progress=user_progress,
                                 interactions=interactions)
            
        except Exception as e:
            print(f"Error in story_detail: {e}")
            return render_template('stories/error.html', error=str(e)), 500
    
    def create_story(self):
        """Create or generate new story"""
        if request.method == 'GET':
            return render_template('stories/create.html')
        
        try:
            data = request.json if request.is_json else request.form
            story_type = data.get('story_type', 'manual')
            
            print(f"Creating story of type: {story_type}")
            
            if story_type == 'generated':
                # Generate story using AI
                topic = data.get('topic', 'software_development')
                difficulty = data.get('difficulty', 'intermediate')
                scenario = data.get('scenario', 'daily_standup')
                length = data.get('length', 'short')
                focus_areas = data.get('focus_areas', [])
                
                story = self.business_service.generate_ai_story(
                    topic=topic, 
                    difficulty=difficulty, 
                    scenario=scenario,
                    length=length,
                    focus_areas=focus_areas
                )
                
                if not story:
                    raise Exception("AI story generation failed")
                    
            else:
                # Manual story creation
                title = data.get('title', '').strip()
                content = data.get('content', '').strip()
                scenario = data.get('scenario', 'general')
                difficulty = data.get('difficulty', 'intermediate')
                
                if not title or not content:
                    return jsonify({"error": "Title and content are required"}), 400
                
                if len(content) < 50:
                    return jsonify({"error": "Content must be at least 50 characters"}), 400
                
                story = self.business_service.create_manual_story(title, content, scenario, difficulty)
            
            if not story or not story.get('id'):
                raise Exception("Story creation failed - no ID returned")
            
            print(f"Successfully created story {story['id']}")
            
            return jsonify({"success": True, "story_id": story['id']})
            
        except Exception as e:
            print(f"Error in create_story: {e}")
            error_message = str(e)
            if "API" in error_message:
                error_message = "AI service is currently unavailable. Please try manual story creation."
            
            return jsonify({"error": error_message}), 500

    def _create_emergency_steps(self, scenario):
        """Create emergency steps when a story has none"""
        scenario_questions = {
            'debugging_session': "A bug has been reported. How would you approach investigating and solving this issue?",
            'code_review': "You need to review a colleague's code. How would you provide constructive feedback?",
            'technical_interview': "The interviewer asks about your problem-solving approach. How would you respond?",
            'daily_standup': "It's your turn in the standup. What would you share with the team?",
            'project_planning': "The team needs to plan the next sprint. What would you contribute to the discussion?",
            'client_meeting': "The client has questions about the project. How would you address their concerns?",
            'architecture_discussion': "The team is debating system architecture. What's your perspective?",
            'deployment_issue': "A deployment has failed. How would you handle this situation?"
        }
        
        question = scenario_questions.get(scenario, "How would you handle this professional situation?")
        
        return [
            {
                'step_number': 1,
                'type': 'question',
                'content': f"You're now in a {scenario.replace('_', ' ')} scenario. This is your opportunity to practice professional communication in English.",
                'question': question,
                'expected_response_type': 'open',
                'learning_focus': 'professional_communication'
            }
        ]
    
    def story_interact(self, story_id):
        """Handle user interactions with stories"""
        try:
            data = request.json
            user_response = data.get('response', '')
            current_step = data.get('current_step', 0)
            
            if not user_response.strip():
                return jsonify({"error": "Response cannot be empty"}), 400
            
            # Process interaction through business service
            result = self.business_service.process_story_interaction(
                story_id, user_response, current_step
            )
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Error in story_interact: {e}")
            return jsonify({"error": str(e)}), 500
    
    def generate_story(self):
        """Generate a new AI story"""
        try:
            data = request.json
            parameters = {
                'topic': data.get('topic', 'software development'),
                'difficulty': data.get('difficulty', 'intermediate'),
                'scenario': data.get('scenario', 'daily_standup'),
                'length': data.get('length', 'short'),  # Default to short for better success rate
                'focus_areas': data.get('focus_areas', ['technical_vocabulary', 'communication_skills'])
            }
            
            print(f"Generating story with parameters: {parameters}")
            
            story = self.business_service.generate_ai_story(**parameters)
            
            if not story:
                raise Exception("Failed to generate story - AI service returned None")
            
            if not story.get('id'):
                raise Exception("Generated story has no ID")
            
            # Validate the story has steps
            if not story.get('steps') or len(story['steps']) == 0:
                print("Generated story has no steps, creating default steps")
                default_steps = self._create_emergency_steps(parameters['scenario'])
                self.business_service.db_service.save_story_steps(story['id'], default_steps)
                story['steps'] = default_steps
                story['total_steps'] = len(default_steps)
            
            print(f"Successfully generated story {story['id']} with {len(story.get('steps', []))} steps")
            
            return jsonify(story)
            
        except Exception as e:
            print(f"Error in generate_story: {e}")
            # Return a meaningful error message
            error_message = str(e)
            if "API" in error_message:
                error_message = "AI service is currently unavailable. Please try again or create a manual story."
            elif "timeout" in error_message.lower():
                error_message = "Story generation timed out. Please try with a shorter story length."
            
            return jsonify({"error": error_message}), 500
    
    def complete_story(self, story_id):
        """Mark story as completed and generate summary"""
        try:
            completion_data = self.business_service.complete_story(story_id)
            return jsonify(completion_data)
            
        except Exception as e:
            print(f"Error in complete_story: {e}")
            return jsonify({"error": str(e)}), 500