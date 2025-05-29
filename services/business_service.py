class BusinessService:
    def __init__(self, db_service, ai_service):
        self.db_service = db_service
        self.ai_service = ai_service
    
    def process_conversation(self, user_message, scenario):
        """Process a user conversation message and return analysis"""
        # Analyze with AI
        analysis = self.ai_service.analyze_english_with_deepseek(user_message, scenario)
        
        # Save to database
        conversation_id = self.db_service.save_conversation(
            user_message,
            analysis.get('conversation_response', ''),
            analysis.get('corrections', []),
            scenario
        )
        
        # Save new vocabulary
        if analysis.get('new_vocabulary'):
            self.db_service.save_vocabulary(analysis.get('new_vocabulary', []))
        
        return analysis
    
    def generate_personalized_quiz(self):
        """Generate a personalized quiz based on user's mistakes"""
        # Get user's mistake patterns
        user_mistakes = self.db_service.get_user_mistakes(5)
        
        if not user_mistakes:
            # If no mistakes found, return default questions
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
                },
                {
                    "question": "What's the best way to describe a completed task?",
                    "option_a": "I have finish the implementation",
                    "option_b": "I have finished the implementation",
                    "option_c": "I have finishing the implementation",
                    "correct_answer": "b",
                    "explanation": "Present perfect requires the past participle 'finished'",
                    "category": "verb_tense"
                },
                {
                    "question": "How should you ask for help in a meeting?",
                    "option_a": "Can you help me with this issue?",
                    "option_b": "Can you help me to this issue?",
                    "option_c": "Can you help me for this issue?",
                    "correct_answer": "a",
                    "explanation": "'Help me with' is the correct preposition usage",
                    "category": "prepositions"
                },
                {
                    "question": "Which sentence is correct for describing progress?",
                    "option_a": "We are making good progresses",
                    "option_b": "We are making good progress",
                    "option_c": "We are making a good progresses",
                    "correct_answer": "b",
                    "explanation": "'Progress' is an uncountable noun, so no plural form",
                    "category": "grammar"
                }
            ]
            return {"questions": default_questions}
        
        # Generate questions based on user mistakes
        questions = self.ai_service.generate_quiz_questions(user_mistakes, 5)
        
        if not questions:
            raise Exception("Failed to generate quiz questions")
        
        return {"questions": questions}
    
    def process_quiz_submission(self, answers, questions):
        """Process quiz submission and return results"""
        if not answers or not questions:
            raise ValueError("Missing quiz data")
        
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
        self.db_service.save_quiz_result('grammar_practice', total_questions, correct_count, detailed_results, focused_areas)
        
        # Generate feedback message
        if score_percentage >= 90:
            feedback = "¡Excelente! Your English grammar is very strong."
        elif score_percentage >= 70:
            feedback = "¡Buen trabajo! You have a good understanding, but there's room for improvement."
        elif score_percentage >= 50:
            feedback = "Not bad, but you should focus more on the areas where you made mistakes."
        else:
            feedback = "Keep practicing! Focus on the grammar areas highlighted in your results."
        
        return {
            "score": score_percentage,
            "correct": correct_count,
            "total": total_questions,
            "feedback": feedback,
            "detailed_results": detailed_results,
            "focused_areas": list(set(focused_areas))
        }
    
    def generate_personal_report(self):
        """Generate comprehensive AI analysis report"""
        try:
            # Generate AI report
            ai_report = self.ai_service.generate_ai_personal_report()
            
            # Get additional analytics data
            analytics = self.db_service.get_user_analytics()
            
            return {
                'report': ai_report,
                'analytics': analytics
            }
            
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
            analytics = self.db_service.get_user_analytics()
            return {
                'report': fallback_report,
                'analytics': analytics
            }
    
    def generate_recommendations(self):
        """Generate personalized learning recommendations"""
        analytics = self.db_service.get_user_analytics()
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
    
    def get_analytics_data(self):
        """Get analytics data with recommendations"""
        analytics = self.db_service.get_user_analytics()
        recommendations = self.generate_recommendations()
        
        return {
            'analytics': analytics,
            'recommendations': recommendations
        }
    
    def get_vocabulary_data(self):
        """Get vocabulary data"""
        return self.db_service.get_vocabulary_list()
    
    def get_conversation_history(self):
        """Get conversation history"""
        return self.db_service.get_conversation_history()