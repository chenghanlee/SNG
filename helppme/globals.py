from flask import Flask
from flask.ext.mongoengine import MongoEngine
from itsdangerous import URLSafeTimedSerializer

import os
import redis
import simplejson as json

app = Flask(__name__)
db = MongoEngine()
r = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
signer = URLSafeTimedSerializer(os.urandom(24))

#possible deal categories and sort options
categories = ['everything', 'games', 'apparel', 'electronics', 'computers',
              'entertainment', 'food', 'beauty', 'books', 'home',
              'automotive', 'finance', 'other']
sorts = ['trending', 'popular', 'newest']
date_ranges = ['today', 'week', 'month', 'year']
user_history_filters = ['shared', 'liked', 'bookmarked']

#global constants
affiliate_tag = '?tag=helppme-20'  # our affiliate tag for amazon
cache_timeout = 900  # default redis cache key timeout length
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
max_num_documents = 1000  # of documents to return by a deal query
non_url_location_length = 25  # how many characters a non-url location can have
per_page = 15  # how many deals to display per page
short_title_length = 100  # max length for short title, which is used in the url
task_retry_delay = 10  # require celery tasks to wait 10 seconds before retrying
set_of_deal_list_keys = 'set_of_deal_list_keys'  # a set that contains all the


# This method is used to convert an object to json. The class object must
# defined a to_json method before it can be properly converted
class CustomObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if callable(getattr(obj, "to_json")):
            return obj.to_json()
        return json.JSONEncoder.default(self, obj)
