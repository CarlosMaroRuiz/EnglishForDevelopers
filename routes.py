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
            story_type = data.get('story_type', 'generated')
            
            if story_type == 'generated':
                # Generate story using AI
                topic = data.get('topic', 'general')
                difficulty = data.get('difficulty', 'intermediate')
                scenario = data.get('scenario', 'daily_standup')
                
                story = self.business_service.generate_ai_story(topic, difficulty, scenario)
            else:
                # Manual story creation
                title = data.get('title', '')
                content = data.get('content', '')
                scenario = data.get('scenario', 'general')
                difficulty = data.get('difficulty', 'intermediate')
                
                if not title or not content:
                    return jsonify({"error": "Title and content are required"}), 400
                
                story = self.business_service.create_manual_story(title, content, scenario, difficulty)
            
            return jsonify({"success": True, "story_id": story['id']})
            
        except Exception as e:
            print(f"Error in create_story: {e}")
            return jsonify({"error": str(e)}), 500
    
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
                'length': data.get('length', 'medium'),
                'focus_areas': data.get('focus_areas', [])
            }
            
            story = self.business_service.generate_ai_story(**parameters)
            return jsonify(story)
            
        except Exception as e:
            print(f"Error in generate_story: {e}")
            return jsonify({"error": str(e)}), 500
    
    def complete_story(self, story_id):
        """Mark story as completed and generate summary"""
        try:
            completion_data = self.business_service.complete_story(story_id)
            return jsonify(completion_data)
            
        except Exception as e:
            print(f"Error in complete_story: {e}")
            return jsonify({"error": str(e)}), 500