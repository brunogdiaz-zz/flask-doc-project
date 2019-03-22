import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

# A Blueprint is a way to organize a group of related views and other code.
# This is prefered instead of just connecting it directly with the app.
bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = f'Username "{username}" already exists exist.'
        if error:
            flash(error)
        else:
            db.execute(
                'INSERT INTO user (username, password) VALUES(?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        # Get user from Database
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username, )
        ).fetchone()
        if username is None:
            error = 'Username is required.'
        elif user is None:
            error = 'Username is not in our system.'
        elif password is None:
            error = 'Password is required.'
        elif not check_password_hash(user['password'], password):
            error = 'Password incorrect. Try again.'

        if error:
            flash(error)
        else:
            # Clear and Set User Session
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

    return render_template('auth/login.html')


# Runs Before View Function - Checks if user is logged in
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id:
        db = get_db()
        g.user = db.execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
    else:
        g.user = None


@bp.route('/logout')
def logout():
    # Clears User Session to log off
    session.clear()
    return redirect(url_for('index'))


# Will be a decorator for other views to force user to be logged in
# Acts as a wrapper for other views
def login_required(view):
    @functools.wraps(view)
    def wrapper_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapper_view
