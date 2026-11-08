"""AI personal report business logic."""
import asyncio

_FALLBACK_REPORT = {
    "strengths": ["You're committed to learning"],
    "weaknesses": ["Continue practicing regularly"],
    "grammar_mastered": [],
    "grammar_needs_work": [],
    "focus_areas": ["Daily practice", "Grammar quizzes"],
    "recommendations": ["Keep practicing conversations"],
    "overall_assessment": "Keep up the great work with your English practice!",
    "learning_path": ["Daily conversations", "Weekly quizzes"],
    "personality_insights": ["Dedicated learner"],
}


class ReportService:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai

    async def generate_personal_report(self):
        detailed = await asyncio.to_thread(self.db.get_detailed_mistakes_for_report)
        vocabulary = await asyncio.to_thread(self.db.get_vocabulary_for_report)
        quiz_history = await asyncio.to_thread(self.db.get_quiz_history_for_report)
        scenario_perf = await asyncio.to_thread(self.db.get_scenario_performance_for_report)
        story_progress = await asyncio.to_thread(self.db.get_user_story_progress)

        summary = (
            "User's learning data:\n"
            f"- {len(detailed)} different error patterns\n"
            f"- {len(vocabulary)} technical terms learned\n"
            f"- {len(quiz_history)} recent quizzes taken\n"
            f"- {len(scenario_perf)} different workplace contexts\n"
            f"- {len(story_progress)} stories engaged with\n"
        )

        report = None
        if self.ai.available:
            try:
                report = await self.ai.generate_report(summary)
            except Exception as exc:  # noqa: BLE001
                print(f"Report generation error: {exc}")
                report = None

        if report is None:
            report = _FALLBACK_REPORT
        else:
            report = report.model_dump()

        analytics = await asyncio.to_thread(self.db.get_user_analytics)
        return {"report": report, "analytics": analytics}
