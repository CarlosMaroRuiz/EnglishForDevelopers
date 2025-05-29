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

### 📊 Progress Tracking
Comprehensive analytics dashboard:
- **Mistake Patterns** - Identify your most common errors
- **Vocabulary Growth** - Track technical words learned
- **Problem Areas** - See which scenarios need more practice
- **Personalized Recommendations** - AI-generated learning suggestions

### 🌐 Bilingual Support
- **English-Spanish Interface** - Switch languages anytime
- **Real-time Translation** - Translate AI responses and corrections
- **Bilingual Feedback** - Understand corrections in your native language

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
   cp .env.example .env
   # Edit .env file with your API keys
   ```
   
   Your `.env` file should contain:
   ```env
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   SECRET_KEY=your_secret_key_for_flask_sessions
   ```

4. **Test API connection** (optional but recommended)
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
├── english_tutor.db     # SQLite database (auto-created)
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   ├── chat.html        # Chat interface
│   ├── analytics.html   # Progress dashboard
│   ├── vocabulary.html  # Vocabulary manager
│   └── history.html     # Conversation history
└── .env                 # Environment variables (create this)
```

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **AI Integration**: DeepSeek API
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Tailwind CSS
- **Translation**: MyMemory Translation API

## 📱 Usage

### 1. Choose a Scenario
Select from 8 different workplace scenarios on the home page.

### 2. Start Practicing
- Type your messages in English
- Receive AI responses that continue the conversation
- Get instant corrections and suggestions

### 3. Review Feedback
- **Red panels**: Grammar and style corrections
- **Blue panels**: New technical vocabulary
- **Yellow panels**: Professional communication tips

### 4. Track Progress
- Visit `/analytics` to see your learning patterns
- Check `/vocabulary` for words you've learned
- Review `/history` for past conversations

## 🧪 Testing Your Setup

Run the test script to verify everything is working:

```bash
python test.py
```

This will:
- ✅ Check if your API key is properly configured
- ✅ Test basic API connectivity
- ✅ Verify JSON response parsing
- ✅ Confirm the application is ready to use

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DEEPSEEK_API_KEY` | Your DeepSeek API key | Yes |
| `SECRET_KEY` | Flask session secret key | Yes |

### Database

The application automatically creates and manages a SQLite database with tables for:
- **Conversations** - Chat history
- **Grammar Mistakes** - Error tracking
- **Vocabulary** - Technical terms learned
- **User Progress** - Learning analytics
- **Recommendations** - AI suggestions

## 🌟 Key Features in Detail

### Intelligent Corrections
The AI analyzes your English and provides:
- **Grammar fixes** with explanations
- **Better word choices** for technical contexts
- **Professional phrasing** suggestions
- **Cultural communication tips**

### Vocabulary Building
- **Context-aware definitions** for technical terms
- **Professional usage examples**
- **Frequency tracking** for retention
- **Bilingual support** for better understanding

### Progress Analytics
- **Visual dashboards** showing improvement trends
- **Mistake pattern analysis** for focused learning
- **Scenario-specific performance** tracking
- **Personalized learning paths**