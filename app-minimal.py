from flask import Flask, render_template, jsonify, request, session as flask_session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
import logging
import re
import json
import csv
from datetime import datetime
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Ensure the data/ directory exists
if not os.path.exists("data"):
    os.makedirs("data")

# Configure the SQLite database
db_path = os.path.abspath("data/example.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
db = SQLAlchemy(app)

# Setup SQLAlchemy session
with app.app_context():
    engine = db.engine
    SQLAlchemySession = sessionmaker(bind=engine)
    sqlalchemy_session = SQLAlchemySession()

# Flask session for storing query results
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.config['SESSION_TYPE'] = 'filesystem'

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_sql_query(query):
    """Basic SQL injection protection"""
    # Remove comments
    query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    
    # Check for dangerous keywords (basic protection)
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
    query_upper = query.upper()
    
    for keyword in dangerous_keywords:
        if keyword in query_upper and not query_upper.strip().startswith('SELECT'):
            raise ValueError(f"Operation '{keyword}' is not allowed for security reasons")
    
    return query.strip()

# Define Models
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
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    result_count = db.Column(db.Integer)
    status = db.Column(db.String(20))  # success, error

@app.route('/')
def index():
    return render_template('index.html', title="Home")

@app.route('/connect', methods=['GET', 'POST'])
def connect_page():
    if request.method == 'POST':
        db_uri = request.json.get('db_uri')
        if not db_uri:
            return jsonify({"error": "SQL Database URI is required."}), 400
        
        # Validate URI format
        if not db_uri.startswith(('sqlite://', 'mysql://', 'postgresql://')):
            return jsonify({"error": "Invalid database URI format. Supported: sqlite://, mysql://, postgresql://"}), 400
        
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
            db.engine.dispose()  # Close existing connections
            with app.app_context():
                db.create_all()
                # Test the connection
                db.session.execute(text("SELECT 1"))
                db.session.commit()
            return jsonify({"message": f"Successfully connected to database: {db_uri}"})
        except Exception as e:
            logger.error(f"Error connecting to SQL: {e}")
            return jsonify({"error": f"Connection failed: {str(e)}"}), 500
    return render_template('connect.html', title="Connect to Database")

@app.route('/manage', methods=['GET', 'POST'])
def manage_page():
    if request.method == 'POST':
        query = request.json.get('query')
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        try:
            # Sanitize the query
            sanitized_query = sanitize_sql_query(query)
            
            with app.app_context():
                # Execute the query using SQLAlchemy session
                if sanitized_query.strip().lower().startswith("select"):
                    result = db.session.execute(text(sanitized_query))
                    # Convert results to list of dicts
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result]
                    
                    # Save to query history
                    history_entry = QueryHistory(
                        query=sanitized_query,
                        result_count=len(rows),
                        status='success'
                    )
                    db.session.add(history_entry)
                    db.session.commit()
                    
                    return jsonify({
                        "data": rows,
                        "count": len(rows),
                        "columns": list(columns)
                    })
                else:
                    db.session.execute(text(sanitized_query))
                    db.session.commit()
                    
                    # Save to query history
                    history_entry = QueryHistory(
                        query=sanitized_query,
                        result_count=0,
                        status='success'
                    )
                    db.session.add(history_entry)
                    db.session.commit()
                    
                    return jsonify({"message": "Query executed successfully."})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error: {e}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error: {e}")
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    return render_template('manage.html', title="Manage Data")

