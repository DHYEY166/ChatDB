# ChatDB - Modern Database Management Platform

**ChatDB** is a powerful, modern web-based application that simplifies database management and visualization. Built with Flask and featuring a beautiful, responsive UI, ChatDB provides an intuitive interface for connecting to databases, managing data, executing queries, and creating visualizations.

![ChatDB Screenshot](https://via.placeholder.com/800x400/667eea/ffffff?text=ChatDB+Platform)

## ✨ Features

### 🔌 Database Connectivity
- **Multi-Database Support**: Connect to SQLite, MySQL, PostgreSQL, and more
- **Secure Connections**: Advanced input validation and connection security
- **Real-time Status**: Instant feedback on connection status

### 📊 Data Management
- **File Upload**: Drag & drop CSV/JSON file uploads with automatic processing
- **Query Execution**: Execute SQL queries with real-time results
- **Query History**: Track and reuse previous queries
- **AI-Powered Suggestions**: Get intelligent query suggestions using OpenAI

### 📈 Visualization
- **Multiple Chart Types**: Bar charts, line charts, scatter plots
- **Customizable**: Choose X/Y axes and chart types
- **High-Quality Output**: Professional-grade visualizations with value labels
- **Export Ready**: Download charts for presentations

### 📋 Reporting
- **CSV Export**: Generate downloadable reports
- **Data Summary**: Row/column counts and execution metrics
- **Performance Tracking**: Monitor query execution times

### 🛡️ Security Features
- **SQL Injection Protection**: Advanced query sanitization
- **Rate Limiting**: Prevent abuse with intelligent throttling
- **File Validation**: Secure file upload processing
- **Input Validation**: Comprehensive data validation

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Dark Mode**: Beautiful gradient backgrounds and modern styling
- **Loading States**: Smooth loading animations and progress indicators
- **Toast Notifications**: Real-time feedback and status updates
- **Keyboard Shortcuts**: Ctrl+Enter to execute queries

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- A database system (SQLite, MySQL, PostgreSQL, etc.)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/DHYEY166/ChatDB.git
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
   export OPENAI_API_KEY="your-openai-api-key"  # Optional for AI features
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://127.0.0.1:5000`

## 🌐 Deployment

### Vercel Deployment (Recommended)

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy the application**
   ```bash
   vercel --prod
   ```

4. **Set environment variables in Vercel dashboard**
   - `SECRET_KEY`: Your secret key for session management
   - `OPENAI_API_KEY`: Your OpenAI API key (optional)

### Alternative Deployment Options

#### Heroku
```bash
# Create Heroku app
heroku create your-chatdb-app

# Set environment variables
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set OPENAI_API_KEY="your-openai-api-key"

# Deploy
git push heroku main
```

#### Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

## 📁 Project Structure

```
ChatDB/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── vercel.json          # Vercel configuration
├── static/
│   ├── css/
│   │   └── styles.css   # Modern CSS styling
│   └── js/
│       └── scripts.js   # Enhanced JavaScript
├── templates/
│   ├── base.html        # Base template with modern UI
│   ├── index.html       # Homepage with feature cards
│   ├── manage.html      # Data management interface
│   ├── connect.html     # Database connection
│   ├── visualize.html   # Chart generation
│   └── report.html      # Report generation
└── data/
    └── example.db       # SQLite database
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | No |

### Database Connection Strings

- **SQLite**: `sqlite:///path/to/database.db`
- **MySQL**: `mysql+pymysql://user:password@host:port/database`
- **PostgreSQL**: `postgresql://user:password@host:port/database`

## 🎯 Usage Guide

### 1. Connect to Database
1. Navigate to the "Connect" page
2. Enter your database connection string
3. Click "Connect" to establish the connection

### 2. Upload Data
1. Go to the "Manage" page
2. Drag & drop CSV/JSON files or click to browse
3. Select file type and upload
4. Data is automatically processed and stored

### 3. Execute Queries
1. Use the query editor on the "Manage" page
2. Type your SQL query or use AI suggestions
3. Click "Execute Query" or press Ctrl+Enter
4. View results in both tabular and JSON formats

### 4. Create Visualizations
1. Navigate to the "Visualize" page
2. Enter a SQL query
3. Select X-axis, Y-axis, and chart type
4. Generate beautiful charts with value labels

### 5. Generate Reports
1. Go to the "Reports" page
2. Provide JSON data
3. Generate downloadable CSV reports

## 🛠️ Development

### Adding New Features

1. **Backend (Flask)**
   - Add routes in `app.py`
   - Implement security measures
   - Add rate limiting where appropriate

2. **Frontend (HTML/CSS/JS)**
   - Create templates in `templates/`
   - Style with modern CSS in `static/css/`
   - Add interactivity in `static/js/`

### Code Style

- Follow PEP 8 for Python code
- Use modern ES6+ JavaScript
- Implement responsive design principles
- Add comprehensive error handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
flask run --debug

# Run tests (if available)
python -m pytest
```

## 📊 Performance

- **Fast Loading**: Optimized assets and lazy loading
- **Efficient Queries**: Query optimization and caching
- **Responsive UI**: Smooth animations and transitions
- **Mobile Optimized**: Touch-friendly interface

## 🔒 Security

- **SQL Injection Protection**: Advanced query sanitization
- **Rate Limiting**: Prevents abuse and DDoS attacks
- **File Upload Security**: Validated file types and sizes
- **Session Security**: Secure session management
- **Input Validation**: Comprehensive data validation

## 📈 Monitoring

- **Query Performance**: Execution time tracking
- **Error Logging**: Comprehensive error handling
- **User Analytics**: Usage statistics and metrics
- **Health Checks**: Application status monitoring

## 🎨 UI/UX Features

- **Modern Design**: Gradient backgrounds and glass morphism
- **Responsive Layout**: Works on all device sizes
- **Smooth Animations**: CSS transitions and micro-interactions
- **Loading States**: Progress indicators and spinners
- **Toast Notifications**: Real-time user feedback
- **Keyboard Shortcuts**: Power user features

## 📱 Mobile Support

- **Touch Optimized**: Large touch targets
- **Responsive Tables**: Horizontal scrolling on mobile
- **Mobile Navigation**: Collapsible menu
- **Touch Gestures**: Swipe and tap interactions

## 🔮 Future Roadmap

- [ ] Real-time collaboration features
- [ ] Advanced chart types (3D, heatmaps)
- [ ] Database schema visualization
- [ ] Export to multiple formats (PDF, Excel)
- [ ] User authentication and roles
- [ ] API endpoints for external integrations
- [ ] Dark/light theme toggle
- [ ] Offline mode support

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 👥 Team

- **Developer**: [DHYEY166](https://github.com/DHYEY166)
- **Design**: Modern UI/UX with Bootstrap 5
- **Backend**: Flask with SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/DHYEY166/ChatDB/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DHYEY166/ChatDB/discussions)
- **Email**: Contact through GitHub profile

---

**Made with ❤️ by the ChatDB Team**

*Empowering developers to manage databases with ease and style.*

