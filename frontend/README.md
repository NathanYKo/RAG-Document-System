# Enterprise RAG System - Streamlit Frontend

A modern, professional-grade Streamlit frontend for the Enterprise Document Intelligence System with RAG capabilities.

## 🌟 Features

### ✨ Enhanced User Experience
- **Intuitive Navigation**: Clean sidebar navigation with visual indicators
- **Real-time Feedback**: Progress bars and status updates for all operations
- **Responsive Design**: Works seamlessly across desktop and mobile devices
- **Professional Styling**: Custom CSS for a polished, modern appearance

### 🔐 Robust Authentication
- **Secure Login/Registration**: JWT token-based authentication
- **Session Management**: Persistent sessions with automatic renewal
- **Input Validation**: Client-side validation for all forms
- **Error Handling**: Comprehensive error messages and recovery options

### 📄 Advanced Document Management
- **Drag & Drop Upload**: Intuitive file upload with progress tracking
- **Multi-format Support**: PDF, DOCX, and TXT file processing
- **Processing Status**: Real-time document processing updates
- **Batch Operations**: Upload multiple documents simultaneously

### 🔍 Intelligent Query Interface
- **Natural Language Queries**: Ask questions in plain English
- **Real-time Processing**: Live progress indicators during query execution
- **Confidence Scoring**: Visual confidence indicators for responses
- **Query History**: Persistent history with search and filters

### 📚 Enhanced Source Citations
- **Smart Highlighting**: Automatic highlighting of relevant text passages
- **Structured Citations**: Properly formatted source references
- **Source Metadata**: Page numbers, document titles, and relevance scores
- **Expandable Sources**: Detailed source information in collapsible panels

### 📊 Comprehensive Analytics
- **Interactive Dashboards**: Dynamic charts and visualizations
- **Real-time Metrics**: Live system statistics and performance data
- **Document Analytics**: Processing status, file type distributions
- **Query Analytics**: Confidence trends, processing time analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Running Enterprise RAG Backend (see backend documentation)
- Environment variables configured (see Configuration section)

### Installation

1. **Clone or create the frontend directory:**
```bash
mkdir frontend && cd frontend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application:**
```bash
streamlit run app.py
```

5. **Access the application:**
Open your browser to `http://localhost:8501`

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
# API Configuration
API_URL=http://localhost:8000
API_TIMEOUT=30
UPLOAD_TIMEOUT=300

# UI Configuration
PAGE_TITLE=Enterprise RAG System
PAGE_ICON=📚
LAYOUT=wide

# File Upload Configuration
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=pdf,txt,docx

# Query Configuration
DEFAULT_MAX_RESULTS=5
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200

# Session Configuration
SESSION_TIMEOUT_MINUTES=30
REMEMBER_ME_DAYS=7

# Analytics Configuration
ENABLE_ANALYTICS=true
ANALYTICS_REFRESH_INTERVAL=300

# Debug Configuration
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### Backend Integration

Ensure your FastAPI backend is running and accessible at the configured `API_URL`. The frontend expects the following endpoints:

- `POST /auth/register` - User registration
- `POST /auth/token` - User authentication
- `GET /users/me` - Get user profile
- `POST /documents/upload` - Document upload
- `GET /documents` - List user documents
- `POST /query` - Query documents
- `POST /feedback` - Submit feedback
- `GET /health` - System health check

## 📱 User Interface Guide

### 🔑 Authentication
1. **Registration**: Create a new account with username, email, and secure password
2. **Login**: Sign in with existing credentials
3. **Session Management**: Automatic token refresh and persistent sessions

### 📄 Document Management
1. **Upload Documents**: Drag and drop files or use the file picker
2. **Processing Options**: Configure chunk size and overlap for optimal processing
3. **Status Tracking**: Monitor document processing status in real-time
4. **Document Library**: View and manage all uploaded documents

### 🔍 Querying Documents
1. **Ask Questions**: Type natural language questions in the query box
2. **Configure Options**: Set maximum results and metadata inclusion
3. **View Results**: Get AI-generated answers with confidence scores
4. **Explore Sources**: Click through source citations and highlighted passages
5. **Provide Feedback**: Rate responses and provide comments for improvement

### 📊 Analytics Dashboard
1. **System Metrics**: View key performance indicators and statistics
2. **Document Analytics**: Analyze document processing and status distributions
3. **Query Analytics**: Track query performance and confidence trends
4. **Interactive Charts**: Explore data with dynamic visualizations

## 🔧 Development

### Project Structure
```
frontend/
├── app.py              # Main Streamlit application
├── utils.py            # Utility functions and helpers
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── README.md          # This documentation
├── .env.example       # Environment variables template
└── .gitignore         # Git ignore rules
```

### Code Organization

- **`app.py`**: Main application with page routing and UI components
- **`utils.py`**: Utility functions for formatting, validation, and session management
- **`config.py`**: Centralized configuration management
- **API Integration**: Robust API client with error handling and retries

### Adding New Features

1. **New Pages**: Add page functions to `app.py` and update navigation
2. **API Endpoints**: Extend the `APIClient` class with new methods
3. **UI Components**: Create reusable components in separate functions
4. **Styling**: Update CSS in `utils.apply_custom_css()`

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py --server.port 8501
```

### Production Deployment

1. **Docker Container:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

2. **Environment Setup:**
- Configure production environment variables
- Set up SSL certificates for HTTPS
- Configure reverse proxy (nginx/Apache)

3. **Cloud Deployment:**
- **Streamlit Cloud**: Direct GitHub integration
- **Heroku**: Use provided Procfile
- **AWS/GCP/Azure**: Container-based deployment

## 🛡️ Security Considerations

- **JWT Token Management**: Secure token storage and automatic refresh
- **Input Validation**: Client-side validation for all user inputs
- **XSS Protection**: Proper escaping of user-generated content
- **CSRF Protection**: Token-based request validation
- **Rate Limiting**: Implemented in API client
- **Environment Variables**: Sensitive data stored securely

## 🧪 Testing

### Manual Testing Checklist
- [ ] User registration and login
- [ ] Document upload and processing
- [ ] Query submission and response
- [ ] Source highlighting and citations
- [ ] Analytics dashboard functionality
- [ ] Error handling and recovery
- [ ] Mobile responsiveness
- [ ] Cross-browser compatibility

### Automated Testing
```bash
# Install testing dependencies
pip install pytest streamlit-testing

# Run tests
pytest tests/
```

## 📈 Performance Optimization

- **Lazy Loading**: Components loaded on demand
- **Caching**: Strategic use of Streamlit caching decorators
- **Async Operations**: Non-blocking API calls where possible
- **Image Optimization**: Compressed images and icons
- **Bundle Size**: Minimal dependency footprint

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify backend is running at configured API_URL
   - Check network connectivity and firewall settings

2. **Authentication Failures**
   - Ensure JWT_SECRET_KEY matches between frontend and backend
   - Check token expiration settings

3. **File Upload Errors**
   - Verify file size limits and allowed types
   - Check backend storage configuration

4. **Query Timeouts**
   - Increase API_TIMEOUT in configuration
   - Optimize backend query processing

### Debug Mode
Enable debug mode in configuration:
```env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper documentation
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section above
- Review the backend documentation
- Open an issue on the project repository
- Contact the development team

---

**Built with ❤️ using Streamlit and modern web technologies** 