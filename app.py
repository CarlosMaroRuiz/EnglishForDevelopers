from flask import Flask
from config import Config
from services.database import DatabaseService
from services.ai_service import AIService
from services.business_service import BusinessService
from routes import Routes

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    
    # Initialize services
    db_service = DatabaseService()
    ai_service = AIService(db_service)
    business_service = BusinessService(db_service, ai_service)
    
    # Register routes
    Routes(app, business_service)
    
    return app

if __name__ == '__main__':
    # Check API key configuration
    if not Config.DEEPSEEK_API_KEY:
        print("⚠️  WARNING: DEEPSEEK_API_KEY not found in environment variables!")
        print("Please create a .env file with your DeepSeek API key.")
        print("Example: DEEPSEEK_API_KEY=your_actual_api_key_here")
    
    # Create and run application
    app = create_app()
    print("🚀 Starting English Tutor for Developers...")
    print("📚 Database initialized successfully")
    print("🌐 Server running on http://localhost:5000")
    app.run(debug=True)