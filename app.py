from flask import Flask, render_template, jsonify, request, session as flask_session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import pandas as pd
import os
import logging
import matplotlib
import matplotlib.pyplot as plt
import secrets
import hashlib
import sqlite3
from datetime import datetime, timedelta
import json
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
matplotlib.use('Agg')

# Initialize Flask app
app = Flask(__name__)

# Security improvements
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Configure the SQLite database - use /tmp for Render (writable location)
# On Render, /tmp is writable, other locations may be read-only
db_path = "/tmp/chatdb.db"
print(f"Database Path: {db_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Hugging Face API Key
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define enhanced Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class QueryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    query = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50), nullable=False)  # 'select', 'insert', 'update', 'delete'
    execution_time = db.Column(db.Float)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DatabaseConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    connection_string = db.Column(db.Text, nullable=False)
    database_type = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Security decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if 'user_id' not in flask_session:
                logger.info("User not logged in, redirecting to login")
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            # Verify user still exists in database
            user_id = flask_session.get('user_id')
            user = User.query.get(user_id)
            
            if not user:
                logger.warning(f"User {user_id} not found in database, clearing session")
                flask_session.clear()
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('login'))
            
            logger.info(f"User {user.username} accessing protected page")
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in login_required decorator: {e}")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('login'))
    
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in flask_session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        # Add admin check logic here if needed
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def log_query(query, query_type, execution_time=None, success=True, error_message=None):
    """Log query execution for analytics"""
    try:
        user_id = flask_session.get('user_id')
        history = QueryHistory(
            user_id=user_id,
            query=query,
            query_type=query_type,
            execution_time=execution_time,
            success=success,
            error_message=error_message
        )
        db.session.add(history)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging query: {e}")

def get_hf_query_suggestion(user_query):
    """Get AI-powered query suggestions using Hugging Face"""
    if not HUGGINGFACE_API_KEY:
        return None
    
    try:
        # Using Hugging Face Inference API with a text generation model
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
        # Create a prompt for SQL query improvement
        prompt = f"Improve this SQL query for better performance and readability: {user_query}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 150,
                "temperature": 0.7,
                "do_sample": True
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'No suggestion available.')
            return result.get('generated_text', 'No suggestion available.')
        else:
            logger.error(f"Hugging Face API error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Hugging Face suggestion: {e}")
        return None

def validate_sql_query(query):
    """Basic SQL injection prevention"""
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
    query_upper = query.upper().strip()
    
    # Check for dangerous operations
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return False, f"Operation '{keyword}' is not allowed for security reasons"
    
    return True, "Query is safe"

def init_database():
    """Initialize database with proper error handling"""
    try:
        print("Initializing database...")
        print(f"Database path: {db_path}")
        
        # First, try to create tables manually to ensure they exist
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        # Create tables manually
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT NOT NULL,
                query_type VARCHAR(50) NOT NULL,
                execution_time FLOAT,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS database_connection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name VARCHAR(100) NOT NULL,
                connection_string TEXT NOT NULL,
                database_type VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')

        conn.commit()
        conn.close()
        print("Database tables created manually")
        
        # Now try SQLAlchemy initialization
        with app.app_context():
            db.create_all()
            print("SQLAlchemy tables created successfully")
            
            # Test the database
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            print("Database connection test successful")
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        logger.error(f"Database initialization error: {e}")
        # If SQLAlchemy fails, we already have the tables from manual creation
        print("Using manually created tables")

def reset_database():
    """Reset database for Render deployment"""
    try:
        # Remove existing database file
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info("Removed existing database file")
        
        # Create fresh database
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        # Create tables with proper schema
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT NOT NULL,
                query_type VARCHAR(50) NOT NULL,
                execution_time FLOAT,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS database_connection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name VARCHAR(100) NOT NULL,
                connection_string TEXT NOT NULL,
                database_type VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database reset successful")
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False

