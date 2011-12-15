from helppme.globals import db
from datetime import datetime


class Vote(db.Document):
    date = db.DateTimeField(default=datetime.now())
    ip = db.StringField()
    point = db.BooleanField(default=True)  # true = 1pt and false = -1pt

    deal_id = db.StringField()
    voter_id = db.StringField()

    meta = {
        'indexes': ['deal_id', 'voter_id']
    }
