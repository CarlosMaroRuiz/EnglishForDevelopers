"""Read-only analytics / dashboard data."""
import asyncio


class AnalyticsService:
    def __init__(self, db):
        self.db = db

    def get_analytics_data(self):
        analytics = self.db.get_user_analytics()
        recommendations = self._generate_recommendations(analytics)
        return {"analytics": analytics, "recommendations": recommendations}

    def get_vocabulary_data(self):
        return self.db.get_vocabulary_list()

    def get_conversation_history(self):
        return self.db.get_conversation_history()

    def _generate_recommendations(self, analytics):
        recommendations = []

        mistake_patterns = analytics.get("mistake_patterns", [])
        if mistake_patterns:
            top = mistake_patterns[0]
            recommendations.append(
                {
                    "type": "grammar_focus",
                    "content": f"Focus on improving {top['mistake_type']} - you've made {top['count']} mistakes in this area",
                    "priority": 3,
                }
            )

        problem_areas = analytics.get("problem_areas", [])
        if problem_areas:
            top = problem_areas[0]
            recommendations.append(
                {
                    "type": "scenario_practice",
                    "content": f"Practice more {top['scenario'].replace('_', ' ')} scenarios - this is where you make most mistakes",
                    "priority": 2,
                }
            )

        if analytics.get("vocabulary_count", 0) < 50:
            recommendations.append(
                {
                    "type": "vocabulary",
                    "content": "Build your technical vocabulary - aim to learn 5 new terms this week",
                    "priority": 1,
                }
            )

        if analytics.get("quiz_stats", {}).get("avg_score", 0) < 70:
            recommendations.append(
                {
                    "type": "quiz_practice",
                    "content": "Your quiz average is below 70%. Take more grammar quizzes to improve!",
                    "priority": 3,
                }
            )

        if analytics.get("story_stats", {}).get("completed_stories", 0) < 3:
            recommendations.append(
                {
                    "type": "story_practice",
                    "content": "Try reading interactive stories to improve your comprehension and vocabulary",
                    "priority": 2,
                }
            )

        return recommendations
