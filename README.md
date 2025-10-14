# 🧠 Advanced AI Reasoning System Pro

A production-ready AI reasoning application built with Gradio and Groq API, featuring multiple research-backed reasoning methodologies, advanced caching, real-time analytics, and comprehensive export capabilities.

## ✨ Features

### 🔬 Research-Backed Reasoning Modes
- **Tree of Thoughts (ToT)** - Systematic exploration of multiple reasoning paths
- **Chain of Thought (CoT)** - Step-by-step logical reasoning
- **Self-Consistency** - Multiple solution paths with consensus
- **Reflexion** - Self-critique and iterative improvement
- **Multi-Agent Debate** - Multiple perspectives and synthesis
- **Analogical Reasoning** - Problem-solving through analogies

### ⚡ Performance Features
- **Response Caching** - LRU cache with TTL for faster responses
- **Rate Limiting** - Token bucket algorithm to prevent API abuse
- **Streaming Responses** - Real-time response generation
- **Multi-threading** - Concurrent request handling

### 📊 Analytics & Monitoring
- **Real-time Metrics** - Live performance tracking
- **Conversation Analytics** - Usage patterns and insights
- **Cache Statistics** - Hit rates and performance metrics
- **Session Tracking** - Unique session identification

### 📤 Export Capabilities
- **Multiple Formats** - JSON, Markdown, TXT, PDF
- **Metadata Support** - Timestamps, models, performance data
- **Automatic Backups** - Periodic conversation backups
- **Search Functionality** - Keyword-based conversation search

### 🎨 User Interface
- **Collapsible Sidebar** - Clean, distraction-free workspace
- **Multiple Tabs** - Reasoning, Export, Analytics, Settings
- **Live Metrics Display** - Real-time performance indicators
- **Responsive Design** - Mobile-friendly interface

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Groq API Key ([Get one here](https://console.groq.com))

### Installation

1. **Clone the repository**
1. **Clone the repository**
git clone <repository-url>
cd reasoning-system-pro

text

2. **Create virtual environment**
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

text

3. **Install dependencies**
pip install -r requirements.txt

text

4. **Configure environment**
cp .env.example .env

Edit .env and add your GROQ_API_KEY
text

5. **Run the application**
python main.py

text

6. **Open in browser**
http://localhost:7860

text

## 📁 Project Structure

reasoning-system-pro/
├── src/
│ ├── api/ # API client management
│ ├── core/ # Core business logic
│ ├── models/ # Data models
│ ├── services/ # Business services
│ ├── ui/ # Gradio interface
│ ├── utils/ # Utilities
│ └── config/ # Configuration
├── tests/ # Test suite
├── exports/ # Generated exports
├── backups/ # Conversation backups
├── logs/ # Application logs
├── main.py # Entry point
├── requirements.txt # Dependencies
└── .env # Environment config

text

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

API
GROQ_API_KEY=your_key_here

Performance
CACHE_SIZE=100
RATE_LIMIT_REQUESTS=50

Features
ENABLE_PDF_EXPORT=true
ENABLE_CACHE=true

text

### Advanced Configuration

Edit `src/config/settings.py` for fine-tuned control over:
- Cache TTL and size
- Rate limiting parameters
- Request timeouts and retries
- File storage locations
- UI themes

## 📖 Usage Examples

### Basic Query
Simply type your question in the chat interface
"Explain quantum entanglement using the Tree of Thoughts method"

text

### With Self-Critique
Enable "Self-Critique" checkbox for automatic validation and refinement.

### Custom Templates
Select from pre-built templates:
- Research Analysis
- Problem Solving
- Code Review
- Writing Enhancement
- Debate Analysis
- Learning Explanation

## 🧪 Testing

Run all tests
pytest

With coverage
pytest --cov=src --cov-report=html

Specific test file
pytest tests/test_reasoner.py

text

## 📊 Available Models

### Meta / Llama Models
- `llama-3.3-70b-versatile` - Best overall performance
- `llama-3.1-8b-instant` - Ultra-fast responses
- `llama-4-maverick-17b-128k` - Experimental long context

### DeepSeek Models
- `deepseek-r1-distill-llama-70b` - Optimized reasoning

### Mixtral Models
- `mixtral-8x7b-32768` - Long context specialist

And many more! See `src/config/constants.py` for the full list.

## 🛠️ Development

### Code Style
Format code
black src/

Check linting
flake8 src/

Type checking
mypy src/

text

### Adding New Reasoning Modes

1. Add to `src/config/constants.py`:
class ReasoningMode(Enum):
YOUR_MODE = "Your Mode Name"

text

2. Add system prompt in `src/core/prompt_engine.py`:
SYSTEM_PROMPTS = {
ReasoningMode.YOUR_MODE: "Your prompt here..."
}

text

## 📝 API Documentation

### Core Classes

#### AdvancedReasoner
Main reasoning engine with streaming support.

reasoner = AdvancedReasoner()
for response in reasoner.generate_response(query, ...):
print(response)

text

#### ResponseCache
Thread-safe LRU cache with TTL.

cache = ResponseCache(maxsize=100, ttl=3600)
cache.set(key, value)
result = cache.get(key)

text

## 🐛 Troubleshooting

### Common Issues

**Issue: "GROQ_API_KEY not found"**
- Solution: Ensure `.env` file exists and contains `GROQ_API_KEY=your_key`

**Issue: PDF export fails**
- Solution: Install reportlab: `pip install reportlab`

**Issue: Rate limit errors**
- Solution: Increase `RATE_LIMIT_WINDOW` in `.env`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Yao et al. (2023)** - Tree of Thoughts
- **Wei et al. (2022)** - Chain of Thought
- **Bai et al. (2022)** - Constitutional AI
- **Groq** - High-speed LLM inference

## 📧 Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review logs in `logs/` directory

---

**Built with ❤️ using Gradio and Groq**