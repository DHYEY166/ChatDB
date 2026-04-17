import logging

from flask import Blueprint, redirect, render_template, session as flask_session, url_for
from sqlalchemy import text

from extensions import db
from models import DatabaseConnection, QueryHistory

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html', title="Home")


@main_bp.route('/dashboard')
def dashboard():
    user_id = flask_session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    try:
        total = db.session.query(QueryHistory).filter_by(user_id=user_id).count()
        successful = db.session.query(QueryHistory).filter_by(user_id=user_id, success=True).count()
        recent = (
            db.session.query(QueryHistory)
            .filter_by(user_id=user_id)
            .order_by(QueryHistory.created_at.desc())
            .limit(5)
            .all()
        )
        connections = db.session.query(DatabaseConnection).filter_by(user_id=user_id).all()
        stats = {
            'total_queries': total,
            'successful_queries': successful,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'connections': len(connections),
            'recent_queries': recent,
        }
    except Exception:
        logger.exception("Error building dashboard stats")
        stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'success_rate': 0,
            'connections': 0,
            'recent_queries': [],
        }

    return render_template('dashboard.html', title="Dashboard", stats=stats)
