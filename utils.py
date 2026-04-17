import logging
import os
from datetime import datetime
from functools import wraps

import requests
from flask import flash, redirect, session as flask_session, url_for

from extensions import db
from models import QueryHistory, User

logger = logging.getLogger(__name__)

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

DANGEROUS_SQL_KEYWORDS = {'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE'}


def validate_sql_query(query):
    """Return (is_safe, message). Only SELECT queries are permitted."""
    query_upper = query.upper().strip()
    for keyword in DANGEROUS_SQL_KEYWORDS:
        if keyword in query_upper:
            return False, f"Operation '{keyword}' is not allowed for security reasons"
    return True, "Query is safe"


def log_query(query, query_type, execution_time=None, success=True, error_message=None):
    """Persist a query execution record for analytics."""
    try:
        history = QueryHistory(
            user_id=flask_session.get('user_id'),
            query=query,
            query_type=query_type,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
        )
        db.session.add(history)
        db.session.commit()
    except Exception:
        logger.exception("Failed to log query")


def get_hf_query_suggestion(user_query):
    """Return an AI-powered query suggestion from Hugging Face, or None if unavailable."""
    if not HUGGINGFACE_API_KEY:
        return None
    try:
        api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        payload = {
            "inputs": f"Improve this SQL query for better performance and readability: {user_query}",
            "parameters": {"max_length": 150, "temperature": 0.7, "do_sample": True},
        }
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                return result[0].get('generated_text')
            return result.get('generated_text')
        logger.error("Hugging Face API returned %s", response.status_code)
    except Exception:
        logger.exception("Error fetching Hugging Face suggestion")
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in flask_session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        user = db.session.get(User, flask_session['user_id'])
        if not user:
            flask_session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated
