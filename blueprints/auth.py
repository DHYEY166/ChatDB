import logging
from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, session as flask_session, url_for

from extensions import db
from models import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html', title="Login")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            flask_session.permanent = True
            flask_session['user_id'] = user.id
            flask_session['username'] = user.username
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            logger.info("Login successful for %s", username)
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))

        logger.info("Failed login attempt for %s", username)
        flash('Invalid username or password', 'error')

    return render_template('login.html', title="Login")


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html', title="Register")
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return render_template('register.html', title="Register")
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html', title="Register")

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html', title="Register")
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html', title="Register")

        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            logger.info("Registered new user: %s", username)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            logger.exception("Registration failed for %s", username)
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('register.html', title="Register")


@auth_bp.route('/logout')
def logout():
    flask_session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
