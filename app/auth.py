from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from email_validator import validate_email, EmailNotValidError
from .models import db, User
from .i18n import t
from .captcha import generate_captcha_text, create_captcha_image, verify_captcha
import requests
import urllib.parse
import logging

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_submit():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash(t("Invalid email or password"), "error")
        return redirect(url_for("auth.login_page"))

    # Check if user is disabled
    if user.disabled:
        flash(t("Your account has been disabled. Please contact support."), "error")
        return redirect(url_for("auth.login_page"))

    login_user(user)
    return redirect(url_for("main.index"))


@auth_bp.get("/register")
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    # Generate new CAPTCHA for registration page
    captcha_text = generate_captcha_text()
    session['captcha'] = captcha_text
    
    # Get preserved form data if any (from failed CAPTCHA)
    form_data = session.pop('register_form_data', {})
    
    return render_template("auth/register.html", form_data=form_data)


@auth_bp.get("/captcha")
def get_captcha():
    """Generate and serve CAPTCHA image"""
    captcha_text = generate_captcha_text()
    session['captcha'] = captcha_text
    
    image_buffer = create_captcha_image(captcha_text)
    return send_file(image_buffer, mimetype='image/png')


@auth_bp.post("/register")
def register_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    captcha_input = request.form.get("captcha", "").strip()
    # Age confirm is checked client-side only (not in form)

    # Validation checks
    if not name or not email or not password or not confirm_password or not captcha_input:
        flash(t("Please fill in all fields"), "error")
        # Preserve all form data
        session['register_form_data'] = {
            'name': name,
            'email': email,
            'password': password,
            'confirm_password': confirm_password
        }
        return redirect(url_for("auth.register_page"))
    
    # Verify CAPTCHA first
    stored_captcha = session.get('captcha', '')
    if not verify_captcha(captcha_input, stored_captcha):
        flash(t("Incorrect verification code. Please try again."), "error")
        # Clear the used CAPTCHA
        session.pop('captcha', None)
        # Preserve all form data including passwords
        session['register_form_data'] = {
            'name': name,
            'email': email,
            'password': password,
            'confirm_password': confirm_password
        }
        return redirect(url_for("auth.register_page"))

    # Validate email format
    try:
        # Validate and normalize the email
        validated_email = validate_email(email)
        email = validated_email.email  # Get the normalized email
    except EmailNotValidError as e:
        flash(t("Please enter a valid email address"), "error")
        session['register_form_data'] = {'name': name, 'email': email, 'password': password, 'confirm_password': confirm_password}
        return redirect(url_for("auth.register_page"))

    # Prevent registration with admin emails
    if email.endswith("@admin") or email.endswith("@admin.com"):
        flash(t("@admin.com is invalid email"), "error")
        session['register_form_data'] = {'name': name, 'email': email, 'password': password, 'confirm_password': confirm_password}
        return redirect(url_for("auth.register_page"))

    if password != confirm_password:
        flash(t("Passwords do not match"), "error")
        session['register_form_data'] = {'name': name, 'email': email, 'password': password, 'confirm_password': confirm_password}
        return redirect(url_for("auth.register_page"))

    if len(password) < 6:
        flash(t("Password must be at least 6 characters long"), "error")
        session['register_form_data'] = {'name': name, 'email': email, 'password': password, 'confirm_password': confirm_password}
        return redirect(url_for("auth.register_page"))

    if User.query.filter_by(email=email).first():
        flash(t("Email is already in use"), "error")
        session['register_form_data'] = {'name': name, 'email': email, 'password': password, 'confirm_password': confirm_password}
        return redirect(url_for("auth.register_page"))

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Clear the used CAPTCHA
    session.pop('captcha', None)

    login_user(user)
    flash(t("Account created successfully!"), "success")
    return redirect(url_for("main.index"))


@auth_bp.post("/logout")
@login_required
def logout_submit():
    logout_user()
    return redirect(url_for("main.index"))