@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Test database connection
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            db.session.commit()
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/')
def index():
    return render_template('index.html', title="Home")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            logger.info(f"Login attempt for username: {username}")
            
            # Validate input
            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('login.html', title="Login")
            
            # Find user
            user = User.query.filter_by(username=username).first()
            
            if user:
                logger.info(f"User found: {username}")
                # Check password
                if user.check_password(password):
                    logger.info(f"Password check successful for {username}")
                    
                    # Set up session
                    flask_session.permanent = True
                    flask_session['user_id'] = user.id
                    flask_session['username'] = user.username
                    
                    # Debug: Print session data
                    logger.info(f"Session data after login: {dict(flask_session)}")
                    logger.info(f"User ID in session: {flask_session.get('user_id')}")
                    logger.info(f"Username in session: {flask_session.get('username')}")
                    
                    # Update last login
                    user.last_login = datetime.utcnow()
                    db.session.commit()
                    
                    logger.info(f"Login successful for {username}, user_id: {user.id}")
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))
                else:
                    logger.info(f"Password check failed for {username}")
                    flash('Invalid username or password', 'error')
            else:
                logger.info(f"User not found: {username}")
                flash('Invalid username or password', 'error')
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html', title="Login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            logger.info(f"Registration attempt for username: {username}, email: {email}")
            
            # Validate input
            if not username or not email or not password:
                flash('All fields are required', 'error')
                return render_template('register.html', title="Register")
            
            if len(username) < 3:
                flash('Username must be at least 3 characters long', 'error')
                return render_template('register.html', title="Register")
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('register.html', title="Register")
            
            # Try to create tables if they don't exist
            try:
                # Test if user table exists
                db.session.execute(text("SELECT 1 FROM user LIMIT 1"))
                db.session.commit()
                logger.info("User table exists")
            except Exception as table_error:
                logger.info(f"User table doesn't exist, creating tables: {table_error}")
                # Create tables manually
                import sqlite3
                conn = sqlite3.connect(db_path)
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS user (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_login DATETIME
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS query_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        query TEXT NOT NULL,
                        query_type VARCHAR(50) NOT NULL,
                        execution_time FLOAT,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user (id)
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS database_connection (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        name VARCHAR(100) NOT NULL,
                        connection_string TEXT NOT NULL,
                        database_type VARCHAR(50) NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES user (id)
                    )
                ''')
                
                conn.commit()
                conn.close()
                logger.info("Tables created successfully")
            
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'error')
                return render_template('register.html', title="Register")
            
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email already registered', 'error')
                return render_template('register.html', title="Register")
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            logger.info(f"Adding user to database: {username}")
            db.session.add(user)
            
            logger.info("Committing user to database")
            db.session.commit()
            
            logger.info(f"User {username} registered successfully")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            
            # Rollback any database changes
            try:
                db.session.rollback()
            except:
                pass
            
            # Try to reset database if it's a schema issue
            if "no such table" in str(e).lower() or "table" in str(e).lower():
                logger.info("Detected table issue, attempting database reset")
                if reset_database():
                    flash('Database was reset. Please try registration again.', 'info')
                else:
                    flash('Database error. Please try again later.', 'error')
            else:
                flash('An error occurred during registration. Please try again.', 'error')
            
            return render_template('register.html', title="Register")
    
    return render_template('register.html', title="Register")

@app.route('/logout')
def logout():
    flask_session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/connect', methods=['GET', 'POST'])
@login_required
def connect_page():
    if request.method == 'POST':
        db_uri = request.json.get('db_uri')
        connection_name = request.json.get('connection_name', 'Default Connection')
        
        if not db_uri:
            return jsonify({"error": "SQL Database URI is required."}), 400
        
        try:
            # Validate connection
            app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
            db.engine.dispose()
            
            with app.app_context():
                db.create_all()
                # Test connection
                db.session.execute(text("SELECT 1"))
                db.session.commit()
            
            # Save connection
            connection = DatabaseConnection(
                user_id=flask_session['user_id'],
                name=connection_name,
                connection_string=db_uri,
                database_type='sqlite' if 'sqlite' in db_uri else 'mysql' if 'mysql' in db_uri else 'postgresql'
            )
            db.session.add(connection)
            db.session.commit()
            
            return jsonify({"message": f"Connected to SQL database: {db_uri}"})
        except Exception as e:
            logger.error(f"Error connecting to SQL: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Get user's saved connections
    connections = DatabaseConnection.query.filter_by(user_id=flask_session.get('user_id')).all()
    return render_template('connect.html', title="Connect to Database", connections=connections)

@app.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_page():
    if request.method == 'POST':
        query = request.json.get('query')
        
        # Validate query
        is_safe, message = validate_sql_query(query)
        if not is_safe:
            return jsonify({"error": message}), 400
        
        start_time = datetime.now()
        try:
            with app.app_context():
                if query.strip().lower().startswith("select"):
                    result = db.session.execute(text(query))
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result]
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    log_query(query, 'select', execution_time, True)
                    
                    return jsonify({"data": rows})
                else:
                    db.session.execute(text(query))
                    db.session.commit()
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    log_query(query, 'modify', execution_time, True)
                    
                    return jsonify({"message": "Query executed successfully."})
        except Exception as e:
            db.session.rollback()
            execution_time = (datetime.now() - start_time).total_seconds()
            log_query(query, 'error', execution_time, False, str(e))
            return jsonify({"error": str(e)}), 500
    
    # Get query history - simplified to avoid complex queries
    try:
        user_id = flask_session.get('user_id')
        # Use a simple query to avoid complex SQLAlchemy operations
        history = db.session.query(QueryHistory).filter(QueryHistory.user_id == user_id).order_by(QueryHistory.created_at.desc()).limit(10).all()
    except Exception as e:
        logger.error(f"Error fetching query history: {e}")
        history = []
    
    return render_template('manage.html', title="Manage Data", history=history)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Validate file type
    allowed_extensions = {'csv', 'json', 'xlsx'}
    if not file.filename.lower().endswith(tuple(allowed_extensions)):
        return jsonify({"error": "File type not allowed"}), 400

    table_name = os.path.splitext(file.filename)[0].lower()
    table_name = ''.join(c if c.isalnum() else '_' for c in table_name)
    if table_name[0].isdigit():
        table_name = 'f_' + table_name

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        if request.form.get('file_type') == 'json':
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)

            def flatten_json(data):
                flattened = []
                for item in data:
                    flat_item = {}
                    for key, value in item.items():
                        if isinstance(value, dict):
                            for nested_key, nested_value in value.items():
                                if isinstance(nested_value, (str, int, float, bool)):
                                    flat_item[f"{key}_{nested_key}"] = nested_value
                        elif isinstance(value, list):
                            flat_item[key] = json.dumps(value)
                        else:
                            flat_item[key] = value
                    flattened.append(flat_item)
                return flattened

            flattened_data = flatten_json(data if isinstance(data, list) else [data])
            df = pd.DataFrame(flattened_data)
        elif file.filename.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        with app.app_context():
            inspector = db.inspect(db.engine)
            if table_name in inspector.get_table_names():
                db.session.execute(text(f'DROP TABLE IF EXISTS {table_name}'))
                db.session.commit()

        df.to_sql(table_name, db.engine, index=False, if_exists='replace')
        
        # Log the upload
        log_query(f"UPLOAD: {file.filename} -> {table_name}", 'upload', success=True)
        
        return jsonify({
            "message": f"File uploaded successfully as table '{table_name}'",
            "table_name": table_name,
            "columns": list(df.columns),
            "row_count": len(df)
        })
    except Exception as e:
        log_query(f"UPLOAD: {file.filename}", 'upload', success=False, error_message=str(e))
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/visualize', methods=['GET', 'POST'])
@login_required
def visualize_page():
    if request.method == 'GET':
        return render_template("visualize.html")
    
    try:
        query = request.json.get('query')
        x_axis = request.json.get('x_axis')
        y_axis = request.json.get('y_axis')
        chart_type = request.json.get('chart_type', 'bar')
        
        # Validate query
        is_safe, message = validate_sql_query(query)
        if not is_safe:
            return jsonify({"error": message}), 400
        
        with app.app_context():
            result = db.session.execute(text(query))
            rows = result.fetchall()
            if not rows:
                return jsonify({"error": "No data returned from query"}), 404

            df = pd.DataFrame(rows)
            df.columns = result.keys()

            plt.figure(figsize=(15, 8))
            plt.style.use('seaborn-v0_8')

            if df[x_axis].dtype == 'object':
                x_values = range(len(df[x_axis]))
                if chart_type == "scatter":
                    plt.scatter(x_values, df[y_axis], alpha=0.7, s=100)
                elif chart_type == "line":
                    plt.plot(x_values, df[y_axis], marker='o', linewidth=2, markersize=6)
                else:  # bar chart
                    bars = plt.bar(x_values, df[y_axis], alpha=0.8)
                    # Add value labels on bars
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height,
                                f'{height:.1f}', ha='center', va='bottom')
                plt.xticks(x_values, df[x_axis], rotation=45, ha='right')
            else:
                if chart_type == "scatter":
                    plt.scatter(df[x_axis], df[y_axis], alpha=0.7, s=100)
                elif chart_type == "line":
                    plt.plot(df[x_axis], df[y_axis], marker='o', linewidth=2, markersize=6)
                else:  # bar chart
                    bars = plt.bar(df[x_axis], df[y_axis], alpha=0.8)
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height,
                                f'{height:.1f}', ha='center', va='bottom')

            plt.xlabel(x_axis, fontsize=12, fontweight='bold')
            plt.ylabel(y_axis, fontsize=12, fontweight='bold')
            plt.title(f"{chart_type.capitalize()} Chart of {y_axis} vs {x_axis}", fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            plot_path = 'static/plot.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()

            return jsonify({
                "message": "Visualization created successfully",
                "plot_url": f"/{plot_path}"
            })
            
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report_page():
    if request.method == 'GET':
        return render_template("report.html", message="Submit data using the form below.")

    data = request.json.get('data')
    report_path = 'static/report.csv'
    try:
        df = pd.DataFrame(data)
        df.to_csv(report_path, index=False)
        return jsonify({"message": "Report generated.", "report_url": report_path})
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ai-suggest', methods=['POST'])
@login_required
def ai_suggest():
    query = request.json.get('query')
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    suggestion = get_hf_query_suggestion(query)
    return jsonify({"suggestion": suggestion})

@app.route('/history')
@login_required
def query_history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    try:
        user_id = flask_session.get('user_id')
        # Use a simple query to avoid complex SQLAlchemy operations
        history = db.session.query(QueryHistory).filter(QueryHistory.user_id == user_id).order_by(QueryHistory.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    except Exception as e:
        logger.error(f"Error fetching query history: {e}")
        history = None
    
    return render_template('history.html', title="Query History", history=history)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    try:
        user_id = flask_session.get('user_id')
        # Use simple queries to avoid complex SQLAlchemy operations
        total_queries = db.session.query(QueryHistory).filter(QueryHistory.user_id == user_id).count()
        successful_queries = db.session.query(QueryHistory).filter(QueryHistory.user_id == user_id, QueryHistory.success == True).count()
        recent_queries = db.session.query(QueryHistory).filter(QueryHistory.user_id == user_id).order_by(QueryHistory.created_at.desc()).limit(5).all()
        
        # Get database connections
        connections = db.session.query(DatabaseConnection).filter(DatabaseConnection.user_id == user_id).all()
        
        stats = {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
            'connections': len(connections),
            'recent_queries': recent_queries
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'success_rate': 0,
            'connections': 0,
            'recent_queries': []
        }
    
    return render_template('dashboard.html', title="Dashboard", stats=stats)

@app.route('/reset-db')
def reset_db():
    """Reset database - for debugging only"""
    try:
        if reset_database():
            return jsonify({"status": "success", "message": "Database reset successful"})
        else:
            return jsonify({"status": "error", "message": "Database reset failed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/test-registration')
def test_registration():
    """Test registration with a sample user"""
    try:
        # Test user creation
        test_user = User(username="test_user", email="test@example.com")
        test_user.set_password("test123")
        
        db.session.add(test_user)
        db.session.commit()
        
        # Clean up
        db.session.delete(test_user)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Registration test successful"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)})

@app.route('/create-tables')
def create_tables():
    """Manually create tables - for debugging"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        # Create tables manually
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT NOT NULL,
                query_type VARCHAR(50) NOT NULL,
                execution_time FLOAT,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS database_connection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name VARCHAR(100) NOT NULL,
                connection_string TEXT NOT NULL,
                database_type VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "Tables created successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/test-db')
def test_db():
    """Test database functionality and create tables if needed"""
    try:
        # Test if we can write to the database
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        # Check if user table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print("User table doesn't exist, creating tables...")
            
            # Create tables manually
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    query TEXT NOT NULL,
                    query_type VARCHAR(50) NOT NULL,
                    execution_time FLOAT,
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS database_connection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name VARCHAR(100) NOT NULL,
                    connection_string TEXT NOT NULL,
                    database_type VARCHAR(50) NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            ''')

            conn.commit()
            print("Tables created successfully")
        
        # Test if we can read from the database
        cursor = conn.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "Database is working correctly",
            "database_path": db_path,
            "user_count": user_count,
            "tables_exist": True
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "database_path": db_path
        })

