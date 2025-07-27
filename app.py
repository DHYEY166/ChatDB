from flask import Flask, render_template, jsonify, request, session as flask_session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os
import openai
import logging
import matplotlib
import matplotlib.pyplot as plt
import re
import json
from werkzeug.utils import secure_filename
from functools import wraps
import hashlib
import time
from datetime import datetime
matplotlib.use('Agg')

# Initialize Flask app
app = Flask(__name__)

# Ensure the data/ directory exists
if not os.path.exists("data"):
    os.makedirs("data")

# Configure the SQLite database
db_path = os.path.abspath("data/example.db")
print(f"Database Path: {db_path}")  # Debugging the database path
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)

# Setup SQLAlchemy session
with app.app_context():
    engine = db.engine
    SQLAlchemySession = sessionmaker(bind=engine)
    sqlalchemy_session = SQLAlchemySession()

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security: SQL injection prevention
def sanitize_sql_query(query):
    """Basic SQL injection prevention"""
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
    query_upper = query.upper()
    
    # Check for dangerous operations
    for keyword in dangerous_keywords:
        if keyword in query_upper and not query_upper.strip().startswith('SELECT'):
            raise ValueError(f"Operation {keyword} is not allowed for security reasons")
    
    return query

# Rate limiting decorator
def rate_limit(max_requests=10, window=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            if 'rate_limit' not in flask_session:
                flask_session['rate_limit'] = {}
            
            if client_ip not in flask_session['rate_limit']:
                flask_session['rate_limit'][client_ip] = {'count': 0, 'reset_time': current_time + window}
            
            if current_time > flask_session['rate_limit'][client_ip]['reset_time']:
                flask_session['rate_limit'][client_ip] = {'count': 0, 'reset_time': current_time + window}
            
            if flask_session['rate_limit'][client_ip]['count'] >= max_requests:
                return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
            
            flask_session['rate_limit'][client_ip]['count'] += 1
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Define a Sample Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.name}>"

class QueryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)

@app.route('/')
def index():
    return render_template('index.html', title="Home")

@app.route('/connect', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=60)
def connect_page():
    if request.method == 'POST':
        db_uri = request.json.get('db_uri')
        if not db_uri:
            return jsonify({"error": "SQL Database URI is required."}), 400
        
        # Validate URI format
        if not re.match(r'^[a-zA-Z]+://', db_uri):
            return jsonify({"error": "Invalid database URI format."}), 400
        
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
            db.engine.dispose()  # Close existing connections
            with app.app_context():
                db.create_all()
            flask_session['current_db_uri'] = db_uri
            return jsonify({"message": f"Connected to SQL database: {db_uri}"})
        except Exception as e:
            logger.error(f"Error connecting to SQL: {e}")
            return jsonify({"error": f"Connection failed: {str(e)}"}), 500
    return render_template('connect.html', title="Connect to Database")

@app.route('/manage', methods=['GET', 'POST'])
@rate_limit(max_requests=20, window=60)
def manage_page():
    if request.method == 'POST':
        query = request.json.get('query')
        if not query:
            return jsonify({"error": "Query is required."}), 400
        
        try:
            # Sanitize query
            sanitized_query = sanitize_sql_query(query)
            
            with app.app_context():
                # Log query for history
                query_history = QueryHistory(query=sanitized_query)
                db.session.add(query_history)
                
                # Execute the query using SQLAlchemy session
                if sanitized_query.strip().lower().startswith("select"):
                    result = db.session.execute(text(sanitized_query))
                    # Convert results to list of dicts
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result]
                    
                    query_history.success = True
                    db.session.commit()
                    
                    return jsonify({
                        "data": rows,
                        "row_count": len(rows),
                        "columns": list(columns)
                    })
                else:
                    db.session.execute(text(sanitized_query))
                    db.session.commit()
                    
                    query_history.success = True
                    db.session.commit()
                    
                    return jsonify({"message": "Query executed successfully."})
        except ValueError as e:
            query_history.success = False
            query_history.error_message = str(e)
            db.session.commit()
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            if 'query_history' in locals():
                query_history.success = False
                query_history.error_message = str(e)
                db.session.commit()
            db.session.rollback()
            logger.error(f"Query execution error: {e}")
            return jsonify({"error": f"Query execution failed: {str(e)}"}), 500
    return render_template('manage.html', title="Manage Data")

