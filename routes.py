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