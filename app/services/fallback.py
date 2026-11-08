"""Shared offline fallback used when the AI service is unavailable."""
import re

from app.schemas import ConversationAnalysis, Correction, VocabularyItem

_GRAMMAR_PATTERNS = [
    (r"\bi am work\b", "I am working", "Present continuous tense"),
    (r"\bcan able to\b", "can / am able to", "Avoid double modals"),
    (r"\bvery much\b", "a lot / greatly", "More natural expression"),
    (r"\bmake a test\b", "run a test", "Technical terminology"),
    (r"\bfix a bug\b", "fix the bug", "Specific article usage"),
]

_SCENARIO_VOCAB = {
    "debugging_session": [
        VocabularyItem(word="troubleshoot", definition="to identify and solve problems", example="Let me troubleshoot this issue step by step."),
    ],
    "code_review": [
        VocabularyItem(word="refactor", definition="to restructure code without changing functionality", example="We should refactor this function for better readability."),
    ],
    "daily_standup": [
        VocabularyItem(word="blocker", definition="an issue preventing progress", example="I have a blocker with the API integration."),
    ],
}

_SCENARIO_RESPONSES = {
    "debugging_session": "I understand you're working on debugging. That's a great approach to problem-solving. What's your next step?",
    "code_review": "Your code review feedback sounds constructive. It's important to provide clear, actionable suggestions.",
    "daily_standup": "Thanks for the update. It's good to communicate both progress and any blockers clearly.",
    "technical_interview": "That's a thoughtful response. Technical interviews are great opportunities to showcase your problem-solving approach.",
    "project_planning": "Good planning approach. Breaking down tasks helps estimate effort more accurately.",
    "client_meeting": "Clear communication with clients is essential. Making technical concepts accessible is a valuable skill.",
    "architecture_discussion": "Architecture discussions benefit from considering multiple perspectives. What are the trade-offs?",
    "deployment_issue": "Handling deployment issues requires both technical skills and clear communication with stakeholders.",
}


def fallback_analysis(message: str, scenario: str) -> ConversationAnalysis:
    """Produce a basic, deterministic analysis when no AI is available."""
    corrections: list[Correction] = []
    user_lower = message.lower()

    for pattern, corrected, explanation in _GRAMMAR_PATTERNS:
        match = re.search(pattern, user_lower)
        if match:
            corrections.append(
                Correction(original=match.group(), corrected=corrected, type="grammar", explanation=explanation)
            )

    new_vocabulary = _SCENARIO_VOCAB.get(scenario, [])
    conversation_response = _SCENARIO_RESPONSES.get(scenario, "I understand your point. Let's continue the discussion.")

    suggestions = "Keep practicing professional communication! "
    if corrections:
        suggestions += f"Focus on the {len(corrections)} grammar point(s) highlighted above."
    else:
        suggestions += "Your English looks good! Try using more technical vocabulary to sound more professional."

    return ConversationAnalysis(
        conversation_response=conversation_response,
        corrections=corrections,
        new_vocabulary=new_vocabulary,
        suggestions=suggestions,
    )
