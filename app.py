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
import sqlite3
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
            # Execute the query using SQLAlchemy session
            if query.strip().lower().startswith("select"):
                result = sqlalchemy_session.execute(text(query)).fetchall()
                # Convert rows to dictionaries
                data = [dict(row._mapping) for row in result]
                # Save query results in Flask session
                flask_session['query_results'] = data
                return jsonify({"data": data})
            else:
                sqlalchemy_session.execute(text(query))
                sqlalchemy_session.commit()
                return jsonify({"message": "Query executed successfully."})
        except Exception as e:
            logger.error(f"SQL query error: {e}")
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

    file_type = request.form.get('file_type')
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        if file_type == 'csv':
            df = pd.read_csv(file_path)
        elif file_type == 'json':
            df = pd.read_json(file_path)
        else:
            return jsonify({"message": "Unsupported file type"}), 400

        # Insert data into SQLite using dynamic column mapping
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for record in df.to_dict(orient='records'):
            columns = ", ".join(record.keys())
            placeholders = ", ".join("?" * len(record))
            sql = f"INSERT INTO uploaded_data ({columns}) VALUES ({placeholders})"

            try:
                cursor.execute(sql, tuple(record.values()))
            except sqlite3.OperationalError as e:
                logger.error(f"Error inserting record: {e}")

        conn.commit()
        conn.close()

        return jsonify({"message": "File uploaded and data inserted successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error processing file: {e}"}), 500
    finally:
        os.remove(file_path)

@app.route('/visualize', methods=['GET', 'POST'])
def visualize_page():
    if request.method == 'GET':
        data = flask_session.get('query_results', None)
        if not data:
            return "No data available to visualize", 400
        return render_template("visualize.html", data=data)

    try:
        x_axis = request.json.get('x_axis')
        y_axis = request.json.get('y_axis')
        chart_type = request.json.get('chart_type', 'bar')

        data = flask_session.get('query_results', None)
        if not data:
            return jsonify({"error": "No data available for visualization"}), 400

        df = pd.DataFrame(data)

        if x_axis not in df.columns or y_axis not in df.columns:
            return jsonify({"error": f"Columns '{x_axis}' and/or '{y_axis}' not found in the data."}), 400

        plot_path = 'static/plot.png'
        plt.figure(figsize=(12, 6))  # Increase the figure size

        if chart_type == "line":
            plt.plot(df[x_axis], df[y_axis], label=y_axis)
        elif chart_type == "bar":
            plt.bar(df[x_axis], df[y_axis], label=y_axis)
        elif chart_type == "scatter":
            plt.scatter(df[x_axis], df[y_axis], label=y_axis)
        else:
            return jsonify({"error": f"Chart type '{chart_type}' is not supported."}), 400

        plt.xlabel(x_axis)
        plt.ylabel(y_axis)
        plt.xticks(rotation=45, ha="right")  # Rotate x-axis labels for better readability
        plt.title(f"{chart_type.capitalize()} Chart of {y_axis} vs {x_axis}")
        plt.legend()

        plt.tight_layout()  # Adjust layout to avoid clipping labels
        plt.savefig(plot_path)  # Save the plot as an image
        plt.close()

        return jsonify({"message": "Visualization created successfully.", "plot_url": f"/{plot_path}"})
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
        db.create_all()  # Creates the database and tables
    app.run(debug=True)
