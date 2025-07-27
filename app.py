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
import secrets
import re
from werkzeug.utils import secure_filename
from datetime import datetime
import json
matplotlib.use('Agg')

# Initialize Flask app
app = Flask(__name__)

# Security: Generate a secure secret key
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Ensure the data/ directory exists
if not os.path.exists("data"):
    os.makedirs("data")

# Configure the SQLite database
db_path = os.path.abspath("data/example.db")
print(f"Database Path: {db_path}")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
db = SQLAlchemy(app)

# Setup SQLAlchemy session
with app.app_context():
    engine = db.engine
    SQLAlchemySession = sessionmaker(bind=engine)
    sqlalchemy_session = SQLAlchemySession()

# Flask session configuration
app.config['SESSION_TYPE'] = 'filesystem'

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_sql_query(query):
    """Basic SQL injection prevention"""
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
    query_upper = query.upper().strip()
    
    # Check for dangerous keywords in non-SELECT queries
    if not query_upper.startswith('SELECT'):
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False, f"Potentially dangerous SQL keyword '{keyword}' detected"
    
    return True, "Query is safe"

def sanitize_table_name(name):
    """Sanitize table name to prevent SQL injection"""
    # Remove any non-alphanumeric characters except underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = 'tbl_' + sanitized
    return sanitized or 'table'

# Define a Sample Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.name}>"

@app.route('/')
def index():
    """Homepage with improved layout"""
    return render_template('index.html', title="ChatDB - Database Management Tool")

@app.route('/connect', methods=['GET', 'POST'])
def connect_page():
    """Database connection page with improved error handling"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            db_uri = data.get('db_uri', '').strip()
            if not db_uri:
                return jsonify({"error": "Database URI is required"}), 400
            
            # Basic URI validation
            if not (db_uri.startswith('sqlite://') or 
                   db_uri.startswith('mysql://') or 
                   db_uri.startswith('postgresql://')):
                return jsonify({"error": "Invalid database URI format"}), 400
            
            # Test connection
            try:
                app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
                db.engine.dispose()  # Close existing connections
                with app.app_context():
                    db.create_all()
                    # Test the connection
                    db.session.execute(text("SELECT 1"))
                    db.session.commit()
                
                return jsonify({
                    "message": f"Successfully connected to database",
                    "uri": db_uri
                })
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                return jsonify({"error": f"Failed to connect to database: {str(e)}"}), 500
                
        except Exception as e:
            logger.error(f"Connect page error: {e}")
            return jsonify({"error": "An unexpected error occurred"}), 500
    
    return render_template('connect.html', title="Connect to Database")

@app.route('/manage', methods=['GET', 'POST'])
def manage_page():
    """Data management page with improved security"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            query = data.get('query', '').strip()
            if not query:
                return jsonify({"error": "Query is required"}), 400
            
            # Validate query
            is_safe, message = validate_sql_query(query)
            if not is_safe:
                return jsonify({"error": message}), 400
            
            with app.app_context():
                try:
                    if query.strip().lower().startswith("select"):
                        result = db.session.execute(text(query))
                        columns = result.keys()
                        rows = [dict(zip(columns, row)) for row in result]
                        return jsonify({
                            "data": rows,
                            "row_count": len(rows),
                            "column_count": len(columns) if rows else 0
                        })
                    else:
                        # For non-SELECT queries, limit to safe operations
                        if any(keyword in query.upper() for keyword in ['DROP', 'DELETE', 'TRUNCATE']):
                            return jsonify({"error": "Destructive operations are not allowed"}), 400
                        
                        result = db.session.execute(text(query))
                        db.session.commit()
                        return jsonify({
                            "message": "Query executed successfully",
                            "affected_rows": result.rowcount if hasattr(result, 'rowcount') else 0
                        })
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Query execution error: {e}")
                    return jsonify({"error": f"Query execution failed: {str(e)}"}), 500
                    
        except Exception as e:
            logger.error(f"Manage page error: {e}")
            return jsonify({"error": "An unexpected error occurred"}), 500
    
    return render_template('manage.html', title="Manage Data")

