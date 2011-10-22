from flask import Blueprint, jsonify, redirect, render_template, request, \
				  url_for
from flask.ext.login import login_user, logout_user

from helppme.helper import debug
#from helppme.globals import app, login_form, signup_form
from helppme.forms.forms import Login_Form, Signup_Form
from helppme.models.user import User

import string 

user = Blueprint('user', __name__)

@user.route('/signup', methods=['POST'])
def signup():
	form = Signup_Form(csrf_enabled=False)
	
	if request.method == 'POST' and form.validate_on_submit():
		username = request.form.get('username', None)
		email = request.form.get('email', None)
		password = request.form.get('password', None)
		password_hash = User.gen_hash(password)
		new_user = User(name=username, email=email, 
						password_hash=password_hash)
		new_user.save()
		login_user(new_user)
		return jsonify(status="success", redirect=request.referrer)
	else:
		#we can safely assume that there at most 1 error for any field
		errors={}
		if len(form.email.errors) > 0:
			errors["email_error"] = form.email.errors[0]
		if len(form.username.errors) > 0:
			errors["username_error"] = form.username.errors[0]
		if len(form.password.errors) > 0:
			errors["password_error"] = form.password.errors[0]
		if errors:
			errors["status"] = "error"
		return jsonify(errors)

@user.route('/login', methods=['POST'])
def login():
	form = Login_Form(csrf_enabled=False)
	if request.method == 'POST' and form.validate_on_submit():
		login_user(form.user)	
		return jsonify(status="success", redirect=request.referrer)
	else:
		return jsonify(status="error", msg="Wrong username or password")

@user.route('/logout', methods=['GET'])
def logout():
	logout_user()
	return redirect(request.referrer)

