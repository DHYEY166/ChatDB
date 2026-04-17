import logging
import os
from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, render_template, request, session as flask_session
from sqlalchemy import text

from extensions import db
from models import DatabaseConnection, QueryHistory
from utils import log_query, login_required, validate_sql_query

logger = logging.getLogger(__name__)

data_bp = Blueprint('data', __name__)

UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}


@data_bp.route('/connect', methods=['GET', 'POST'])
@login_required
def connect_page():
    if request.method == 'POST':
        db_uri = request.json.get('db_uri')
        connection_name = request.json.get('connection_name', 'Default Connection')

        if not db_uri:
            return jsonify({"error": "SQL Database URI is required."}), 400

        try:
            db.engine.dispose()
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            connection = DatabaseConnection(
                user_id=flask_session['user_id'],
                name=connection_name,
                connection_string=db_uri,
                database_type='sqlite' if 'sqlite' in db_uri else 'mysql' if 'mysql' in db_uri else 'postgresql',
            )
            db.session.add(connection)
            db.session.commit()
            return jsonify({"message": f"Connected to SQL database: {db_uri}"})
        except Exception as e:
            logger.exception("DB connection error")
            return jsonify({"error": str(e)}), 500

    connections = DatabaseConnection.query.filter_by(user_id=flask_session.get('user_id')).all()
    return render_template('connect.html', title="Connect to Database", connections=connections)


@data_bp.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_page():
    if request.method == 'POST':
        query = request.json.get('query', '')
        is_safe, message = validate_sql_query(query)
        if not is_safe:
            return jsonify({"error": message}), 400

        start_time = datetime.now()
        try:
            if query.strip().lower().startswith('select'):
                result = db.session.execute(text(query))
                columns = list(result.keys())
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

    user_id = flask_session.get('user_id')
    try:
        history = (
            db.session.query(QueryHistory)
            .filter(QueryHistory.user_id == user_id)
            .order_by(QueryHistory.created_at.desc())
            .limit(10)
            .all()
        )
    except Exception:
        logger.exception("Error fetching query history")
        history = []

    return render_template('manage.html', title="Manage Data", history=history)


@data_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No selected file"}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "File type not allowed"}), 400

    table_name = ''.join(c if c.isalnum() else '_' for c in os.path.splitext(file.filename)[0].lower())
    if table_name[0].isdigit():
        table_name = 'f_' + table_name

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        if ext == 'json':
            import json
            with open(file_path) as f:
                data = json.load(f)
            data = data if isinstance(data, list) else [data]
            df = pd.DataFrame(_flatten_json(data))
        elif ext in ('xlsx', 'xls'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        inspector = db.inspect(db.engine)
        if table_name in inspector.get_table_names():
            db.session.execute(text(f'DROP TABLE IF EXISTS {table_name}'))
            db.session.commit()

        df.to_sql(table_name, db.engine, index=False, if_exists='replace')
        log_query(f"UPLOAD: {file.filename} -> {table_name}", 'upload', success=True)
        logger.info("Uploaded %s as table %s (%d rows)", file.filename, table_name, len(df))

        return jsonify({
            "message": f"File uploaded successfully as table '{table_name}'",
            "table_name": table_name,
            "columns": list(df.columns),
            "row_count": len(df),
        })
    except Exception as e:
        logger.exception("File upload failed")
        log_query(f"UPLOAD: {file.filename}", 'upload', success=False, error_message=str(e))
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@data_bp.route('/history')
@login_required
def query_history():
    page = request.args.get('page', 1, type=int)
    user_id = flask_session.get('user_id')
    try:
        history = (
            db.session.query(QueryHistory)
            .filter(QueryHistory.user_id == user_id)
            .order_by(QueryHistory.created_at.desc())
            .paginate(page=page, per_page=20, error_out=False)
        )
    except Exception:
        logger.exception("Error fetching query history")
        history = None

    return render_template('history.html', title="Query History", history=history)


def _flatten_json(data):
    result = []
    for item in data:
        flat = {}
        for key, value in item.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, (str, int, float, bool)):
                        flat[f"{key}_{k}"] = v
            elif isinstance(value, list):
                import json
                flat[key] = json.dumps(value)
            else:
                flat[key] = value
        result.append(flat)
    return result
