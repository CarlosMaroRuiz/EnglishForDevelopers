# 💻 English Tutor for Developers

An AI-powered English tutor specifically designed for software developers who want to improve their technical English communication skills in professional workplace scenarios.

## ✨ Features

### 🎯 Real Workplace Scenarios
Practice English in authentic software development contexts:
- **Daily Standups** - Share updates, discuss blockers
- **Code Reviews** - Provide feedback, suggest improvements
- **Technical Interviews** - Answer questions, explain solutions
- **Debugging Sessions** - Communicate issues and solutions
- **Project Planning** - Discuss requirements and timelines
- **Client Meetings** - Present technical solutions
- **Architecture Discussions** - Design system architecture
- **Deployment Issues** - Handle production problems

### 🤖 AI-Powered Learning
Using DeepSeek API for intelligent analysis:
- **Grammar Corrections** - Instant feedback on mistakes
- **Vocabulary Enhancement** - Learn technical terminology
- **Style Improvements** - Professional communication tips
- **Context-Aware Responses** - Scenario-specific conversations

### 📝 Personalized Grammar Quizzes
- **AI-Generated Questions** - Based on your most common mistakes
- **Adaptive Learning** - Questions target your weak areas
- **Detailed Explanations** - Learn why answers are correct
- **Progress Tracking** - Monitor quiz performance over time
- **Focus Area Recommendations** - Know what to practice next

### 🤖 AI Personal Analysis Reports
- **Comprehensive Skill Assessment** - Detailed analysis of your English abilities
- **Strengths & Weaknesses** - Identify what you do well and what needs work
- **Grammar Mastery Tracking** - See which topics you've mastered
- **Personalized Learning Path** - Step-by-step improvement plan
- **Learning Style Insights** - Understand how you learn best
- **Actionable Recommendations** - Specific steps to improve faster

### 📊 Advanced Analytics Dashboard
- **Mistake Pattern Analysis** - Identify your most common errors
- **Vocabulary Growth Tracking** - Monitor words learned over time
- **Scenario Performance** - See which situations need more practice
- **Progress Visualization** - Charts and metrics to track improvement
- **Personalized Recommendations** - AI suggestions for focused learning

### 🌐 Bilingual Support (English-Spanish)
- **Real-time Translation** - Translate AI responses and corrections
- **Bilingual Interface** - Switch languages with one click
- **Enhanced Translation** - Multiple translation services with fallbacks
- **Technical Term Dictionary** - Specialized vocabulary translations
- **Cultural Context** - Understand professional communication differences

