from flask import Flask, render_template, request, _request_ctx_stack, url_for
from flask.ext.login import current_user, LoginManager
from werkzeug.local import LocalProxy

from helppme.globals import app
from helppme.models.user import User
from helppme.views.deals import deals
from helppme.views.user import user

from mongoengine import connect

app.register_blueprint(deals)
app.register_blueprint(user)
app.config.update(
	DEBUG=True,
	SECRET_KEY='\xb8\xc7"\xe0\xf2U\x96\xb5\x94c\xe5\xc5R1\x9f\xd6f\x87i\xe96\x92\xf0\xf1'
)

connect('ecchiav-dev', host='mongodb://ecchiav:0e2dYTeh@staff.mongohq.com:10051/ecchiav-dev')

#configuring login information
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "user.login"
login_manager.session_protection

@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()

#jinaj2 global template variables
app.jinja_env.globals['user'] = current_user
