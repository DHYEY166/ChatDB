from flask import Flask, render_template, jsonify, request, session as flask_session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
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
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Ensure the data/ directory exists
if not os.path.exists("data"):
    os.makedirs("data")

# Configure the SQLite database
db_path = os.path.abspath("data/example.db")
print(f"Database Path: {db_path}")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup SQLAlchemy session
with app.app_context():
    engine = db.engine
    SQLAlchemySession = sessionmaker(bind=engine)
    sqlalchemy_session = SQLAlchemySession()

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
        if 'user_id' not in flask_session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
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
        with app.app_context():
            db.create_all()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Try to create database file manually
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.close()
            logger.info("Database file created manually")
        except Exception as e2:
            logger.error(f"Manual database creation failed: {e2}")

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
            
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                flask_session['user_id'] = user.id
                flask_session['username'] = user.username
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html', title="Login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
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
            
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return render_template('register.html', title="Register")
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return render_template('register.html', title="Register")
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            db.session.rollback()
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
    
    # Get query history
    history = QueryHistory.query.filter_by(user_id=flask_session.get('user_id')).order_by(QueryHistory.created_at.desc()).limit(10).all()
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
    
    history = QueryHistory.query.filter_by(user_id=flask_session.get('user_id'))\
        .order_by(QueryHistory.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('history.html', title="Query History", history=history)

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    total_queries = QueryHistory.query.filter_by(user_id=flask_session.get('user_id')).count()
    successful_queries = QueryHistory.query.filter_by(user_id=flask_session.get('user_id'), success=True).count()
    recent_queries = QueryHistory.query.filter_by(user_id=flask_session.get('user_id'))\
        .order_by(QueryHistory.created_at.desc()).limit(5).all()
    
    # Get database connections
    connections = DatabaseConnection.query.filter_by(user_id=flask_session.get('user_id')).all()
    
    stats = {
        'total_queries': total_queries,
        'successful_queries': successful_queries,
        'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
        'connections': len(connections),
        'recent_queries': recent_queries
    }
    
    return render_template('dashboard.html', title="Dashboard", stats=stats)

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
    init_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
