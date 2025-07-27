# ChatDB - Intelligent Database Management Platform

**ChatDB** is a modern, web-based application that simplifies database management and visualization. With an intuitive interface and powerful features, ChatDB helps you connect to databases, manage data, execute queries, generate reports, and create beautiful visualizations.

![ChatDB Demo](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🔌 Database Connectivity
- **Multiple Database Support**: Connect to SQLite, MySQL, PostgreSQL, and more
- **Secure Connections**: Encrypted connections with proper authentication
- **Connection Validation**: Real-time connection testing and validation
- **URI Templates**: Pre-configured connection strings for easy setup

### 📊 Data Management
- **File Upload**: Support for CSV, JSON, and Excel files
- **Automatic Processing**: Smart data type detection and table creation
- **Query Execution**: Execute SQL queries with real-time results
- **Data Validation**: Input sanitization and SQL injection prevention

### 📈 Data Visualization
- **Multiple Chart Types**: Bar charts, line charts, scatter plots, and pie charts
- **Interactive Charts**: Responsive visualizations with hover effects
- **Custom Styling**: Beautiful, modern chart designs
- **Export Options**: Download charts as high-resolution images

### 📋 Report Generation
- **CSV Export**: Generate downloadable reports in CSV format
- **Custom Data**: Upload JSON data for custom report generation
- **Timestamped Files**: Automatic file naming with timestamps
- **Data Validation**: JSON validation and error handling

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Modern Styling**: Beautiful gradient backgrounds and smooth animations
- **Loading States**: Visual feedback during operations
- **Error Handling**: User-friendly error messages and alerts

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- A database system (SQLite, MySQL, PostgreSQL, etc.)

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/DHYEY166/ChatDB.git
   cd ChatDB
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create a .env file (optional)
   echo "SECRET_KEY=your-secret-key-here" > .env
   echo "FLASK_ENV=development" >> .env
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://127.0.0.1:5000`

## 🌐 Deployment

### Railway Deployment (Recommended)

1. **Fork this repository** to your GitHub account

2. **Connect to Railway**
   - Go to [Railway.app](https://railway.app)
   - Sign in with your GitHub account
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your forked repository

3. **Configure Environment Variables** (Optional)
   - Go to your project settings
   - Add environment variables:
     - `SECRET_KEY`: A secure random string
     - `OPENAI_API_KEY`: Your OpenAI API key (if using AI features)

4. **Deploy**
   - Railway will automatically detect the Python app
   - The app will be deployed and you'll get a live URL

### Alternative Deployment Options

#### Heroku
```bash
# Install Heroku CLI
heroku create your-app-name
git push heroku main
```

#### Vercel
```bash
# Install Vercel CLI
npm i -g vercel
vercel
```

#### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

## 📁 Project Structure

```
ChatDB/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku deployment config
├── railway.json          # Railway deployment config
├── runtime.txt           # Python version specification
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── connect.html      # Database connection
│   ├── manage.html       # Data management
│   ├── visualize.html    # Data visualization
│   ├── report.html       # Report generation
│   ├── 404.html          # 404 error page
│   └── 500.html          # 500 error page
├── static/               # Static files
│   ├── css/
│   │   └── styles.css    # Custom styles
│   └── js/
│       └── scripts.js    # JavaScript functionality
├── data/                 # Database files
│   └── example.db        # SQLite database
└── uploads/              # File upload directory
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `FLASK_ENV` | Flask environment | `production` |
| `DATABASE_URL` | Database connection string | `sqlite:///data/example.db` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | None |
| `PORT` | Server port | `5000` |

### Database Connection Examples

```bash
# SQLite
sqlite:///data/example.db

# MySQL
mysql+pymysql://username:password@localhost/database_name

# PostgreSQL
postgresql://username:password@localhost/database_name
```

## 🛡️ Security Features

- **SQL Injection Prevention**: Query validation and sanitization
- **File Upload Security**: File type validation and size limits
- **Input Sanitization**: XSS prevention and data cleaning
- **Secure Headers**: CSRF protection and security headers
- **Error Handling**: Safe error messages without information leakage

## 🎨 UI/UX Improvements

- **Modern Design**: Gradient backgrounds and smooth animations
- **Responsive Layout**: Mobile-first design approach
- **Loading States**: Visual feedback during operations
- **Toast Notifications**: User-friendly success/error messages
- **Copy to Clipboard**: Easy data copying functionality
- **Auto-resize Textareas**: Dynamic form field sizing

## 🔄 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Homepage |
| `/connect` | GET/POST | Database connection |
| `/manage` | GET/POST | Data management and queries |
| `/upload` | POST | File upload |
| `/visualize` | GET/POST | Data visualization |
| `/report` | GET/POST | Report generation |

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask**: Web framework
- **Bootstrap**: CSS framework
- **Font Awesome**: Icons
- **Matplotlib**: Data visualization
- **Pandas**: Data manipulation
- **SQLAlchemy**: Database ORM

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/DHYEY166/ChatDB/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DHYEY166/ChatDB/discussions)
- **Email**: [Contact Maintainer](mailto:your-email@example.com)

---

**Made with ❤️ by [DHYEY166](https://github.com/DHYEY166)**

