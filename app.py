from flask import Flask, render_template, jsonify, request, session as flask_session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os
import openai
import logging
import matplotlib
import matplotlib.pyplot as plt
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
db = SQLAlchemy(app)

# Setup SQLAlchemy session
with app.app_context():
    engine = db.engine
    SQLAlchemySession = sessionmaker(bind=engine)
    sqlalchemy_session = SQLAlchemySession()

# Flask session for storing query results
app.secret_key = "supersecretkey"
app.config['SESSION_TYPE'] = 'filesystem'

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a Sample Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"<User {self.name}>"

@app.route('/')
def index():
    return render_template('index.html', title="Home")

@app.route('/connect', methods=['GET', 'POST'])
def connect_page():
    if request.method == 'POST':
        db_uri = request.json.get('db_uri')
        if not db_uri:
            return jsonify({"error": "SQL Database URI is required."}), 400
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
            db.engine.dispose()  # Close existing connections
            with app.app_context():
                db.create_all()
            return jsonify({"message": f"Connected to SQL database: {db_uri}"})
        except Exception as e:
            logger.error(f"Error connecting to SQL: {e}")
            return jsonify({"error": str(e)}), 500
    return render_template('connect.html', title="Connect to Database")

@app.route('/manage', methods=['GET', 'POST'])
def manage_page():
    if request.method == 'POST':
        query = request.json.get('query')
        try:
            with app.app_context():
                # Execute the query using SQLAlchemy session
                if query.strip().lower().startswith("select"):
                    result = db.session.execute(text(query))
                    # Convert results to list of dicts
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result]
                    return jsonify({"data": rows})
                else:
                    db.session.execute(text(query))
                    db.session.commit()
                    return jsonify({"message": "Query executed successfully."})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    return render_template('manage.html', title="Manage Data")

@app.route('/upload', methods=['POST'])
def upload_file():
    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

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
            "columns": list(df.columns)
        })
    except Exception as e:
        return jsonify({"message": f"Error processing file: {str(e)}"}), 500
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
        
        with app.app_context():
            result = db.session.execute(text(query))
            rows = result.fetchall()
            if not rows:
                return jsonify({"error": "No data returned from query"}), 404

            df = pd.DataFrame(rows)
            df.columns = result.keys()

            plt.figure(figsize=(15, 8))

            if df[x_axis].dtype == 'object':
                x_values = range(len(df[x_axis]))
                if chart_type == "scatter":
                    plt.scatter(x_values, df[y_axis])
                elif chart_type == "line":
                    plt.plot(x_values, df[y_axis])
                else:  # bar chart
                    plt.bar(x_values, df[y_axis])
                plt.xticks(x_values, df[x_axis], rotation=45, ha='right')
            else:
                if chart_type == "scatter":
                    plt.scatter(df[x_axis], df[y_axis])
                elif chart_type == "line":
                    plt.plot(df[x_axis], df[y_axis])
                else:  # bar chart
                    plt.bar(df[x_axis], df[y_axis])

            plt.xlabel(x_axis)
            plt.ylabel(y_axis)
            plt.title(f"{chart_type.capitalize()} Chart of {y_axis} vs {x_axis}")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            plot_path = 'static/plot.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()

            return jsonify({
                "message": "Visualization created successfully",
                "plot_url": f"/{plot_path}"
            })
            
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/report', methods=['GET', 'POST'])
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Optional: Initializes your database
    port = int(os.environ.get('PORT', 5000))  # Heroku provides the PORT environment variable
    app.run(host='0.0.0.0', port=port)