@app.route('/upload', methods=['POST'])
@rate_limit(max_requests=5, window=60)
def upload_file():
    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Validate file type
    allowed_extensions = {'csv', 'json'}
    file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_extension not in allowed_extensions:
        return jsonify({"error": "Only CSV and JSON files are allowed"}), 400

    # Secure filename
    filename = secure_filename(file.filename)
    table_name = os.path.splitext(filename)[0].lower()
    table_name = ''.join(c if c.isalnum() else '_' for c in table_name)
    if table_name[0].isdigit():
        table_name = 'f_' + table_name

    file_path = os.path.join(UPLOAD_FOLDER, filename)
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
                            # Extract important fields from nested dict
                            for nested_key, nested_value in value.items():
                                if isinstance(nested_value, (str, int, float, bool)):
                                    flat_item[f"{key}_{nested_key}"] = nested_value
                        elif isinstance(value, list):
                            # Convert lists to string representation
                            flat_item[key] = json.dumps(value)
                        else:
                            flat_item[key] = value
                    flattened.append(flat_item)
                return flattened

            flattened_data = flatten_json(data if isinstance(data, list) else [data])
            df = pd.DataFrame(flattened_data)
        else:
            df = pd.read_csv(file_path)

        with app.app_context():
            inspector = db.inspect(db.engine)
            if table_name in inspector.get_table_names():
                db.session.execute(text(f'DROP TABLE IF EXISTS {table_name}'))
                db.session.commit()

        df.to_sql(table_name, db.engine, index=False, if_exists='replace')
        
        return jsonify({
            "message": f"File uploaded successfully as table '{table_name}'",
            "table_name": table_name,
            "columns": list(df.columns),
            "row_count": len(df)
        })
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/visualize', methods=['GET', 'POST'])
@rate_limit(max_requests=10, window=60)
def visualize_page():
    if request.method == 'GET':
        return render_template("visualize.html")
    
    try:
        query = request.json.get('query')
        x_axis = request.json.get('x_axis')
        y_axis = request.json.get('y_axis')
        chart_type = request.json.get('chart_type', 'bar')
        
        if not all([query, x_axis, y_axis]):
            return jsonify({"error": "Query, x_axis, and y_axis are required"}), 400
        
        # Sanitize query
        sanitized_query = sanitize_sql_query(query)
        
        with app.app_context():
            result = db.session.execute(text(sanitized_query))
            rows = result.fetchall()
            if not rows:
                return jsonify({"error": "No data returned from query"}), 404

            df = pd.DataFrame(rows)
            df.columns = result.keys()
            
            # Validate columns exist
            if x_axis not in df.columns or y_axis not in df.columns:
                return jsonify({"error": f"Columns {x_axis} or {y_axis} not found in query results"}), 400

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
                    # Add value labels on bars
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height,
                                f'{height:.1f}', ha='center', va='bottom')

            plt.xlabel(x_axis, fontsize=12, fontweight='bold')
            plt.ylabel(y_axis, fontsize=12, fontweight='bold')
            plt.title(f"{chart_type.capitalize()} Chart of {y_axis} vs {x_axis}", 
                     fontsize=14, fontweight='bold', pad=20)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            plot_path = 'static/plot.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()

            return jsonify({
                "message": "Visualization created successfully",
                "plot_url": f"/{plot_path}",
                "data_points": len(df)
            })
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        return jsonify({"error": f"Visualization failed: {str(e)}"}), 500

@app.route('/report', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=60)
def report_page():
    if request.method == 'GET':
        return render_template("report.html", message="Submit data using the form below.")

    data = request.json.get('data')
    if not data:
        return jsonify({"error": "Data is required"}), 400
    
    try:
        df = pd.DataFrame(data)
        report_path = 'static/report.csv'
        df.to_csv(report_path, index=False)
        
        return jsonify({
            "message": "Report generated successfully.",
            "report_url": report_path,
            "row_count": len(df),
            "column_count": len(df.columns)
        })
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({"error": f"Report generation failed: {str(e)}"}), 500

@app.route('/api/suggest-query', methods=['POST'])
@rate_limit(max_requests=5, window=60)
def suggest_query():
    """AI-powered query suggestions"""
    if not openai.api_key:
        return jsonify({"error": "OpenAI API key not configured"}), 500
    
    try:
        data = request.json
        table_info = data.get('table_info', '')
        user_intent = data.get('intent', '')
        
        prompt = f"""
        Given the following table information:
        {table_info}
        
        User intent: {user_intent}
        
        Generate a SQL query that matches the user's intent. 
        Only return the SQL query, nothing else.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        
        suggested_query = response.choices[0].message.content.strip()
        return jsonify({"suggested_query": suggested_query})
        
    except Exception as e:
        logger.error(f"Query suggestion error: {e}")
        return jsonify({"error": "Failed to generate query suggestion"}), 500

@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get list of available tables"""
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            table_info = []
            for table in tables:
                columns = inspector.get_columns(table)
                table_info.append({
                    "name": table,
                    "columns": [col['name'] for col in columns]
                })
            
            return jsonify({"tables": table_info})
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return jsonify({"error": "Failed to get table information"}), 500

@app.route('/api/query-history', methods=['GET'])
def get_query_history():
    """Get recent query history"""
    try:
        with app.app_context():
            recent_queries = QueryHistory.query.order_by(QueryHistory.executed_at.desc()).limit(10).all()
            
            history = []
            for query in recent_queries:
                history.append({
                    "query": query.query,
                    "executed_at": query.executed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "success": query.success,
                    "error_message": query.error_message
                })
            
            return jsonify({"history": history})
    except Exception as e:
        logger.error(f"Error getting query history: {e}")
        return jsonify({"error": "Failed to get query history"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Optional: Initializes your database
    port = int(os.environ.get('PORT', 5000))  # Heroku provides the PORT environment variable
    app.run(host='0.0.0.0', port=port)
