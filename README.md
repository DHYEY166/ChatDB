# ChatDB - Enhanced Database Management Platform

**ChatDB** is a modern, interactive web-based application that simplifies database management and visualization. With enhanced security, AI-powered features, and a beautiful user interface, ChatDB makes database operations intuitive and efficient.

![ChatDB Dashboard](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.0-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ New Features (v2.0)

### 🔐 Enhanced Security
- **User Authentication**: Secure login/registration system
- **Session Management**: Protected routes and user sessions
- **SQL Injection Prevention**: Query validation and sanitization
- **Password Hashing**: Secure password storage with Werkzeug

### 🤖 AI-Powered Features
- **Query Suggestions**: Get intelligent SQL query improvements
- **Error Analysis**: AI-powered error explanations
- **Smart Recommendations**: Context-aware database suggestions

### 📊 Advanced Analytics
- **Query History**: Track and review all executed queries
- **Performance Metrics**: Execution time and success rate tracking
- **User Dashboard**: Comprehensive statistics and insights
- **Export Capabilities**: Download query history and reports

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on all devices
- **Dark Theme**: Professional dark mode interface
- **Interactive Charts**: Beautiful data visualizations
- **Real-time Feedback**: Live status updates and notifications

### 📈 Enhanced Data Management
- **Multi-format Support**: CSV, JSON, Excel file uploads
- **Connection Management**: Save and manage multiple database connections
- **Advanced Visualization**: Bar charts, line charts, scatter plots
- **Report Generation**: Automated CSV report creation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- A modern web browser

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ChatDB.git
   cd ChatDB
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export OPENAI_API_KEY="your-openai-api-key"  # Optional
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

---

## 🌐 Free Deployment

### Option 1: Render (Recommended)

1. **Fork this repository** to your GitHub account

2. **Sign up for Render** at [render.com](https://render.com)

3. **Create a new Web Service**
   - Connect your GitHub repository
   - Choose the repository you just forked
   - Set the following:
     - **Name**: `chatdb`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`

4. **Set Environment Variables**
   - `SECRET_KEY`: Generate a random string
   - `OPENAI_API_KEY`: Your OpenAI API key (optional)

5. **Deploy!**
   Click "Create Web Service" and wait for deployment

### Option 2: Railway

1. **Sign up for Railway** at [railway.app](https://railway.app)

2. **Connect your GitHub repository**

3. **Deploy automatically**
   Railway will detect the Python app and deploy it

### Option 3: Heroku (Legacy)

1. **Install Heroku CLI**
2. **Create Heroku app**
   ```bash
   heroku create your-chatdb-app
   ```
3. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY="your-secret-key"
   heroku config:set OPENAI_API_KEY="your-openai-key"
   ```
4. **Deploy**
   ```bash
   git push heroku main
   ```

---

## 📁 Project Structure

```
ChatDB/
├── app.py                 # Main Flask application
├── database_setup.py      # Database setup utilities
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── deploy.sh            # Deployment script
├── templates/           # HTML templates
│   ├── base.html       # Base layout
│   ├── index.html      # Homepage
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   ├── dashboard.html  # User dashboard
│   ├── manage.html     # Data management
│   ├── visualize.html  # Data visualization
│   ├── history.html    # Query history
│   └── error pages     # 404, 500 pages
├── static/             # Static files
│   ├── css/           # Stylesheets
│   └── js/            # JavaScript files
└── data/              # Database files
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | Auto-generated |
| `OPENAI_API_KEY` | OpenAI API key for AI features | No | None |
| `PORT` | Server port | No | 5000 |

### Database Support

- **SQLite**: Built-in support (default)
- **MySQL**: Requires `mysql-connector-python`
- **PostgreSQL**: Requires `psycopg2-binary`

---

## 🎯 Features

### 🔐 Authentication & Security
- User registration and login
- Password hashing and validation
- Session management
- Protected routes
- SQL injection prevention

### 📊 Data Management
- Multi-format file uploads (CSV, JSON, Excel)
- SQL query execution
- Real-time data visualization
- Report generation
- Query history tracking

### 🤖 AI Integration
- Query optimization suggestions
- Error analysis and explanations
- Smart database recommendations
- Context-aware assistance

### 📈 Analytics & Monitoring
- Query performance metrics
- Success rate tracking
- User activity monitoring
- Export capabilities

### 🎨 User Interface
- Responsive Bootstrap design
- Dark theme support
- Interactive charts
- Real-time notifications
- Mobile-friendly interface

---

## 🛠️ Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
```bash
black .
flake8 .
```

### Database Migrations
```bash
flask db upgrade
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
pre-commit install
pre-commit run --all-files
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Flask** - Web framework
- **Bootstrap** - CSS framework
- **Chart.js** - Data visualization
- **FontAwesome** - Icons
- **OpenAI** - AI features

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ChatDB/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ChatDB/discussions)
- **Email**: your-email@example.com

---

## 🔄 Changelog

### v2.0.0 (Current)
- ✨ Added user authentication system
- 🤖 Integrated AI-powered query suggestions
- 📊 Enhanced analytics and dashboard
- 🎨 Modernized UI with dark theme
- 🔐 Improved security features
- 📈 Added query history and performance tracking

### v1.0.0
- 🎉 Initial release
- 📊 Basic database management
- 📈 Simple data visualization
- 📁 File upload support

---

**Made with ❤️ by [Your Name]**