@app.route('/upload', methods=['POST'])
def upload_file():
    """File upload with improved security and validation"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed. Please upload CSV, JSON, or Excel files"}), 400

        # Secure filename
        filename = secure_filename(file.filename)
        file_type = request.form.get('file_type', 'csv').lower()
        
        # Create upload directory
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        try:
            # Process file based on type
            if file_type == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                def flatten_json(data):
                    """Flatten nested JSON structures"""
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
            elif file_type in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:  # CSV
                df = pd.read_csv(file_path)

            # Generate safe table name
            table_name = sanitize_table_name(os.path.splitext(filename)[0].lower())

            with app.app_context():
                # Check if table exists and drop if needed
                inspector = db.inspect(db.engine)
                if table_name in inspector.get_table_names():
                    db.session.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
                    db.session.commit()

            # Save to database
            df.to_sql(table_name, db.engine, index=False, if_exists='replace')
            
            return jsonify({
                "message": f"File uploaded successfully as table '{table_name}'",
                "table_name": table_name,
                "columns": list(df.columns),
                "row_count": len(df),
                "file_size": os.path.getsize(file_path)
            })
            
        except Exception as e:
            logger.error(f"File processing error: {e}")
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": "An unexpected error occurred during upload"}), 500

@app.route('/visualize', methods=['GET', 'POST'])
def visualize_page():
    """Data visualization with improved error handling"""
    if request.method == 'GET':
        return render_template("visualize.html", title="Data Visualization")
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        query = data.get('query', '').strip()
        x_axis = data.get('x_axis', '').strip()
        y_axis = data.get('y_axis', '').strip()
        chart_type = data.get('chart_type', 'bar').lower()
        
        if not query or not x_axis or not y_axis:
            return jsonify({"error": "Query, X-axis, and Y-axis are required"}), 400
        
        # Validate query
        is_safe, message = validate_sql_query(query)
        if not is_safe:
            return jsonify({"error": message}), 400
        
        # Validate chart type
        valid_chart_types = ['bar', 'line', 'scatter', 'pie']
        if chart_type not in valid_chart_types:
            return jsonify({"error": f"Invalid chart type. Must be one of: {', '.join(valid_chart_types)}"}), 400
        
        with app.app_context():
            try:
                result = db.session.execute(text(query))
                rows = result.fetchall()
                if not rows:
                    return jsonify({"error": "No data returned from query"}), 404

                df = pd.DataFrame(rows)
                df.columns = result.keys()

                # Validate columns exist
                if x_axis not in df.columns or y_axis not in df.columns:
                    return jsonify({"error": "Specified columns not found in query results"}), 400

                # Create visualization
                plt.figure(figsize=(12, 8))
                plt.style.use('default')  # Use default style for better appearance

                if chart_type == "pie":
                    plt.pie(df[y_axis], labels=df[x_axis], autopct='%1.1f%%')
                    plt.title(f"Pie Chart: {y_axis} by {x_axis}")
                else:
                    if df[x_axis].dtype == 'object':
                        x_values = range(len(df[x_axis]))
                        if chart_type == "scatter":
                            plt.scatter(x_values, df[y_axis], alpha=0.7)
                        elif chart_type == "line":
                            plt.plot(x_values, df[y_axis], marker='o')
                        else:  # bar chart
                            plt.bar(x_values, df[y_axis], alpha=0.8)
                        plt.xticks(x_values, df[x_axis], rotation=45, ha='right')
                    else:
                        if chart_type == "scatter":
                            plt.scatter(df[x_axis], df[y_axis], alpha=0.7)
                        elif chart_type == "line":
                            plt.plot(df[x_axis], df[y_axis], marker='o')
                        else:  # bar chart
                            plt.bar(df[x_axis], df[y_axis], alpha=0.8)

                    plt.xlabel(x_axis)
                    plt.ylabel(y_axis)
                    plt.title(f"{chart_type.capitalize()} Chart: {y_axis} vs {x_axis}")

                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                # Save plot with timestamp to avoid caching issues
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                plot_filename = f'plot_{timestamp}.png'
                plot_path = os.path.join('static', plot_filename)
                plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
                plt.close()

                return jsonify({
                    "message": "Visualization created successfully",
                    "plot_url": f"/static/{plot_filename}",
                    "data_points": len(df)
                })
                
            except Exception as e:
                logger.error(f"Visualization error: {e}")
                return jsonify({"error": f"Error creating visualization: {str(e)}"}), 500
                
    except Exception as e:
        logger.error(f"Visualize page error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/report', methods=['GET', 'POST'])
def report_page():
    """Report generation with improved validation"""
    if request.method == 'GET':
        return render_template("report.html", title="Generate Reports")

    try:
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"error": "No data provided"}), 400
        
        input_data = data['data']
        
        # Validate input data
        if not isinstance(input_data, list):
            return jsonify({"error": "Data must be a list of objects"}), 400
        
        if not input_data:
            return jsonify({"error": "Data list cannot be empty"}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(input_data)
        
        # Generate report with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f'report_{timestamp}.csv'
        report_path = os.path.join('static', report_filename)
        
        df.to_csv(report_path, index=False)
        
        return jsonify({
            "message": "Report generated successfully",
            "report_url": f"/static/{report_filename}",
            "row_count": len(df),
            "column_count": len(df.columns)
        })
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({"error": f"Error generating report: {str(e)}"}), 500

@app.errorhandler(404)
def not_found_error(error):
    """Custom 404 error handler"""
    return render_template('404.html', title="Page Not Found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 error handler"""
    db.session.rollback()
    return render_template('500.html', title="Server Error"), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
