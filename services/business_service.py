import json
from .ai_service import AIService
from .database import DatabaseService
import random

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
        
        # NEW: Story recommendations
        if analytics.get('story_stats', {}).get('completed_stories', 0) < 3:
            recommendations.append({
                'type': 'story_practice',
                'content': "Try reading interactive stories to improve your comprehension and vocabulary",
                'priority': 2
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
    
    # NEW: Stories methods
    def get_stories_list(self):
        """Get list of available stories with enhanced information"""
        stories = self.db_service.get_stories_list()
        
        # Convert to list of dictionaries with additional info
        enhanced_stories = []
        for story in stories:
            story_dict = {
                'id': story[0],
                'title': story[1],
                'description': story[2],
                'scenario': story[3],
                'difficulty_level': story[4],
                'topic': story[5],
                'estimated_time': story[6],
                'total_steps': story[7],
                'created_at': story[8]
            }
            enhanced_stories.append(story_dict)
        
        return enhanced_stories
    
    def get_story_by_id(self, story_id):
        """Get a specific story by ID"""
        return self.db_service.get_story_by_id(story_id)
    
    def get_user_story_progress(self):
        """Get user progress for all stories"""
        return self.db_service.get_user_story_progress()
    
    def get_story_progress(self, story_id):
        """Get user progress for a specific story"""
        return self.db_service.get_story_progress(story_id)
    
    def get_story_interactions(self, story_id):
        """Get user interactions for a specific story"""
        return self.db_service.get_story_interactions(story_id)
    
    def generate_ai_story(self, topic='software_development', difficulty='intermediate', 
                         scenario='daily_standup', length='medium', focus_areas=None, 
                         additional_preferences=''):
        """Generate a new AI story based on parameters"""
        if not self.ai_service.client:
            return self._create_fallback_story(topic, difficulty, scenario)
        
        # Prepare parameters for AI generation
        parameters = {
            'topic': topic,
            'scenario': scenario,
            'difficulty': difficulty,
            'length': length,
            'focus_areas': focus_areas or ['technical_vocabulary', 'communication_skills'],
            'additional_preferences': additional_preferences
        }
        
        # Generate story using AI service
        story_data = self.ai_service.generate_story_with_ai(parameters)
        
        if not story_data:
            # Fallback to manual creation if AI fails
            return self._create_fallback_story(topic, difficulty, scenario)
        
        try:
            # Save story to database
            story_id = self.db_service.save_story(
                title=story_data.get('title', 'Generated Story'),
                description=story_data.get('description', ''),
                content=story_data.get('content', ''),
                story_type='generated',
                scenario=scenario,
                difficulty_level=difficulty,
                topic=topic,
                estimated_time=story_data.get('estimated_time', 15),
                learning_objectives=story_data.get('learning_objectives', [])
            )
            
            # Save story steps
            steps = story_data.get('steps', [])
            if steps:
                # Ensure step numbers are correct
                for i, step in enumerate(steps):
                    step['step_number'] = i + 1
                self.db_service.save_story_steps(story_id, steps)
            
            # Return story with ID
            story_data['id'] = story_id
            return story_data
            
        except Exception as e:
            print(f"Error saving AI-generated story: {e}")
            return self._create_fallback_story(topic, difficulty, scenario)
    
    def _create_fallback_story(self, topic, difficulty, scenario, length='short'):
        """Create a fallback story when AI generation fails"""
        fallback_stories = {
            'debugging_session': {
                'short': {
                    'title': 'Quick Bug Fix',
                    'description': 'Help solve a simple bug that\'s blocking the team (3-4 minutes)',
                    'content': 'It\'s 2 PM and you\'re in the middle of coding when your teammate Sarah rushes over. "Hey, we have a small issue with the login form - users can\'t submit it. Can you take a quick look?"',
                    'estimated_time': 4,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'Sarah shows you her screen with the login form.',
                            'question': 'What would be your first question to understand the problem better?',
                            'learning_focus': 'problem-solving communication'
                        },
                        {
                            'type': 'question',
                            'content': 'After checking the browser console, you see a JavaScript error.',
                            'question': 'How would you explain this technical issue to Sarah in simple terms?',
                            'learning_focus': 'technical explanations'
                        }
                    ]
                },
                'medium': {
                    'title': 'The Mystery Bug Hunt',
                    'description': 'Help solve a critical production bug that\'s affecting users (5-7 minutes)',
                    'content': 'It\'s Monday morning and you arrive at the office to find the development team in crisis mode. The main application is experiencing a strange bug that only affects certain users, and nobody can figure out why.',
                    'estimated_time': 6,
                    'steps': [
                        {
                            'type': 'narrative',
                            'content': 'You check the error logs and notice that the bug seems to occur only for users with specific account types.',
                            'question': None,
                            'learning_focus': 'technical vocabulary'
                        },
                        {
                            'type': 'question',
                            'content': 'Your team lead asks you to investigate the issue.',
                            'question': 'How would you approach debugging this problem? Describe your first steps.',
                            'learning_focus': 'problem-solving communication'
                        },
                        {
                            'type': 'question',
                            'content': 'After investigating, you find the root cause in the authentication module.',
                            'question': 'How would you explain this technical issue to non-technical stakeholders?',
                            'learning_focus': 'technical explanations'
                        }
                    ]
                }
            },
            'code_review': {
                'short': {
                    'title': 'Quick Code Feedback',
                    'description': 'Review a small pull request and provide constructive feedback (3-4 minutes)',
                    'content': 'Your colleague Alex just submitted a small pull request with a new utility function. It\'s your turn to review it.',
                    'estimated_time': 3,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'Looking at the code, you notice the function works but could be improved.',
                            'question': 'How would you give constructive feedback without being too critical?',
                            'learning_focus': 'diplomatic communication'
                        }
                    ]
                },
                'medium': {
                    'title': 'The Diplomatic Code Review',
                    'description': 'Navigate a challenging code review with a senior developer (5-6 minutes)',
                    'content': 'You\'ve been assigned to review a pull request from a senior developer on your team. The code works, but you\'ve identified several areas that could be improved.',
                    'estimated_time': 5,
                    'steps': [
                        {
                            'type': 'narrative',
                            'content': 'Looking at the code, you notice some potential performance issues and unclear variable names.',
                            'question': None,
                            'learning_focus': 'technical analysis'
                        },
                        {
                            'type': 'question',
                            'content': 'You need to provide feedback to someone more experienced than you.',
                            'question': 'How would you diplomatically suggest improvements to a senior developer?',
                            'learning_focus': 'diplomatic communication'
                        }
                    ]
                }
            },
            'technical_interview': {
                'short': {
                    'title': 'Quick Interview Question',
                    'description': 'Answer a common technical interview question (2-3 minutes)',
                    'content': 'You\'re in a phone screening for a developer position. The interviewer asks you to explain a basic concept.',
                    'estimated_time': 3,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'The interviewer asks: "Can you explain what an API is in simple terms?"',
                            'question': 'How would you explain an API to someone who might not be technical?',
                            'learning_focus': 'technical explanations'
                        }
                    ]
                },
                'medium': {
                    'title': 'The Dream Job Interview',
                    'description': 'Ace your technical interview at a top tech company (5-6 minutes)',
                    'content': 'You\'re sitting in the lobby of your dream company, waiting for your technical interview to begin. You\'ve prepared for months, and now it\'s time to show what you can do.',
                    'estimated_time': 5,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'The interviewer asks you to introduce yourself.',
                            'question': 'How would you describe your background and experience in a compelling way?',
                            'learning_focus': 'self-presentation'
                        },
                        {
                            'type': 'question',
                            'content': 'They ask about a challenging project you worked on.',
                            'question': 'Describe a difficult technical problem you solved. Focus on your thought process.',
                            'learning_focus': 'technical storytelling'
                        }
                    ]
                }
            },
            'daily_standup': {
                'short': {
                    'title': 'First Day Standup',
                    'description': 'Participate in your first daily standup meeting (3-4 minutes)',
                    'content': 'It\'s your first day at a new company and you\'re about to join the daily standup meeting.',
                    'estimated_time': 3,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'The team lead asks you to introduce yourself briefly.',
                            'question': 'How would you introduce yourself to the team in a standup format?',
                            'learning_focus': 'introductions'
                        }
                    ]
                },
                'medium': {
                    'title': 'Standup Challenges',
                    'description': 'Navigate a daily standup with blockers and updates (4-5 minutes)',
                    'content': 'It\'s Tuesday morning and time for the daily standup. You have both progress to report and a blocker that needs team input.',
                    'estimated_time': 4,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'It\'s your turn to give updates.',
                            'question': 'How would you report your yesterday\'s progress, today\'s plan, and your blocker?',
                            'learning_focus': 'structured communication'
                        },
                        {
                            'type': 'question',
                            'content': 'A teammate offers to help with your blocker.',
                            'question': 'How would you accept their help and coordinate the next steps?',
                            'learning_focus': 'collaboration'
                        }
                    ]
                }
            },
            'project_planning': {
                'short': {
                    'title': 'Feature Estimate',
                    'description': 'Give time estimates for a new feature (2-3 minutes)',
                    'content': 'Your manager asks you to estimate how long it would take to implement a new search feature.',
                    'estimated_time': 3,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'You need to break down the feature into smaller tasks.',
                            'question': 'How would you explain your estimation process and timeline?',
                            'learning_focus': 'project communication'
                        }
                    ]
                }
            },
            'client_meeting': {
                'short': {
                    'title': 'Client Check-in',
                    'description': 'Update a client on project progress (3-4 minutes)',
                    'content': 'You\'re in a brief call with a client to update them on the project status.',
                    'estimated_time': 3,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'The client asks about the current progress and next milestones.',
                            'question': 'How would you explain the technical progress in business terms?',
                            'learning_focus': 'client communication'
                        }
                    ]
                }
            },
            'deployment_issue': {
                'short': {
                    'title': 'Quick Hotfix',
                    'description': 'Handle a minor deployment issue quickly (3-4 minutes)',
                    'content': 'A small issue was discovered right after deployment. It\'s not critical, but needs to be addressed.',
                    'estimated_time': 3,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'You need to inform the team about the issue and your plan to fix it.',
                            'question': 'How would you communicate the issue and your solution approach?',
                            'learning_focus': 'incident communication'
                        }
                    ]
                }
            },
            'architecture_discussion': {
                'short': {
                    'title': 'Quick Architecture Decision',
                    'description': 'Discuss a simple architectural choice (3-4 minutes)',
                    'content': 'The team needs to decide between two approaches for implementing a new feature.',
                    'estimated_time': 3,
                    'steps': [
                        {
                            'type': 'question',
                            'content': 'You need to present the pros and cons of each approach.',
                            'question': 'How would you explain the trade-offs in a clear and concise way?',
                            'learning_focus': 'technical comparison'
                        }
                    ]
                }
            }
        }
        
        # Get fallback story based on scenario and length
        scenario_stories = fallback_stories.get(scenario, fallback_stories['debugging_session'])
        story_template = scenario_stories.get(length, scenario_stories.get('short', scenario_stories['short']))
        
        # Save to database
        story_id = self.db_service.save_story(
            title=story_template['title'],
            description=story_template['description'],
            content=story_template['content'],
            story_type='fallback',
            scenario=scenario,
            difficulty_level=difficulty,
            topic=topic,
            estimated_time=story_template['estimated_time'],
            learning_objectives=['professional communication', 'technical vocabulary']
        )
        
        # Save steps
        if story_template.get('steps'):
            self.db_service.save_story_steps(story_id, story_template['steps'])
        
        story_template['id'] = story_id
        story_template['learning_objectives'] = ['professional communication', 'technical vocabulary']
        
        return story_template
    
    def create_manual_story(self, title, content, scenario, difficulty):
        """Create a manually entered story"""
        story_id = self.db_service.save_story(
            title=title,
            description=f'A custom story about {scenario.replace("_", " ")}',
            content=content,
            story_type='manual',
            scenario=scenario,
            difficulty_level=difficulty,
            topic='custom',
            estimated_time=10,
            learning_objectives=['reading comprehension', 'vocabulary building']
        )
        
        # Create basic steps for manual story
        steps = [
            {
                'type': 'narrative',
                'content': content,
                'question': None,
                'learning_focus': 'reading comprehension'
            },
            {
                'type': 'question',
                'content': 'After reading this story...',
                'question': 'What are the main points you learned from this scenario?',
                'learning_focus': 'comprehension and reflection'
            }
        ]
        
        self.db_service.save_story_steps(story_id, steps)
        
        return {
            'id': story_id,
            'title': title,
            'content': content,
            'scenario': scenario,
            'difficulty_level': difficulty
        }
    
    def process_story_interaction(self, story_id, user_response, current_step):
        """Process user interaction with a story step"""
        # Get story details
        story = self.db_service.get_story_by_id(story_id)
        if not story:
            raise Exception("Story not found")
        
        # Analyze user response with AI
        ai_analysis = self.ai_service.analyze_english_with_deepseek(
            user_response, 
            f"story_interaction_{story['scenario']}"
        )
        
        # Calculate interaction score based on response quality
        interaction_score = self._calculate_interaction_score(
            user_response, ai_analysis, current_step
        )
        
        # Save interaction to database
        interaction_id = self.db_service.save_story_interaction(
            story_id=story_id,
            step_number=current_step,
            user_response=user_response,
            ai_feedback=ai_analysis.get('conversation_response', ''),
            corrections=ai_analysis.get('corrections', []),
            new_vocabulary=ai_analysis.get('new_vocabulary', []),
            interaction_score=interaction_score
        )
        
        # Save new vocabulary to main vocabulary table
        if ai_analysis.get('new_vocabulary'):
            self.db_service.save_vocabulary(ai_analysis['new_vocabulary'])
        
        # Determine next step
        next_step = current_step + 1
        is_story_complete = next_step > len(story.get('steps', []))
        
        result = {
            'interaction_id': interaction_id,
            'ai_feedback': ai_analysis.get('conversation_response', ''),
            'corrections': ai_analysis.get('corrections', []),
            'new_vocabulary': ai_analysis.get('new_vocabulary', []),
            'suggestions': ai_analysis.get('suggestions', ''),
            'interaction_score': interaction_score,
            'next_step': next_step if not is_story_complete else None,
            'is_complete': is_story_complete,
            'story_progress': self._calculate_story_progress(story_id, next_step, len(story.get('steps', [])))
        }
        
        return result
    
    def _calculate_interaction_score(self, user_response, ai_analysis, step):
        """Calculate a score for the user's interaction"""
        score = 70  # Base score
        
        # Length bonus (encourages detailed responses)
        word_count = len(user_response.split())
        if word_count >= 20:
            score += 10
        elif word_count >= 10:
            score += 5
        
        # Grammar quality (fewer corrections = higher score)
        corrections_count = len(ai_analysis.get('corrections', []))
        if corrections_count == 0:
            score += 20
        elif corrections_count <= 2:
            score += 10
        elif corrections_count <= 5:
            score += 5
        
        # Vocabulary usage (new vocabulary = bonus)
        new_vocab_count = len(ai_analysis.get('new_vocabulary', []))
        score += new_vocab_count * 5
        
        # Cap at 100
        return min(score, 100)
    
    def _calculate_story_progress(self, story_id, current_step, total_steps):
        """Calculate story completion progress"""
        if total_steps == 0:
            return 100.0
        
        progress = (current_step / total_steps) * 100
        return min(progress, 100.0)
    
    def complete_story(self, story_id):
        """Mark story as completed and generate completion summary"""
        # Mark as completed in database
        self.db_service.complete_story(story_id)
        
        # Get story interactions for summary
        interactions = self.db_service.get_story_interactions(story_id)
        story = self.db_service.get_story_by_id(story_id)
        
        # Calculate summary statistics
        total_interactions = len(interactions)
        avg_score = sum(i['interaction_score'] for i in interactions) / total_interactions if total_interactions > 0 else 0
        total_corrections = sum(len(i.get('corrections', [])) for i in interactions)
        total_new_vocab = sum(len(i.get('new_vocabulary', [])) for i in interactions)
        
        # Generate completion summary
        completion_data = {
            'story_title': story['title'],
            'completion_time': self._get_story_completion_time(story_id),
            'total_interactions': total_interactions,
            'average_score': round(avg_score, 1),
            'total_corrections': total_corrections,
            'new_vocabulary_learned': total_new_vocab,
            'story_difficulty': story['difficulty_level'],
            'congratulations_message': self._generate_congratulations_message(avg_score, story['difficulty_level']),
            'next_recommendations': self._get_next_story_recommendations(story['scenario'], story['difficulty_level'])
        }
        
        return completion_data
    
    def _get_story_completion_time(self, story_id):
        """Calculate time spent on story"""
        progress = self.db_service.get_story_progress(story_id)
        if progress and progress.get('started_at') and progress.get('completed_at'):
            # This would need proper time calculation
            return "15 minutes"  # Placeholder
        return "Unknown"
    
    def _generate_congratulations_message(self, avg_score, difficulty):
        """Generate a personalized congratulations message"""
        messages = {
            'beginner': {
                90: "Outstanding work! You've mastered this beginner story with exceptional English skills!",
                70: "Great job! You completed the story well. Keep practicing to improve even more!",
                50: "Good effort! You're making progress. Try more stories to build your confidence!"
            },
            'intermediate': {
                90: "Excellent! Your English skills are impressive for this intermediate level!",
                70: "Well done! You handled this intermediate story very well!",
                50: "Nice work! Intermediate stories are challenging, and you're improving!"
            },
            'advanced': {
                90: "Exceptional! You've demonstrated advanced English proficiency!",
                70: "Great performance! Your advanced English skills are showing!",
                50: "Good work! Advanced content is tough - keep challenging yourself!"
            }
        }
        
        level_messages = messages.get(difficulty, messages['intermediate'])
        
        if avg_score >= 90:
            return level_messages[90]
        elif avg_score >= 70:
            return level_messages[70]
        else:
            return level_messages[50]
    
    def _get_next_story_recommendations(self, scenario, difficulty):
        """Get recommendations for next stories to try"""
        recommendations = []
        
        # Same scenario, higher difficulty
        if difficulty == 'beginner':
            recommendations.append(f"Try an intermediate {scenario.replace('_', ' ')} story")
        elif difficulty == 'intermediate':
            recommendations.append(f"Challenge yourself with an advanced {scenario.replace('_', ' ')} story")
        
        # Different scenarios, same difficulty
        other_scenarios = ['debugging_session', 'code_review', 'technical_interview', 'daily_standup']
        current_scenario = scenario
        if current_scenario in other_scenarios:
            other_scenarios.remove(current_scenario)
        
        if other_scenarios:
            random_scenario = random.choice(other_scenarios)
            recommendations.append(f"Explore {random_scenario.replace('_', ' ')} stories")
        
        # Grammar quiz recommendation
        recommendations.append("Take a grammar quiz to reinforce what you learned")
        
        return recommendations[:3]  # Return top 3 recommendations