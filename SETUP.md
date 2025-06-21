# 🚀 Smart AI Chatbot - Setup & Deployment Guide

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended for production)
- **Storage**: 2GB free space for models and data
- **OS**: Windows, macOS, or Linux

### Required Software
- **Git**: For version control
- **Python pip**: Package manager
- **Virtual Environment**: For dependency isolation

## 🛠️ Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/tahadeab/graduation-ai-chatbot.git
cd graduation-ai-chatbot
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
# Use any text editor to modify the configuration
```

### 5. Create Required Directories
```bash
# Create directories for data and models
mkdir -p data/training
mkdir -p data/knowledge_base
mkdir -p models
mkdir -p logs
```

### 6. Initialize Database
```bash
# The database will be created automatically on first run
python app.py
```

## 🔧 Configuration

### Environment Variables (.env file)

#### Essential Settings
```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=False
FLASK_ENV=production

# Database Configuration
DATABASE_URL=sqlite:///chatbot.db
```

#### AI/ML Model Settings
```bash
# Model Configuration
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
GENERATIVE_MODEL=microsoft/DialoGPT-medium
SENTIMENT_MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest

# FAISS Configuration
FAISS_INDEX_PATH=models/faiss_index
FAISS_DIMENSION=384
```

#### Performance Settings
```bash
# Performance Configuration
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
CACHE_TTL=3600

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/chatbot.log
```

## 🚀 Running the Application

### Development Mode
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run in development mode
export FLASK_ENV=development  # Linux/macOS
# or
set FLASK_ENV=development     # Windows

python app.py
```

### Production Mode
```bash
# Set production environment
export FLASK_ENV=production
export SECRET_KEY=your-production-secret-key

# Run with Gunicorn (recommended for production)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker (Optional)
```bash
# Build Docker image
docker build -t smart-ai-chatbot .

# Run container
docker run -p 5000:5000 -e SECRET_KEY=your-secret smart-ai-chatbot
```

## 🌐 Accessing the Application

### Web Interface
- **URL**: http://localhost:5000
- **Features**: Real-time chat, language switching, feedback system

### API Endpoints
- **Health Check**: GET http://localhost:5000/api/health
- **Chat**: POST http://localhost:5000/api/chat
- **Feedback**: POST http://localhost:5000/api/feedback
- **Conversations**: GET http://localhost:5000/api/conversations/{user_id}
- **Translation**: POST http://localhost:5000/api/translate

## 📊 Monitoring & Logs

### Log Files
- **Application Logs**: `logs/chatbot.log`
- **Error Logs**: `logs/error.log`
- **Access Logs**: `logs/access.log`

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about application flow
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may cause system failure

### Monitoring Commands
```bash
# View real-time logs
tail -f logs/chatbot.log

# Check application status
curl http://localhost:5000/api/health

# Monitor system resources
htop  # or top
```

## 🔄 Training Pipeline

### Initial Training
```bash
# Run initial training (optional)
python -c "
from src.services.training_service import TrainingService
training_service = TrainingService()
training_service.run_training_pipeline()
"
```

### Scheduled Training
```bash
# Set up cron job for automatic training (Linux/macOS)
# Add to crontab: 0 2 * * 0 /path/to/chatbot/venv/bin/python -c "from src.services.training_service import TrainingService; TrainingService().run_training_pipeline()"

# Windows Task Scheduler
# Create a scheduled task to run training weekly
```

## 🗄️ Database Management

### Database Operations
```bash
# Initialize database (automatic on first run)
python -c "from src.database.models import init_db; from app import app; init_db(app)"

# Reset database (development only)
rm chatbot.db  # SQLite
# or
python -c "from src.database.models import db; db.drop_all(); db.create_all()"

# Database backup
cp chatbot.db backup/chatbot_$(date +%Y%m%d_%H%M%S).db
```

### Database Schema
- **Users**: User information and preferences
- **Conversations**: Chat messages and responses
- **Feedback**: User ratings and comments
- **TrainingData**: Data for model improvement
- **ModelVersion**: ML model versioning
- **EmbeddingCache**: Performance optimization

## 🔒 Security Configuration

### Production Security Checklist
- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set up database encryption
- [ ] Enable input validation
- [ ] Configure logging security

### Security Commands
```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Check for security vulnerabilities
pip audit

# Update dependencies
pip install --upgrade -r requirements.txt
```

## 📈 Performance Optimization

### Performance Settings
```bash
# Increase concurrent requests
MAX_CONCURRENT_REQUESTS=1000

# Optimize cache settings
CACHE_TTL=7200
EMBEDDING_CACHE_SIZE=50000

# Database optimization
SQLALCHEMY_ENGINE_OPTIONS={"pool_size": 20, "pool_recycle": 3600}
```

### Monitoring Performance
```bash
# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/health

# Check memory usage
ps aux | grep python

# Monitor database performance
sqlite3 chatbot.db "PRAGMA cache_size = 10000;"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Model Download Issues
```bash
# Solution: Check internet connection and try again
# Models are downloaded automatically on first use
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('microsoft/DialoGPT-medium')"
```

#### 3. Database Connection Errors
```bash
# Solution: Check database path and permissions
ls -la chatbot.db
chmod 644 chatbot.db
```

#### 4. Memory Issues
```bash
# Solution: Reduce model complexity or increase system memory
# Edit config.py to use smaller models
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2  # Smaller model
```

#### 5. Port Already in Use
```bash
# Solution: Change port or kill existing process
lsof -ti:5000 | xargs kill -9
# or
python app.py --port 5001
```

### Debug Mode
```bash
# Enable debug mode for detailed error messages
export FLASK_ENV=development
export DEBUG=True
python app.py
```

## 🔄 Updates & Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart application
pkill -f "python app.py"
python app.py
```

### Backup Strategy
```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/$DATE"
mkdir -p $BACKUP_DIR

# Backup database
cp chatbot.db $BACKUP_DIR/

# Backup models
cp -r models $BACKUP_DIR/

# Backup logs
cp -r logs $BACKUP_DIR/

# Backup configuration
cp .env $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

## 📞 Support

### Getting Help
- **Documentation**: Check README.md and PROJECT_OVERVIEW.md
- **Issues**: Create GitHub issue with detailed description
- **Email**: tahadeab201@gmail.com
- **GitHub**: https://github.com/tahadeab

### Useful Commands
```bash
# Check system status
python -c "from app import app; print('App loaded successfully')"

# Test API endpoints
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test", "language": "en"}'

# Check logs
tail -n 50 logs/chatbot.log

# Monitor system resources
htop
```

---

**This setup guide provides comprehensive instructions for installing, configuring, and maintaining the Smart AI Chatbot system. Follow these steps carefully for a successful deployment.** 