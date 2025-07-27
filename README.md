# ChatDB - Interactive Database Management & Visualization Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy](https://img.shields.io/badge/Deploy-Render-blue.svg)](https://render.com)

A modern, web-based database management and visualization platform built with Flask. ChatDB allows users to upload data, execute SQL queries, create interactive visualizations, and leverage AI-powered query suggestions.

## 🌟 Features

### 📊 Data Management
- **Multi-format Support**: Upload CSV, JSON, and Excel files
- **SQL Query Execution**: Execute SELECT queries with real-time results
- **Data Validation**: Built-in SQL injection prevention and query validation
- **Query History**: Track and review all executed queries

### 📈 Visualization
- **Interactive Charts**: Create bar charts, line charts, and scatter plots
- **Dynamic Plotting**: Automatic data type detection and formatting
- **Export Capabilities**: Download visualizations as high-resolution images
- **Real-time Updates**: Instant chart generation from query results

### 🤖 AI Integration
- **Smart Suggestions**: AI-powered SQL query suggestions using Hugging Face
- **Query Optimization**: Get intelligent recommendations for better queries
- **Error Analysis**: AI assistance for debugging query issues

### 🔐 User Management
- **Secure Authentication**: User registration and login system
- **Session Management**: Persistent user sessions across the application
- **User Dashboard**: Personalized statistics and activity tracking
- **Multi-user Support**: Isolated data and queries per user

### 🎨 Modern Interface
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Bootstrap UI**: Clean, modern interface with intuitive navigation
- **Real-time Feedback**: Instant notifications and status updates
- **Dark Theme**: Professional dark mode interface

## 🚀 Live Demo

**🌐 Application URL**: [https://chatdb-hcm5.onrender.com](https://chatdb-hcm5.onrender.com)

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Git

## 🛠️ Installation

### Local Development

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
   export SECRET_KEY="your-secret-key-here"
   export HUGGINGFACE_API_KEY="your-huggingface-api-key"
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## 🚀 Deployment

### Render (Recommended)

1. **Fork or clone this repository** to your GitHub account

2. **Create a new Web Service** on Render:
   - Connect your GitHub repository
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `gunicorn app:app`

3. **Configure environment variables**:
   - `SECRET_KEY`: Generate a random secret key
   - `HUGGINGFACE_API_KEY`: Your Hugging Face API key

4. **Deploy**: Render will automatically deploy your application

### Alternative Platforms

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Heroku
```bash
# Install Heroku CLI and deploy
heroku create your-app-name
git push heroku main
```

## 📁 Project Structure

```
ChatDB/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment configuration
├── deploy.sh            # Deployment automation script
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Home page
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   ├── dashboard.html  # User dashboard
│   ├── manage.html     # Data management
│   ├── visualize.html  # Visualization page
│   ├── history.html    # Query history
│   └── connect.html    # Database connection
├── static/             # Static assets
│   ├── css/           # Stylesheets
│   └── js/            # JavaScript files
└── README.md          # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for session management | Yes |
| `HUGGINGFACE_API_KEY` | Hugging Face API key for AI features | No |
| `PORT` | Port for the application (auto-set by platform) | No |

### Database Configuration

The application uses SQLite by default, which is perfect for development and small to medium deployments. For production with high traffic, consider:

- **PostgreSQL**: For better performance and concurrent users
- **MySQL**: For enterprise environments
- **Cloud Databases**: AWS RDS, Google Cloud SQL, etc.

## 🎯 Usage

### Getting Started

1. **Register an account** on the application
2. **Upload your data** (CSV, JSON, or Excel files)
3. **Execute queries** using the SQL interface
4. **Create visualizations** from your query results
5. **Explore AI suggestions** for query optimization

### Example Queries

```sql
-- Basic SELECT query
SELECT * FROM your_table LIMIT 10;

-- Aggregation with GROUP BY
SELECT category, COUNT(*) as count 
FROM your_table 
GROUP BY category;

-- Complex joins
SELECT t1.name, t2.value 
FROM table1 t1 
JOIN table2 t2 ON t1.id = t2.id;
```

## 🔒 Security Features

- **SQL Injection Prevention**: Query validation and sanitization
- **Input Validation**: Comprehensive input checking
- **Session Security**: Secure session management
- **Error Handling**: Safe error messages without exposing internals
- **File Upload Security**: File type and size validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask**: Web framework
- **Bootstrap**: UI framework
- **Pandas**: Data manipulation
- **Matplotlib**: Data visualization
- **Hugging Face**: AI integration
- **Render**: Hosting platform

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/DHYEY166/ChatDB/issues) page
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

---

**Made with ❤️ by the ChatDB Team**

