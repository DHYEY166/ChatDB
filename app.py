import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from flask import jsonify
from sqlalchemy import text

from extensions import db

_log_handlers = [logging.StreamHandler()]
_log_file = os.getenv('LOG_FILE')
if _log_file:
    _log_handlers.append(logging.FileHandler(_log_file))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    handlers=_log_handlers,
)
logger = logging.getLogger(__name__)


def create_app(testing=False):
    from flask import Flask, render_template

    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if testing:
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        db_path = os.getenv('DATABASE_PATH', '/tmp/chatdb.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    db.init_app(app)

    from blueprints.main import main_bp
    from blueprints.auth import auth_bp
    from blueprints.data import data_bp
    from blueprints.visualize import viz_bp
    from blueprints.ai import ai_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(viz_bp)
    app.register_blueprint(ai_bp)

    with app.app_context():
        db.create_all()

    @app.route('/health')
    def health_check():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})
        except Exception as e:
            logger.error("Health check failed: %s", e)
            return jsonify({"status": "unhealthy", "error": str(e)}), 500

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        logger.error("500 error: %s", e)
        return render_template('500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
