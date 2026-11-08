"""Interactive story business logic."""
import asyncio
import random
from datetime import datetime

from app.services.fallback import fallback_analysis
from config import get_scenario_prompt


class StoryService:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai

    # ------------------------------------------------------------------ reads
    def get_stories_list(self):
        return self.db.get_stories_list()

    def get_story_by_id(self, story_id):
        return self.db.get_story_by_id(story_id)

    def get_user_story_progress(self):
        return self.db.get_user_story_progress()

    def get_story_progress(self, story_id):
        return self.db.get_story_progress(story_id)

    def get_story_interactions(self, story_id):
        return self.db.get_story_interactions(story_id)

    # --------------------------------------------------------------- creation
    async def generate_ai_story(self, topic="software_development", difficulty="intermediate",
                                scenario="daily_standup", length="medium", focus_areas=None):
        parameters = {
            "topic": topic,
            "scenario": scenario,
            "difficulty": difficulty,
            "length": length,
            "focus_areas": focus_areas or ["technical_vocabulary", "communication_skills"],
        }

        story_data = None
        if self.ai.available:
            try:
                story_data = await self.ai.generate_story(parameters)
            except Exception as exc:  # noqa: BLE001
                print(f"Story generation error: {exc}")
                story_data = None

        if story_data is None or not story_data.title or not story_data.content:
            return await asyncio.to_thread(self._create_fallback_story, topic, difficulty, scenario, length)

        story_id = await asyncio.to_thread(
            self.db.save_story,
            title=story_data.title,
            description=story_data.description or "",
            content=story_data.content,
            story_type="generated",
            scenario=scenario,
            difficulty_level=difficulty,
            topic=topic,
            estimated_time=story_data.estimated_time or 10,
            learning_objectives=story_data.learning_objectives or [],
        )

        steps = [self._validate_and_fix_step(s.model_dump(), i + 1) for i, s in enumerate(story_data.steps)]
        if not steps:
            steps = self._create_default_steps(scenario)
        await asyncio.to_thread(self.db.save_story_steps, story_id, steps)

        result = story_data.model_dump()
        result["id"] = story_id
        result["steps"] = steps
        return result

    def create_manual_story(self, title, content, scenario, difficulty):
        story_id = self.db.save_story(
            title=title,
            description=f"A custom story about {scenario.replace('_', ' ')}",
            content=content,
            story_type="manual",
            scenario=scenario,
            difficulty_level=difficulty,
            topic="custom",
            estimated_time=10,
            learning_objectives=["reading comprehension", "vocabulary building"],
        )
        steps = [
            {"type": "narrative", "content": content, "question": None, "learning_focus": "reading comprehension"},
            {"type": "question", "content": "After reading this story...",
             "question": "What are the main points you learned from this scenario?",
             "learning_focus": "comprehension and reflection"},
        ]
        self.db.save_story_steps(story_id, steps)
        return {
            "id": story_id,
            "title": title,
            "content": content,
            "scenario": scenario,
            "difficulty_level": difficulty,
        }

    # ------------------------------------------------------------ interaction
    async def stream_story_interaction(self, story_id, user_response, current_step):
        story = await asyncio.to_thread(self.db.get_story_by_id, story_id)
        if not story:
            yield {"type": "error", "message": "Story not found"}
            return

        steps = story.get("steps", [])
        scenario = story.get("scenario", "daily_standup")

        context = None
        if 0 < current_step <= len(steps):
            step = steps[current_step - 1]
            context = f"Step {current_step}: {step.get('content', '')}"
            if step.get("question"):
                context += f" Question: {step['question']}"

        analysis = None
        if self.ai.available:
            try:
                async for snapshot in self.ai.stream_conversation(user_response, scenario, context):
                    analysis = snapshot
                    yield {"type": "delta", "text": snapshot.conversation_response or ""}
            except Exception as exc:  # noqa: BLE001
                print(f"Story interaction streaming error: {exc}")
                analysis = None

        if analysis is None or not analysis.conversation_response:
            analysis = fallback_analysis(user_response, scenario)

        score = self._calculate_interaction_score(user_response, analysis)

        await asyncio.to_thread(
            self.db.save_story_interaction,
            story_id,
            current_step,
            user_response,
            analysis.conversation_response,
            [c.model_dump() for c in analysis.corrections],
            [v.model_dump() for v in analysis.new_vocabulary],
            score,
        )
        if analysis.new_vocabulary:
            await asyncio.to_thread(self.db.save_vocabulary, [v.model_dump() for v in analysis.new_vocabulary])

        next_step = current_step + 1
        is_complete = next_step > len(steps)

        yield {
            "type": "done",
            "data": {
                "ai_feedback": analysis.conversation_response,
                "corrections": [c.model_dump() for c in analysis.corrections],
                "new_vocabulary": [v.model_dump() for v in analysis.new_vocabulary],
                "suggestions": analysis.suggestions,
                "interaction_score": score,
                "next_step": next_step if not is_complete else None,
                "is_complete": is_complete,
                "story_progress": self._calculate_story_progress(next_step, len(steps)),
            },
        }

    def _calculate_interaction_score(self, user_response, analysis):
        score = 50
        words = len(user_response.split())
        if words >= 20:
            score += 10
        elif words >= 10:
            score += 5

        corrections_count = len(analysis.corrections or [])
        if corrections_count == 0:
            score += 20
        elif corrections_count <= 2:
            score += 10
        elif corrections_count <= 5:
            score += 0
        else:
            score -= 10

        score += len(analysis.new_vocabulary or []) * 5
        return max(0, min(score, 100))

    def _calculate_story_progress(self, current_step, total_steps):
        if total_steps == 0:
            return 100.0
        return min((current_step / total_steps) * 100, 100.0)

    # -------------------------------------------------------------- completion
    def complete_story(self, story_id):
        try:
            self.db.complete_story(story_id)
            interactions = self.db.get_story_interactions(story_id)
            story = self.db.get_story_by_id(story_id)
            if not story:
                return self._fallback_completion_data(story_id)

            total = len(interactions)
            scores = [i["interaction_score"] for i in interactions
                      if isinstance(i.get("interaction_score"), (int, float))]
            avg = sum(scores) / len(scores) if scores else 75
            total_corrections = sum(len(i.get("corrections", [])) for i in interactions)
            total_vocab = sum(len(i.get("new_vocabulary", [])) for i in interactions)
            difficulty = story.get("difficulty_level", "intermediate")

            return {
                "story_title": story.get("title", "Completed Story"),
                "completion_time": self._completion_time(story_id),
                "total_interactions": total,
                "average_score": round(avg, 1),
                "total_corrections": total_corrections,
                "new_vocabulary_learned": total_vocab,
                "story_difficulty": difficulty,
                "congratulations_message": self._congratulations(avg, difficulty),
                "next_recommendations": self._next_recommendations(story.get("scenario", "general"), difficulty),
            }
        except Exception as exc:  # noqa: BLE001
            print(f"Error completing story: {exc}")
            return self._fallback_completion_data(story_id, str(exc))

    def _completion_time(self, story_id):
        progress = self.db.get_story_progress(story_id)
        started = progress.get("started_at")
        completed = progress.get("completed_at")
        if started and completed:
            try:
                a = datetime.fromisoformat(started)
                b = datetime.fromisoformat(completed)
                minutes = max(1, round((b - a).total_seconds() / 60))
                return f"{minutes} minute(s)"
            except ValueError:
                pass
        return "Unknown"

    def _congratulations(self, avg_score, difficulty):
        levels = {
            "beginner": {90: "Outstanding work! You've mastered this beginner story with exceptional English skills!",
                         70: "Great job! You completed the story well. Keep practicing to improve even more!",
                         50: "Good effort! You're making progress. Try more stories to build your confidence!"},
            "intermediate": {90: "Excellent! Your English skills are impressive for this intermediate level!",
                             70: "Well done! You handled this intermediate story very well!",
                             50: "Nice work! Intermediate stories are challenging, and you're improving!"},
            "advanced": {90: "Exceptional! You've demonstrated advanced English proficiency!",
                         70: "Great performance! Your advanced English skills are showing!",
                         50: "Good work! Advanced content is tough - keep challenging yourself!"},
        }
        level = levels.get(difficulty, levels["intermediate"])
        if avg_score >= 90:
            return level[90]
        if avg_score >= 70:
            return level[70]
        return level[50]

    def _next_recommendations(self, scenario, difficulty):
        recommendations = []
        if difficulty == "beginner":
            recommendations.append(f"Try an intermediate {scenario.replace('_', ' ')} story")
        elif difficulty == "intermediate":
            recommendations.append(f"Challenge yourself with an advanced {scenario.replace('_', ' ')} story")

        others = ["debugging_session", "code_review", "technical_interview", "daily_standup"]
        if scenario in others:
            others.remove(scenario)
        if others:
            recommendations.append(f"Explore {random.choice(others).replace('_', ' ')} stories")

        recommendations.append("Take a grammar quiz to reinforce what you learned")
        return recommendations[:3]

    def _fallback_completion_data(self, story_id, error=None):
        data = {
            "story_title": "Completed Story",
            "completion_time": "5 minutes",
            "total_interactions": 1,
            "average_score": 80.0,
            "total_corrections": 0,
            "new_vocabulary_learned": 0,
            "story_difficulty": "intermediate",
            "congratulations_message": "Congratulations on completing the story! Great job practicing your English.",
            "next_recommendations": [
                "Try another story to continue practicing",
                "Take a grammar quiz to reinforce learning",
                "Review your vocabulary to strengthen retention",
            ],
        }
        if error:
            data["error_note"] = f"Note: Some completion data may be approximate due to: {error}"
        return data

    # -------------------------------------------------------------- helpers
    def _validate_and_fix_step(self, step, step_number):
        content = step.get("content", "")
        if not content or len(content.strip()) < 10:
            content = f"Step {step_number}: Continue with your response to this scenario."
        return {
            "step_number": step_number,
            "type": step.get("type", "narrative"),
            "content": content,
            "question": step.get("question"),
            "expected_response_type": step.get("expected_response_type", "open"),
            "learning_focus": step.get("learning_focus", "communication_skills"),
        }

    def _create_default_steps(self, scenario):
        prompt = get_scenario_prompt(scenario)
        return [
            {
                "step_number": 1,
                "type": "question",
                "content": prompt,
                "question": "How would you handle this professional situation?",
                "expected_response_type": "open",
                "learning_focus": "professional_communication",
            }
        ]

    def _create_fallback_story(self, topic, difficulty, scenario, length="short"):
        prompt = get_scenario_prompt(scenario)
        title = f"{scenario.replace('_', ' ').title()} Practice"
        content = f"You are about to practice professional communication. {prompt}"
        steps = [
            {"step_number": 1, "type": "question", "content": prompt,
             "question": "How would you handle this situation professionally?",
             "expected_response_type": "open", "learning_focus": "professional_communication"},
            {"step_number": 2, "type": "question", "content": "A teammate asks a follow-up question.",
             "question": "How would you explain your approach and next steps?",
             "expected_response_type": "open", "learning_focus": "technical_vocabulary"},
        ]
        story_id = self.db.save_story(
            title=title,
            description="Offline fallback story",
            content=content,
            story_type="fallback",
            scenario=scenario,
            difficulty_level=difficulty,
            topic=topic,
            estimated_time=5,
            learning_objectives=["professional communication", "technical vocabulary"],
        )
        self.db.save_story_steps(story_id, steps)
        return {
            "id": story_id,
            "title": title,
            "description": "Offline fallback story",
            "content": content,
            "scenario": scenario,
            "difficulty_level": difficulty,
            "steps": steps,
            "learning_objectives": ["professional communication", "technical vocabulary"],
        }
