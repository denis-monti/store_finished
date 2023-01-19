from flask import render_template, flash, redirect, url_for, request, render_template_string, g, \
    jsonify, current_app, session

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from urllib.parse import unquote
from app import db
from app.auth import bp
from app.auth.forms import RegistrationForm, LoginForm, ResetPasswordRequestForm
from app.models import User
from app.auth.email import send_password_reset_email



@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form_reg = RegistrationForm()
    if form_reg.validate_on_submit():
        user = User(username=form_reg.username.data, email=form_reg.email.data)
        user.set_password(form_reg.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем с началом сотрудничества с нашим интернет-магазином')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form_reg=form_reg)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if (url_for('auth.login')) != ('/' + (request.referrer.split('/')[3])):
        session['previous_url'] = unquote(request.referrer)
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form_auth = LoginForm()
    if form_auth.validate_on_submit():
        user = User.query.filter_by(username=form_auth.username.data).first()
        if user is None or not user.check_password(form_auth.password.data):
            return redirect(url_for('auth.login'))
        login_user(user, remember=form_auth.remember_me.data)
        redirect_prev_url = session['previous_url']
        session.pop('previous_url', None)
        return redirect(redirect_prev_url)

    return render_template('auth/login.html', form_auth=form_auth)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(unquote(request.referrer))

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            ('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title=('Reset Password'), form_reset=form)