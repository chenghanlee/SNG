from helppme.models.user import User

from flask.ext.wtf import  DecimalField, email, Form, Length, Required,\
	PasswordField, NumberRange, TextField, TextAreaField, SelectField,\
	SubmitField, URL

class Login_Form(Form):
	username = TextField("username", validators=[Required(message='Username is required')])
	password = TextField("password", validators=[Required(message='Password is required')])
	submit = SubmitField("submit")
	
	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.user = None
		
	def validate(self):
		rv = Form.validate(self)
		if not rv:
			return False

		user = User.get_user(self.username.data, self.password.data)
		if user is None:
			return False
		
		self.user = user
		return True

class Item_Form(Form):
	title=TextField("title", validators=[
			Required(message='Please tell us what you found')])
	url=TextField("url", validators=[
			Required(message='Please tell us where to buy it'),
			URL(message='Is this a valid URL?')])
	price=DecimalField("price")
	categories=SelectField('categories', choices=[('electronics', 'electronics'), 
										('food', 'food'), ('others', 'others')])
	description=TextAreaField('description', validators=[(
			Length(max=1000, message='Description cannot be longer than 1000 characters'))])
	submit=SubmitField("Submit") 

class Signup_Form(Form):
	email = TextField("email", validators=[email(message='Is this a valid email?'),
						Required(message='Email address is required')])
	
	username = TextField("username", validators=[Length(min=3, message = 'Username must be 3 characters or longer'),
							Length(max=20, message="Username cannot be longer than 20 characters"),
							Required(message='Username is required')])
	password = TextField("password", validators=[Length(min=6, message="Password must be 6 characters or longer"),
							Length(max=50, message="Password cannot be longer than 50 characters"),
							Required(message='Password is required')])			
	submit = SubmitField("submit")

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
	
	def validate(self):
		rv = Form.validate(self)
		num_errors = 0
		if not rv:
			num_errors = num_errors + 1
		
		if not User.is_email_available(self.email.data):
			self.email.errors.append('This email has been registered. Try a different one')
			num_errors = num_errors + 1

		if not User.is_username_available(self.username.data):
			self.username.errors.append('This username has been registered. Try a different one')
			num_errors = num_errors + 1

		if num_errors > 0:
			return False

		return True