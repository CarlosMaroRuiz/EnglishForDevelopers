import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY') or ''
    DATABASE_PATH = 'english_tutor.db'
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    
    # Work scenarios for practice
    WORK_SCENARIOS = [
        "daily_standup",
        "code_review", 
        "technical_interview",
        "debugging_session",
        "project_planning",
        "client_meeting",
        "architecture_discussion",
        "deployment_issue"
    ]
    
    # Scenario prompts
    SCENARIO_PROMPTS = {
        "daily_standup": "You're in a daily standup meeting. Discuss what you worked on yesterday, what you're working on today, and any blockers.",
        "code_review": "You're reviewing a colleague's pull request. Discuss the code quality, suggest improvements, and ask questions.",
        "technical_interview": "You're in a technical interview. Answer questions about your experience, solve coding problems, and ask about the role.",
        "debugging_session": "You're helping debug a production issue. Explain the problem, discuss potential causes, and propose solutions.",
        "project_planning": "You're planning a new feature. Discuss requirements, technical approach, and timeline estimates.",
        "client_meeting": "You're meeting with a client to discuss their software requirements and provide technical recommendations.",
        "architecture_discussion": "You're discussing system architecture with your team. Talk about design patterns, scalability, and best practices.",
        "deployment_issue": "There's a deployment problem in production. Communicate the issue, impact, and resolution steps."
    }
    
    @classmethod
    def get_scenario_prompt(cls, scenario):
        return cls.SCENARIO_PROMPTS.get(scenario, "General technical discussion")