@app.route('/check-users')
def check_users():
    """Check if users exist in database - for debugging"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        # Check if user table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            return jsonify({"status": "error", "message": "User table does not exist"})
        
        # Get all users
        cursor = conn.execute("SELECT id, username, email, created_at FROM user")
        users = cursor.fetchall()
        
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "created_at": user[3]
            })
        
        return jsonify({
            "status": "success",
            "user_count": len(user_list),
            "users": user_list
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/session-test')
def session_test():
    """Test session functionality"""
    try:
        # Test session write
        flask_session['test_key'] = 'test_value'
        
        # Test session read
        test_value = flask_session.get('test_key')
        
        # Clean up
        flask_session.pop('test_key', None)
        
        if test_value == 'test_value':
            return jsonify({
                "status": "success",
                "message": "Session is working correctly",
                "session_id": flask_session.get('_id', 'No session ID')
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Session read/write test failed"
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/session-debug')
def session_debug():
    """Debug session functionality"""
    try:
        # Get current session data
        session_data = dict(flask_session)
        
        return jsonify({
            "status": "success",
            "session_data": session_data,
            "user_id_in_session": flask_session.get('user_id'),
            "username_in_session": flask_session.get('username'),
            "session_id": flask_session.get('_id', 'No session ID')
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/login-test')
def login_test():
    """Test login functionality"""
    try:
        # Test if user exists
        user = User.query.filter_by(username='testuser5').first()
        
        if user:
            # Test password check
            password_check = user.check_password('test123')
            
            return jsonify({
                "status": "success",
                "user_exists": True,
                "username": user.username,
                "email": user.email,
                "password_check": password_check,
                "user_id": user.id
            })
        else:
            return jsonify({
                "status": "error",
                "message": "User testuser5 not found",
                "user_exists": False
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/auth-test')
@login_required
def auth_test():
    """Test authentication - if you can see this, you're logged in"""
    user_id = flask_session.get('user_id')
    username = flask_session.get('username')
    
    return jsonify({
        "status": "success",
        "message": "Authentication working",
        "user_id": user_id,
        "username": username
    })

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"500 error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize database on startup
    print("Starting ChatDB application...")
    print(f"Database path: {db_path}")
    init_database()
    print("Database initialization complete")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
