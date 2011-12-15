from flask.ext.mongoengine import MongoEngine
from flask.ext.celery import Celery
from flask.ext.login import current_user, LoginManager
from flask.ext.markdown import Markdown

from werkzeug.contrib.cache import RedisCache

from helppme.globals import app, db, categories, sorts, date_ranges, \
                            user_history_filters
from helppme.template_filters import prettify
from helppme.helper import  get_deal, user_has
from helppme.caching.jinja2_fragment_caching import FragmentCacheExtension
from helppme.models.user import User
from helppme.views.deals import deals
from helppme.views.user import user
from helppme.views.other import other

import os

app.register_blueprint(deals)
app.register_blueprint(user)
app.register_blueprint(other)

app.config.from_pyfile('celeryconfig.py')
app.config.update(
    #general flask config
    DEBUG=True,
    SECRET_KEY=os.urandom(24),

    #mongodb config
    MONGODB_DB='ecchiav-dev',
    MONGODB_USERNAME='ecchiav',
    MONGODB_PASSWORD='0e2dYTeh',
    MONGODB_HOST='staff.mongohq.com',
    MONGODB_PORT='10051',

    #email server config
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="587",
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME="mokkori@ecchiav.com",
    MAIL_PASSWORD="Hnaoa6hW!",
    MAIL_FAIL_SILENTLY=False
)
#setup jinja2 fragment caching
app.jinja_env.fragment_cache = RedisCache(host="127.0.0.1",
                                          default_timeout=86000)
app.jinja_env.add_extension(FragmentCacheExtension)

#connecting to celery
Celery(app)

#connect to mongohq
db.init_app(app)

#enabling markdown
Markdown(app)

#configuring flask-login
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "other.login_required"
login_manager.session_protection

@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()

#jinaj2 global template variables and function
#variables available to jinja2
app.jinja_env.globals['categories'] = categories
app.jinja_env.globals['date_ranges'] = date_ranges
app.jinja_env.globals['sorts'] = sorts
app.jinja_env.globals['user'] = current_user
app.jinja_env.globals['user_history_filters'] = user_history_filters

#custom fuctions available to jinja2
app.jinja_env.globals['get_deal'] = get_deal
app.jinja_env.globals['user_has'] = user_has