@app.route('/upload', methods=['POST'])
def upload_file():
    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Please upload CSV or JSON files."}), 400

    # Secure the filename
    filename = secure_filename(file.filename)
    table_name = os.path.splitext(filename)[0].lower()
    table_name = ''.join(c if c.isalnum() else '_' for c in table_name)
    if table_name[0].isdigit():
        table_name = 'f_' + table_name

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        if filename.endswith('.json'):
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
            
            # Create table manually since we don't have pandas
            if flattened_data:
                columns = list(flattened_data[0].keys())
                create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
                create_table_sql += ", ".join([f"{col} TEXT" for col in columns])
                create_table_sql += ")"
                
                with app.app_context():
                    db.session.execute(text(create_table_sql))
                    db.session.commit()
                    
                    # Insert data
                    for row in flattened_data:
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
                        db.session.execute(text(insert_sql), list(row.values()))
                    db.session.commit()
            
            return jsonify({
                "message": f"File uploaded successfully as table '{table_name}'",
                "table_name": table_name,
                "columns": columns if flattened_data else [],
                "rows": len(flattened_data)
            })
        else:
            # Handle CSV files
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            if rows:
                columns = list(rows[0].keys())
                create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
                create_table_sql += ", ".join([f"{col} TEXT" for col in columns])
                create_table_sql += ")"
                
                with app.app_context():
                    db.session.execute(text(create_table_sql))
                    db.session.commit()
                    
                    # Insert data
                    for row in rows:
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
                        db.session.execute(text(insert_sql), list(row.values()))
                    db.session.commit()
                
                return jsonify({
                    "message": f"File uploaded successfully as table '{table_name}'",
                    "table_name": table_name,
                    "columns": columns,
                    "rows": len(rows)
                })
            else:
                return jsonify({"error": "No data found in CSV file"}), 400
                
    except Exception as e:
        logger.error(f"File processing error: {e}")
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/visualize', methods=['GET', 'POST'])
def visualize_page():
    if request.method == 'GET':
        return render_template("visualize.html")
    
    try:
        query = request.json.get('query')
        x_axis = request.json.get('x_axis')
        y_axis = request.json.get('y_axis')
        chart_type = request.json.get('chart_type', 'bar')
        
        if not all([query, x_axis, y_axis]):
            return jsonify({"error": "Query, X-axis, and Y-axis are required"}), 400
        
        # Sanitize the query
        sanitized_query = sanitize_sql_query(query)
        
        with app.app_context():
            result = db.session.execute(text(sanitized_query))
            rows = result.fetchall()
            if not rows:
                return jsonify({"error": "No data returned from query"}), 404

            # Convert to list of dicts
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in result]

            # Validate columns exist
            if x_axis not in columns or y_axis not in columns:
                return jsonify({"error": "Specified columns not found in query results"}), 400

            # Return data for client-side visualization
            return jsonify({
                "message": "Data prepared for visualization",
                "data": data,
                "x_axis": x_axis,
                "y_axis": y_axis,
                "chart_type": chart_type,
                "data_points": len(data)
            })
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        return jsonify({"error": f"Visualization error: {str(e)}"}), 500

@app.route('/report', methods=['GET', 'POST'])
def report_page():
    if request.method == 'GET':
        return render_template("report.html", message="Submit data using the form below.")

    data = request.json.get('data')
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    report_path = 'static/report.csv'
    try:
        if data and len(data) > 0:
            columns = list(data[0].keys())
            
            with open(report_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(data)
            
            return jsonify({
                "message": "Report generated successfully.",
                "report_url": report_path,
                "rows": len(data),
                "columns": columns
            })
        else:
            return jsonify({"error": "No data to write"}), 400
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({"error": f"Report generation error: {str(e)}"}), 500

@app.route('/history')
def query_history():
    """Get query history"""
    try:
        with app.app_context():
            history = QueryHistory.query.order_by(QueryHistory.timestamp.desc()).limit(20).all()
            return jsonify({
                "history": [
                    {
                        "id": h.id,
                        "query": h.query,
                        "timestamp": h.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "result_count": h.result_count,
                        "status": h.status
                    } for h in history
                ]
            })
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tables')
def get_tables():
    """Get list of available tables"""
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            return jsonify({"tables": tables})
    except Exception as e:
        logger.error(f"Error fetching tables: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/table/<table_name>')
def get_table_info(table_name):
    """Get table structure and sample data"""
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            if table_name not in inspector.get_table_names():
                return jsonify({"error": "Table not found"}), 404
            
            columns = inspector.get_columns(table_name)
            sample_query = f"SELECT * FROM {table_name} LIMIT 5"
            result = db.session.execute(text(sample_query))
            sample_data = [dict(zip(result.keys(), row)) for row in result]
            
            return jsonify({
                "table_name": table_name,
                "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns],
                "sample_data": sample_data
            })
    except Exception as e:
        logger.error(f"Error fetching table info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Initialize database tables
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 