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
            return self._create_fallback_story(topic, difficulty, scenario, length)
        
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
            return self._create_fallback_story(topic, difficulty, scenario, length)
        
        try:
            # Validate story data structure
            if not self._validate_story_data(story_data):
                print("Invalid story data from AI, using fallback")
                return self._create_fallback_story(topic, difficulty, scenario, length)
            
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
            
            # Save story steps - CRITICAL FIX
            steps = story_data.get('steps', [])
            if steps:
                # Ensure step numbers are correct and validate each step
                validated_steps = []
                for i, step in enumerate(steps):
                    validated_step = self._validate_and_fix_step(step, i + 1)
                    validated_steps.append(validated_step)
                
                self.db_service.save_story_steps(story_id, validated_steps)
            else:
                # If no steps, create a basic interaction step
                default_steps = self._create_default_steps(scenario)
                self.db_service.save_story_steps(story_id, default_steps)
            
            # Return story with ID and ensure it has steps
            story_data['id'] = story_id
            story_data['steps'] = validated_steps if steps else default_steps
            return story_data
            
        except Exception as e:
            print(f"Error saving AI-generated story: {e}")
            return self._create_fallback_story(topic, difficulty, scenario, length)
        
    def _validate_story_data(self, story_data):
        """Validate that story data has required fields"""
        required_fields = ['title', 'content']
        for field in required_fields:
            if not story_data.get(field):
                return False
        return True
    
    def _create_default_steps(self, scenario):
        """Create default steps when AI doesn't generate them"""
        scenario_prompts = {
            'debugging_session': "You've identified the issue. How would you explain the solution to your team?",
            'code_review': "You've reviewed the code. What feedback would you provide to the developer?",
            'technical_interview': "The interviewer asks about your experience. How would you respond?",
            'daily_standup': "It's your turn in the standup. What would you share with the team?",
            'project_planning': "The team needs your input on the timeline. What would you suggest?",
            'client_meeting': "The client has questions about the implementation. How would you address them?",
            'architecture_discussion': "The team is debating the architecture. What's your perspective?",
            'deployment_issue': "The deployment has failed. How would you communicate this to stakeholders?"
        }
        
        default_question = scenario_prompts.get(scenario, "How would you handle this professional situation?")
        
        return [
            {
                'step_number': 1,
                'type': 'question',
                'content': f"Now it's your turn to respond. Think about how you would handle this {scenario.replace('_', ' ')} situation professionally.",
                'question': default_question,
                'expected_response_type': 'open',
                'learning_focus': 'professional_communication'
            }
        ]
    
    def _validate_and_fix_step(self, step, step_number):
        """Validate and fix a story step"""
        validated_step = {
            'step_number': step_number,
            'type': step.get('type', 'narrative'),
            'content': step.get('content', 'Continue with the story...'),
            'question': step.get('question'),
            'expected_response_type': step.get('expected_response_type', 'open'),
            'learning_focus': step.get('learning_focus', 'communication_skills')
        }
        
        # Ensure content is not empty
        if not validated_step['content'] or len(validated_step['content'].strip()) < 10:
            validated_step['content'] = f"Step {step_number}: Continue with your response to this scenario."
        
        return validated_step
    

    
    def _create_fallback_story(self, topic, difficulty, scenario, length='short'):
        """Create a fallback story when AI generation fails"""
        fallback_stories = {
            'debugging_session': {
                'short': {
                    'title': 'Quick Bug Fix',
                    'description': 'Help solve a simple bug that\'s blocking the team (3-4 minutes)',
                    'content': 'It\'s 2 PM and you\'re in the middle of coding when your teammate Sarah rushes over. "Hey, we have a small issue with the login form - users can\'t submit it. Can you take a quick look?" You check the browser console and see a JavaScript error.',
                    'estimated_time': 4,
                    'steps': [
                        {
                            'step_number': 1,
                            'type': 'question',
                            'content': 'Sarah shows you her screen with the login form error.',
                            'question': 'What would be your first question to understand the problem better?',
                            'expected_response_type': 'open',
                            'learning_focus': 'problem-solving communication'
                        },
                        {
                            'step_number': 2,
                            'type': 'question',
                            'content': 'After investigating, you find the issue is a missing validation function.',
                            'question': 'How would you explain this technical issue to Sarah in simple terms?',
                            'expected_response_type': 'open',
                            'learning_focus': 'technical explanations'
                        }
                    ]
                },
                'medium': {
                    'title': 'The Mystery Bug Hunt',
                    'description': 'Help solve a critical production bug affecting users (5-7 minutes)',
                    'content': 'It\'s Monday morning and you arrive at the office to find the development team in crisis mode. The main application is experiencing a strange bug that only affects certain users, and nobody can figure out why. The error logs show inconsistent patterns.',
                    'estimated_time': 6,
                    'steps': [
                        {
                            'step_number': 1,
                            'type': 'narrative',
                            'content': 'You check the error logs and notice that the bug seems to occur only for users with specific account types.',
                            'question': None,
                            'expected_response_type': 'none',
                            'learning_focus': 'technical vocabulary'
                        },
                        {
                            'step_number': 2,
                            'type': 'question',
                            'content': 'Your team lead asks you to investigate the issue.',
                            'question': 'How would you approach debugging this problem? Describe your first steps.',
                            'expected_response_type': 'open',
                            'learning_focus': 'problem-solving communication'
                        },
                        {
                            'step_number': 3,
                            'type': 'question',
                            'content': 'After investigating, you find the root cause in the authentication module.',
                            'question': 'How would you explain this technical issue to non-technical stakeholders?',
                            'expected_response_type': 'open',
                            'learning_focus': 'technical explanations'
                        }
                    ]
                },
                'long': {
                    'title': 'Critical System Debugging',
                    'description': 'Lead a complex debugging session for a system-wide issue (8-10 minutes)',
                    'content': 'The entire production system is experiencing intermittent failures. Multiple teams are affected, and you\'ve been asked to lead the debugging effort. Customer complaints are increasing, and management is asking for updates every hour.',
                    'estimated_time': 9,
                    'steps': [
                        {
                            'step_number': 1,
                            'type': 'question',
                            'content': 'You need to organize the debugging effort across multiple teams.',
                            'question': 'How would you structure the investigation and coordinate with different teams?',
                            'expected_response_type': 'open',
                            'learning_focus': 'leadership_communication'
                        },
                        {
                            'step_number': 2,
                            'type': 'question',
                            'content': 'Management asks for a status update in 30 minutes.',
                            'question': 'How would you communicate the current situation to management?',
                            'expected_response_type': 'open',
                            'learning_focus': 'stakeholder_communication'
                        },
                        {
                            'step_number': 3,
                            'type': 'question',
                            'content': 'You discover the issue is related to a recent database migration.',
                            'question': 'How would you explain the root cause and propose a solution?',
                            'expected_response_type': 'open',
                            'learning_focus': 'technical_explanations'
                        },
                        {
                            'step_number': 4,
                            'type': 'question',
                            'content': 'The fix is implemented and the system is stable.',
                            'question': 'How would you conduct a post-mortem discussion with the team?',
                            'expected_response_type': 'open',
                            'learning_focus': 'retrospective_communication'
                        }
                    ]
                }
            },
            'code_review': {
                'short': {
                    'title': 'Quick Code Feedback',
                    'description': 'Review a small pull request and provide constructive feedback (3-4 minutes)',
                    'content': 'Your colleague Alex just submitted a small pull request with a new utility function. It\'s your turn to review it. The code works but could be improved.',
                    'estimated_time': 3,
                    'steps': [
                        {
                            'step_number': 1,
                            'type': 'question',
                            'content': 'Looking at the code, you notice the function works but could be improved.',
                            'question': 'How would you give constructive feedback without being too critical?',
                            'expected_response_type': 'open',
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
                            'step_number': 1,
                            'type': 'narrative',
                            'content': 'Looking at the code, you notice some potential performance issues and unclear variable names.',
                            'question': None,
                            'expected_response_type': 'none',
                            'learning_focus': 'technical analysis'
                        },
                        {
                            'step_number': 2,
                            'type': 'question',
                            'content': 'You need to provide feedback to someone more experienced than you.',
                            'question': 'How would you diplomatically suggest improvements to a senior developer?',
                            'expected_response_type': 'open',
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
                            'step_number': 1,
                            'type': 'question',
                            'content': 'The interviewer asks: "Can you explain what an API is in simple terms?"',
                            'question': 'How would you explain an API to someone who might not be technical?',
                            'expected_response_type': 'open',
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
                            'step_number': 1,
                            'type': 'question',
                            'content': 'The interviewer asks you to introduce yourself.',
                            'question': 'How would you describe your background and experience in a compelling way?',
                            'expected_response_type': 'open',
                            'learning_focus': 'self-presentation'
                        },
                        {
                            'step_number': 2,
                            'type': 'question',
                            'content': 'They ask about a challenging project you worked on.',
                            'question': 'Describe a difficult technical problem you solved. Focus on your thought process.',
                            'expected_response_type': 'open',
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
                            'step_number': 1,
                            'type': 'question',
                            'content': 'The team lead asks you to introduce yourself briefly.',
                            'question': 'How would you introduce yourself to the team in a standup format?',
                            'expected_response_type': 'open',
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
                            'step_number': 1,
                            'type': 'question',
                            'content': 'It\'s your turn to give updates.',
                            'question': 'How would you report your yesterday\'s progress, today\'s plan, and your blocker?',
                            'expected_response_type': 'open',
                            'learning_focus': 'structured communication'
                        },
                        {
                            'step_number': 2,
                            'type': 'question',
                            'content': 'A teammate offers to help with your blocker.',
                            'question': 'How would you accept their help and coordinate the next steps?',
                            'expected_response_type': 'open',
                            'learning_focus': 'collaboration'
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
        
        # Save steps - CRITICAL: Ensure steps are always saved
        steps = story_template.get('steps', [])
        if not steps:
            steps = self._create_default_steps(scenario)
        
        self.db_service.save_story_steps(story_id, steps)
        
        # Return complete story data
        story_template['id'] = story_id
        story_template['learning_objectives'] = ['professional communication', 'technical vocabulary']
        story_template['steps'] = steps  # Ensure steps are included
        
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
        try:
            # Mark as completed in database
            self.db_service.complete_story(story_id)
            
            # Get story interactions for summary
            interactions = self.db_service.get_story_interactions(story_id)
            story = self.db_service.get_story_by_id(story_id)
            
            # Validate data
            if not story:
                print(f"⚠️ Story {story_id} not found")
                return self._get_fallback_completion_data(story_id)
            
            if not interactions:
                print(f"⚠️ No interactions found for story {story_id}")
                interactions = []
            
            if not isinstance(interactions, list):
                print(f"⚠️ Interactions is not a list: {type(interactions)}")
                interactions = []
            
            # Calculate summary statistics
            total_interactions = len(interactions)
            
            # Calculate average score with safe handling
            scores = []
            for interaction in interactions:
                score = interaction.get('interaction_score', 0) if isinstance(interaction, dict) else 0
                if score and isinstance(score, (int, float)):
                    scores.append(score)
            
            avg_score = sum(scores) / len(scores) if scores else 75  # Default to 75 if no scores
            
            # Calculate corrections with safe handling
            total_corrections = 0
            for interaction in interactions:
                if isinstance(interaction, dict):
                    corrections = interaction.get('corrections')
                    if corrections:
                        try:
                            if isinstance(corrections, str):
                                corrections_list = json.loads(corrections)
                            elif isinstance(corrections, list):
                                corrections_list = corrections
                            else:
                                corrections_list = []
                            
                            total_corrections += len(corrections_list)
                        except (json.JSONDecodeError, TypeError):
                            # Skip invalid corrections data
                            continue
            
            # Calculate vocabulary with safe handling
            total_new_vocab = 0
            for interaction in interactions:
                if isinstance(interaction, dict):
                    vocab = interaction.get('new_vocabulary')
                    if vocab:
                        try:
                            if isinstance(vocab, str):
                                vocab_list = json.loads(vocab)
                            elif isinstance(vocab, list):
                                vocab_list = vocab
                            else:
                                vocab_list = []
                            
                            total_new_vocab += len(vocab_list)
                        except (json.JSONDecodeError, TypeError):
                            # Skip invalid vocabulary data
                            continue
            
            # Generate completion summary
            completion_data = {
                'story_title': story.get('title', 'Completed Story'),
                'completion_time': self._get_story_completion_time(story_id),
                'total_interactions': total_interactions,
                'average_score': round(avg_score, 1),
                'total_corrections': total_corrections,
                'new_vocabulary_learned': total_new_vocab,
                'story_difficulty': story.get('difficulty_level', 'intermediate'),
                'congratulations_message': self._generate_congratulations_message(avg_score, story.get('difficulty_level', 'intermediate')),
                'next_recommendations': self._get_next_story_recommendations(story.get('scenario', 'general'), story.get('difficulty_level', 'intermediate'))
            }
            
            print(f"✅ Story {story_id} completed successfully")
            return completion_data
            
        except Exception as e:
            print(f"❌ Error in complete_story: {e}")
            return self._get_fallback_completion_data(story_id, error=str(e))
    
    
    def _get_story_completion_time(self, story_id):
        """Calculate time spent on story"""
        progress = self.db_service.get_story_progress(story_id)
        if progress and progress.get('started_at') and progress.get('completed_at'):
            # This would need proper time calculation
            return "15 minutes"  # Placeholder
        return "Unknown"
    
    def  _generate_congratulations_message(self, avg_score, difficulty):
        """Generate a personalized congratulations message"""
        try:
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
                
        except Exception as e:
            print(f"Error generating congratulations message: {e}")
            return "Congratulations on completing the story! Keep up the great work!"
    
    def _get_next_story_recommendations(self, scenario, difficulty):
        """Get recommendations for next stories to try"""
        try:
            recommendations = []
            
            # Same scenario, higher difficulty
            if difficulty == 'beginner':
                recommendations.append(f"Try an intermediate {scenario.replace('_', ' ')} story")
            elif difficulty == 'intermediate':
                recommendations.append(f"Challenge yourself with an advanced {scenario.replace('_', ' ')} story")
            
            # Different scenarios, same difficulty
            other_scenarios = ['debugging_session', 'code_review', 'technical_interview', 'daily_standup']
            if scenario in other_scenarios:
                other_scenarios.remove(scenario)
            
            if other_scenarios:
                random_scenario = random.choice(other_scenarios)
                recommendations.append(f"Explore {random_scenario.replace('_', ' ')} stories")
            
            # Grammar quiz recommendation
            recommendations.append("Take a grammar quiz to reinforce what you learned")
            
            # Always ensure we have at least one recommendation
            if not recommendations:
                recommendations = [
                    "Try another story to continue practicing",
                    "Take a grammar quiz",
                    "Review your vocabulary"
                ]
            
            return recommendations[:3]  # Return top 3 recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return [
                "Continue practicing with more stories",
                "Take grammar quizzes to improve",
                "Build your technical vocabulary"
            ]
    
    def _get_fallback_completion_data(self, story_id, error=None):
        """Generate fallback completion data when there's an error"""
        print(f"🔄 Using fallback completion data for story {story_id}")
        
        return {
            'story_title': 'Completed Story',
            'completion_time': '5 minutes',
            'total_interactions': 1,
            'average_score': 80.0,
            'total_corrections': 0,
            'new_vocabulary_learned': 0,
            'story_difficulty': 'intermediate',
            'congratulations_message': 'Congratulations on completing the story! Great job practicing your English.',
            'next_recommendations': [
                'Try another story to continue practicing',
                'Take a grammar quiz to reinforce learning',
                'Review your vocabulary to strengthen retention'
            ],
            'error_note': f'Note: Some completion data may be approximate due to: {error}' if error else None
        }
     
    def _get_story_completion_time(self, story_id):
        """Calculate time spent on story"""
        try:
            progress = self.db_service.get_story_progress(story_id)
            if progress and isinstance(progress, dict):
                started_at = progress.get('started_at')
                completed_at = progress.get('completed_at')
                if started_at and completed_at:
                    # This would need proper time calculation
                    return "15 minutes"  # Placeholder
            return "10 minutes"  # Default fallback
        except Exception as e:
            print(f"Error calculating completion time: {e}")
            return "Unknown"