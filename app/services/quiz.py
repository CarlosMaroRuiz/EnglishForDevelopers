"""Quiz business logic."""
import asyncio

_DEFAULT_QUESTIONS = [
    {
        "question": "Choose the correct sentence for a code review:",
        "option_a": "This function works good",
        "option_b": "This function works well",
        "option_c": "This function work well",
        "correct_answer": "b",
        "explanation": "'Well' is the correct adverb to describe how something works",
        "category": "grammar",
    },
    {
        "question": "Which is the correct way to report a bug?",
        "option_a": "I found a bug in the login system",
        "option_b": "I finded a bug in the login system",
        "option_c": "I find a bug in the login system",
        "correct_answer": "a",
        "explanation": "'Found' is the correct past tense of 'find'",
        "category": "verb_tense",
    },
    {
        "question": "What's the best way to describe a completed task?",
        "option_a": "I have finish the implementation",
        "option_b": "I have finished the implementation",
        "option_c": "I have finishing the implementation",
        "correct_answer": "b",
        "explanation": "Present perfect requires the past participle 'finished'",
        "category": "verb_tense",
    },
    {
        "question": "How should you ask for help in a meeting?",
        "option_a": "Can you help me with this issue?",
        "option_b": "Can you help me to this issue?",
        "option_c": "Can you help me for this issue?",
        "correct_answer": "a",
        "explanation": "'Help me with' is the correct preposition usage",
        "category": "prepositions",
    },
    {
        "question": "Which sentence is correct for describing progress?",
        "option_a": "We are making good progresses",
        "option_b": "We are making good progress",
        "option_c": "We are making a good progresses",
        "correct_answer": "b",
        "explanation": "'Progress' is an uncountable noun, so no plural form",
        "category": "grammar",
    },
]


class QuizService:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai

    async def generate_personalized_quiz(self):
        user_mistakes = await asyncio.to_thread(self.db.get_user_mistakes, 5)

        if not user_mistakes:
            return {"questions": _DEFAULT_QUESTIONS}

        mistake_types = [m["mistake_type"] for m in user_mistakes[:3]]
        questions = None
        if self.ai.available:
            try:
                questions = await self.ai.generate_quiz(mistake_types, 5)
            except Exception as exc:  # noqa: BLE001
                print(f"Quiz generation error: {exc}")
                questions = None

        if not questions:
            # Always fall back to defaults rather than failing the request.
            return {"questions": _DEFAULT_QUESTIONS}

        self.db.save_quiz_questions([q.model_dump() for q in questions])
        return {"questions": [q.model_dump() for q in questions]}

    def process_quiz_submission(self, answers, questions):
        if not answers or not questions:
            raise ValueError("Missing quiz data")

        correct_count = 0
        total = len(questions)
        detailed_results = []
        focused_areas = []

        for i, question in enumerate(questions):
            user_answer = answers.get(str(i))
            correct_answer = question.get("correct_answer")
            is_correct = user_answer == correct_answer

            if is_correct:
                correct_count += 1
            else:
                focused_areas.append(question.get("category", "general"))

            detailed_results.append(
                {
                    "question": question.get("question"),
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "explanation": question.get("explanation"),
                    "category": question.get("category"),
                }
            )

        score = (correct_count / total * 100) if total > 0 else 0
        self.db.save_quiz_result("grammar_practice", total, correct_count, detailed_results, focused_areas)

        if score >= 90:
            feedback = "Excellent! Your English grammar is very strong."
        elif score >= 70:
            feedback = "Good job! You have a good understanding, but there's room for improvement."
        elif score >= 50:
            feedback = "Not bad, but you should focus more on the areas where you made mistakes."
        else:
            feedback = "Keep practicing! Focus on the grammar areas highlighted in your results."

        return {
            "score": score,
            "correct": correct_count,
            "total": total,
            "feedback": feedback,
            "detailed_results": detailed_results,
            "focused_areas": list(set(focused_areas)),
        }