### 📈 Progress Tracking & History
- **Conversation History** - Review all your practice sessions
- **Vocabulary Management** - Track and review learned words
- **Detailed Corrections** - See all grammar improvements over time
- **Export Functionality** - Save your learning data

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- DeepSeek API key ([Get one here](https://platform.deepseek.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/CarlosMaroRuiz/EnglishForDevelopers.git
   cd EnglishForDevelopers
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp example.env .env
   # Edit .env file with your API keys
   ```
   
   Your `.env` file should contain:
   ```env
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   SECRET_KEY=your_secret_key_for_flask_sessions
   ```

4. **Test API connection** (recommended)
   ```bash
   python test.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## 🏗️ Project Structure

```
english-tutor-developers/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── test.py              # API connection testing
├── .gitignore           # Git ignore rules
├── example.env          # Environment variables template
├── english_tutor.db     # SQLite database (auto-created)
├── services/            # Business logic layer
│   ├── __init__.py      # Services package init
│   ├── database.py      # Database operations
│   ├── ai_service.py    # DeepSeek AI integration
│   └── business_service.py # Core business logic
├── routes.py            # Flask routes and endpoints
└── templates/           # HTML templates
    ├── base.html        # Base template with navigation
    ├── index.html       # Home page with scenarios
    ├── chat.html        # Interactive chat interface
    ├── quiz.html        # Grammar quiz interface
    ├── report.html      # AI personal analysis report
    ├── analytics.html   # Progress dashboard
    ├── vocabulary.html  # Vocabulary manager
    └── history.html     # Conversation history
```

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with comprehensive analytics tables
- **AI Integration**: DeepSeek API for natural language processing
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Tailwind CSS with custom animations
- **Translation**: MyMemory Translation API with fallback dictionaries
- **Architecture**: Service-oriented architecture with separation of concerns

## 📱 Usage Guide

### 1. Home Dashboard
- **Scenario Selection**: Choose from 8 different workplace scenarios
- **Quick Access**: Jump directly to practice or quizzes
- **Progress Overview**: See your learning statistics at a glance

### 2. Interactive Conversations
- **Type Messages**: Practice English in realistic work situations
- **AI Responses**: Get contextual replies that continue the conversation
- **Instant Feedback**: Receive corrections and suggestions in real-time
- **Translation Support**: Translate messages and feedback to Spanish

### 3. Personalized Quizzes
- **Adaptive Questions**: Based on your conversation mistakes
- **Multiple Choice**: Technical grammar questions with explanations
- **Immediate Results**: See your score and detailed feedback
- **Focus Areas**: Identify specific topics to practice

### 4. AI Analysis Reports
- **Comprehensive Assessment**: Detailed analysis of your English skills
- **Visual Progress**: Charts showing your improvement over time
- **Learning Path**: Step-by-step plan for continued improvement
- **Bilingual Support**: View reports in English or Spanish

### 5. Analytics Dashboard
- **Mistake Patterns**: Identify your most common errors
- **Performance Tracking**: Monitor improvement across scenarios
- **Vocabulary Growth**: Track technical terms learned
- **Recommendations**: AI-generated suggestions for focused practice

### 6. Progress Management
- **Conversation History**: Review all your practice sessions
- **Vocabulary Library**: Manage and review learned words
- **Export Data**: Save your progress and analytics

## 🧪 Testing Your Setup

Run the comprehensive test script:

```bash
python test.py
```

This will:
- ✅ Verify your DeepSeek API key is configured correctly
- ✅ Test basic API connectivity and response handling
- ✅ Validate JSON response parsing for grammar analysis
- ✅ Confirm the application is ready for full functionality

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEEPSEEK_API_KEY` | Your DeepSeek API key for AI functionality | Yes | - |
| `SECRET_KEY` | Flask session secret key for security | Yes | Auto-generated |

### Database Schema

The application automatically creates and manages SQLite tables for:

- **conversations** - Chat history with AI responses
- **grammar_mistakes** - Detailed error tracking and patterns
- **vocabulary** - Technical terms with definitions and examples
- **user_progress** - Learning analytics and improvement metrics
- **quiz_results** - Quiz performance and detailed results
- **quiz_questions** - AI-generated personalized questions
- **recommendations** - AI-powered learning suggestions

## 🌟 Key Features in Detail

### Advanced AI Analysis
- **Context-Aware Corrections**: Grammar fixes specific to technical communication
- **Professional Vocabulary**: Industry-specific term suggestions
- **Cultural Communication**: Tips for professional workplace interactions
- **Pattern Recognition**: Identifies your most common mistake types

### Intelligent Quiz Generation
- **Mistake-Based Questions**: Targets your specific problem areas
- **Difficulty Adaptation**: Adjusts based on your performance level
- **Comprehensive Explanations**: Learn why answers are correct or incorrect
- **Progress Integration**: Results feed back into your overall analytics

### Bilingual Learning Support
- **Real-Time Translation**: Instant Spanish translations for all content
- **Technical Dictionaries**: Specialized IT/development term translations
- **Cultural Context**: Professional communication differences between languages
- **Fallback Systems**: Multiple translation sources for reliability

### Comprehensive Progress Tracking
- **Visual Analytics**: Charts and graphs showing improvement trends
- **Detailed History**: Complete record of all conversations and corrections
- **Export Capabilities**: Save your data for external analysis
- **Performance Metrics**: Quantified measures of your English improvement

## 📊 Analytics & Insights

The application provides detailed insights into your learning:

- **Conversation Quality**: Track improvement in natural communication
- **Grammar Mastery**: Monitor which grammar topics you've mastered
- **Vocabulary Expansion**: See your technical vocabulary growth
- **Scenario Performance**: Identify which work situations need more practice
- **Learning Velocity**: Measure how quickly you're improving
- **Mistake Reduction**: Track decreasing error rates over time

## 🔄 Recent Updates

### Version 2.0 Features
- **AI Personal Reports**: Comprehensive skill analysis with learning paths
- **Advanced Quizzes**: Personalized questions based on your mistakes
- **Enhanced Analytics**: Detailed progress tracking and visualization
- **Bilingual Interface**: Full Spanish translation support
- **Improved Architecture**: Service-oriented design for better maintainability
- **Better Error Handling**: More robust API integration and fallbacks



## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. **Check the test script**: Run `python test.py` to verify your setup
2. **Review the logs**: Check console output for error messages
3. **API Key Issues**: Ensure your DeepSeek API key is valid and has sufficient credits
4. **Database Problems**: Delete `english_tutor.db` to reset the database
5. **Translation Issues**: The app has fallback dictionaries if translation APIs fail
