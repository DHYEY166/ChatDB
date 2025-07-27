# ChatDB - Interactive Database Management Platform

**ChatDB** is a modern, web-based application that simplifies database management and visualization. With an intuitive interface, you can connect to databases, upload data, execute queries, create visualizations, and generate reports.

![ChatDB Demo](https://img.shields.io/badge/Status-Live-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.0-red)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

### 🔌 Database Connectivity
- **Multi-Database Support**: Connect to SQLite, MySQL, and PostgreSQL
- **Secure Connections**: Input validation and connection testing
- **Easy Setup**: Simple URI-based connection interface

### 📊 Data Management
- **File Upload**: Drag & drop support for CSV, JSON, and Excel files
- **Query Execution**: Run SQL queries with real-time results
- **Query History**: Track and reuse previous queries
- **Data Export**: Export results to CSV format

### 📈 Data Visualization
- **Multiple Chart Types**: Bar charts, line charts, and scatter plots
- **Interactive Charts**: Beautiful, responsive visualizations
- **Customizable**: Specify X-axis, Y-axis, and chart types
- **Export Ready**: High-resolution chart exports

### 📋 Report Generation
- **CSV Reports**: Generate downloadable reports
- **Data Processing**: Handle complex JSON data structures
- **Easy Sharing**: One-click report downloads

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Git

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

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🌐 Deployment

### Option 1: Deploy to Vercel (Recommended)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy the application**
   ```bash
   vercel --prod
   ```

4. **Set environment variables** (if needed)
   ```bash
   vercel env add SECRET_KEY
   vercel env add OPENAI_API_KEY
   ```

### Option 2: Deploy to Heroku

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku app**
   ```bash
   heroku create your-chatdb-app
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set OPENAI_API_KEY=your-openai-key
   ```

### Option 3: Deploy to Railway

1. **Connect your GitHub repository to Railway**
2. **Railway will automatically detect the Python app**
3. **Set environment variables in Railway dashboard**
4. **Deploy with one click**

## 📁 Project Structure

```
ChatDB/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel deployment config
├── runtime.txt           # Python runtime specification
├── Procfile             # Heroku deployment config
├── static/              # Static assets
│   ├── css/
│   │   └── styles.css   # Custom styles
│   └── js/
│       └── scripts.js   # JavaScript functionality
├── templates/           # HTML templates
│   ├── base.html        # Base layout
│   ├── index.html       # Homepage
│   ├── connect.html     # Database connection
│   ├── manage.html      # Data management
│   ├── visualize.html   # Data visualization
│   └── report.html      # Report generation
└── data/               # Database files
    └── example.db      # SQLite database
```

## 🛠️ Usage Guide

### 1. Connect to Database
- Navigate to the **Connect** page
- Enter your database URI:
  - SQLite: `sqlite:///path/to/database.db`
  - MySQL: `mysql+pymysql://user:password@host/database`
  - PostgreSQL: `postgresql://user:password@host/database`
- Click **Connect** to establish connection

### 2. Upload Data
- Go to the **Manage** page
- Drag & drop files or click to browse
- Supported formats: CSV, JSON, Excel
- Files are automatically processed and stored as tables

### 3. Execute Queries
- Use the query editor in the **Manage** page
- Write SQL queries and click **Execute**
- View results in a formatted table
- Export results to CSV

### 4. Create Visualizations
- Navigate to the **Visualize** page
- Enter a SQL query
- Select X-axis, Y-axis, and chart type
- Generate beautiful charts

### 5. Generate Reports
- Go to the **Reports** page
- Provide JSON data
- Generate downloadable CSV reports

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `supersecretkey` |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `PORT` | Server port | `5000` |

### Database Configuration

The app supports multiple database types:

- **SQLite**: Built-in, no additional setup required
- **MySQL**: Requires `mysql-connector-python`
- **PostgreSQL**: Requires `psycopg2-binary`

## 🎨 Customization

### Styling
- Modify `static/css/styles.css` for custom styling
- The app uses Bootstrap 5 with custom gradients and animations

### Features
- Add new routes in `app.py`
- Create new templates in `templates/`
- Extend functionality with additional JavaScript in `static/js/`

## 🔒 Security Features

- **SQL Injection Protection**: Query sanitization and validation
- **File Upload Security**: File type validation and size limits
- **Input Validation**: Comprehensive input checking
- **Error Handling**: Secure error messages

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check your database URI format
   - Ensure database server is running
   - Verify credentials

2. **File Upload Issues**
   - Check file size (max 16MB)
   - Ensure file format is supported
   - Verify file permissions

3. **Deployment Issues**
   - Check environment variables
   - Verify Python version compatibility
   - Review deployment logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask team for the excellent web framework
- Bootstrap team for the responsive UI components
- Font Awesome for the beautiful icons
- Matplotlib for the charting capabilities

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ChatDB/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ChatDB/discussions)
- **Email**: your-email@example.com

---

**Made with ❤️ by [Your Name]**

