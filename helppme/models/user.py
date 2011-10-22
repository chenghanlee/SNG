from flask.ext.login import UserMixin

from datetime import datetime
from mongoengine import BooleanField, DateTimeField, DecimalField, Document, \
	EmbeddedDocumentField, IntField, EmailField, ListField, ObjectIdField, \
	ReferenceField, StringField
from werkzeug import check_password_hash, generate_password_hash


class User(Document, UserMixin):
	name = StringField()	
	created = DateTimeField(default=datetime.now())
	about = StringField()
	auth = IntField(default=0)
	admin = IntField(default=100)
	member = StringField()
	karma = IntField(default=1)
	avg = DecimalField()
	weight = DecimalField(default=0.5)
	ignored = BooleanField(default=False)
	email = StringField()
	password_hash = StringField()
	showdead = BooleanField(default=False)

	submitted_items = ListField(ReferenceField('Item'))
	votes = ListField(ReferenceField('Vote'))
	
	meta = {
		'indexes': ['name', 'email', ('name', 'password_hash')]
	}

	def change_password(self, password):
		'''
		This function changes the user's password

		args:
			password: a plain password
		'''
		new_pwd_hash = generate_password_hash(password, 
											  method='sha1',
											  salt_length=16)
		self.password_hash = new_pwd_hash
		self.save()
		
	def check_password(self, password):
		'''
		This function checks the entered plain password against the user's encryped password

		args:
			password: entered plain password
		'''
		return check_password_hash(self.password_hash, password)
	
	@classmethod 
	def gen_hash(cls, string):
		'''
		This is a static class function generates a salted hash via
		werkzeug's generate_password_hash function

		:param string: the string that will be used to generate a password hash
		'''

		return generate_password_hash(string, method='sha1', salt_length=16)
		
	@classmethod
	def get_user(cls, username, password):
		'''
		This function returns a user according to the entered username and password

		Args:
			username: a user's username
			password: a plain password
		'''
		
		user = User.objects(name=username).first()
		if user is not None and check_password_hash(user.password_hash, password):
			return user

		return None
		
	@classmethod
	def is_email_available(cls, email):
		'''
		This method checks to see if an email has been previously used or registered by another user

		Args:
			email: The email to be checked for availability

		Returns:
			False is the email has been used by another user
			True if otherwise
		'''
		if email is not None and User.objects(email=email).first() is None:
			return True
		else:
			return False
			
	@classmethod
	def is_username_available(cls, username):
		'''
		This method checks to see if an username has been registered by another user

		Args:
			username: The username to be checked for availability

		Returns:
			False is the username has been used by another user
			True if otherwise
		'''
		if username is not None and \
		   User.objects(name=username).first() is None:
			return True
		else:
			return False

class Vote(Document):
	date = DateTimeField(default=datetime.now())
	ip = DateTimeField()
	point = BooleanField() #true = 1pt and false = -1pt

	item = ReferenceField('Item')
	user = ReferenceField(User) 

	meta = {
		'indexes': ['point', 'item', 'user']
	}