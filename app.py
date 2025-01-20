from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os
import openai
import logging

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
    Session = sessionmaker(bind=engine)
    session = Session()

# MongoDB Configuration
mongo_client = None
mongo_db = None

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
        db_type = request.json.get('db_type')  # 'sql' or 'nosql'
        if db_type == 'sql':
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
        elif db_type == 'nosql':
            mongo_uri = request.json.get('mongo_uri')
            db_name = request.json.get('db_name')
            if not mongo_uri or not db_name:
                return jsonify({"error": "MongoDB URI and database name are required."}), 400
            try:
                global mongo_client, mongo_db
                mongo_client = MongoClient(mongo_uri)
                mongo_db = mongo_client[db_name]
                return jsonify({"message": f"Connected to MongoDB database: {db_name}"})
            except Exception as e:
                logger.error(f"Error connecting to MongoDB: {e}")
                return jsonify({"error": str(e)}), 500
    return render_template('connect.html', title="Connect to Database")

@app.route('/manage', methods=['GET', 'POST'])
def manage_page():
    if request.method == 'POST':
        db_type = request.json.get('db_type')
        query = request.json.get('query')
        if db_type == 'sql':
            try:
                result = session.execute(text(query)).fetchall()
                if result:
                    # Use row._mapping to convert rows to dictionaries
                    data = [dict(row._mapping) for row in result]
                    return jsonify({"data": data})
                else:
                    session.commit()
                    return jsonify({"message": "Query executed successfully."})
            except Exception as e:
                logger.error(f"SQL query error: {e}")
                return jsonify({"error": str(e)}), 500
        elif db_type == 'nosql':
            collection_name = request.json.get('collection_name')
            if not collection_name:
                return jsonify({"error": "Collection name is required for NoSQL queries."}), 400
            try:
                collection = mongo_db[collection_name]
                data = list(collection.find(query))
                return jsonify({"data": data})
            except Exception as e:
                logger.error(f"NoSQL query error: {e}")
                return jsonify({"error": str(e)}), 500
    return render_template('manage.html', title="Manage Data")


@app.route('/visualize', methods=['GET', 'POST'])
def visualize_page():
    if request.method == 'GET':
        return render_template("visualize.html", message="Submit data using the form below.")

    try:
        # Parse the request data
        query = request.json.get('query')
        x_axis = request.json.get('x_axis')
        y_axis = request.json.get('y_axis')
        chart_type = request.json.get('chart_type', 'bar')

        if not query:
            return jsonify({"error": "No query provided."}), 400

        # Execute the SQL query
        result = session.execute(text(query)).fetchall()
        df = pd.DataFrame(result, columns=result[0].keys())

        print("Received DataFrame:")
        print(df.head())  # Debug the DataFrame content

        # Validate that x_axis and y_axis exist in the DataFrame
        if x_axis not in df.columns or y_axis not in df.columns:
            return jsonify({"error": f"Columns '{x_axis}' and/or '{y_axis}' not found in the data."}), 400

        # Generate the chart
        plot_path = 'static/plot.png'
        if chart_type == 'bar':
            df.plot(kind='bar', x=x_axis, y=y_axis).get_figure().savefig(plot_path)
        elif chart_type == 'line':
            df.plot(kind='line', x=x_axis, y=y_axis).get_figure().savefig(plot_path)
        elif chart_type == 'scatter':
            df.plot(kind='scatter', x=x_axis, y=y_axis).get_figure().savefig(plot_path)

        return jsonify({"message": "Visualization created.", "plot_url": f"/{plot_path}"})
    except Exception as e:
        print(f"Error during visualization: {e}")  # Log the exception
        return jsonify({"error": str(e)}), 500

@app.route('/report', methods=['GET', 'POST'])
def report_page():
    if request.method == 'GET':
        # Render a form or instructions for the report page
        return render_template("report.html", message="Submit data using the form below.")

    # Handle POST request
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
