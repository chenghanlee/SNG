from helppme.globals import db, DATETIME_FORMAT
from helppme.models.vote import Vote

from datetime import datetime


class Deal(db.Document):
    ip = db.StringField()
    sequence_num = db.SequenceField()  # used for url and redis hash purposes
    created = db.DateTimeField(default=datetime.now())
    title = db.StringField()
    short_title = db.StringField()  # used for url purposes
    location = db.StringField()
    online_deal = db.BooleanField(default=True)
    category = db.StringField()
    description = db.StringField()
    edited = db.DateTimeField()
    score = db.DecimalField(default=0)  # used for trending sort
    num_votes = db.IntField(default=0)  # used for popular sort
    dead = db.BooleanField(default=False)
    deleted = db.BooleanField(default=False)

    flags = db.ListField(db.StringField())  # user ids of people who flagged this
    author_id = db.StringField()  # user id of who created this deal
    sockvotes = db.ListField(db.StringField())
    votes = db.ListField(db.StringField())  # user ids of people who voted

    meta = {
        'indexes': ['-created',
                    ('-created', 'author_id', 'dead', 'deleted'),
                    ('-created', 'category',  'dead', 'deleted'),
                    ('-created', '-score', 'category', 'dead', 'deleted'),
                    ('-created', '-num_votes',  'category', 'dead', 'deleted'),
                    ('sequence_num', 'short_title')]
    }

    @property
    def date_created(self):
        '''
        This method returns a prettier format for when the movie was
        created e.g. "now", "a hour ago", "today", "yest" etc.

        Args:
            None
        '''

        return pretty_date(self.created)

    @property
    def date_edited(self):
        '''
        This method returns a prettier format for when the deal was last modified
        by its author e.g. "now", "a hour ago", "today", "yest" etc.

        Args:
          None
        '''
        if self.edited:
            return pretty_date(self.edited)

    @property
    def url(self):
        url = ['/deals/', str(self.sequence_num), '/', self.short_title, '/']
        return ''.join(url)

    def to_json(self):
        '''
        This method returns a selected set of deal attributes as json
        '''
        json = {'id': str(self.id), 'ip': self.ip, 'sequence_num': self.sequence_num,
                'created': datetime.strftime(self.created, DATETIME_FORMAT),
                'title': self.title, 'short_title': self.short_title,
                'location': self.location, 'category': self.category,
                'description': self.description,
                'score': self.score, 'num_votes': self.num_votes,
                'author_id': self.author_id, 'url': self.url}
        if self.edited is not None:
            json['edited'] = datetime.strftime(self.edited, DATETIME_FORMAT)
        return json


class Item(db.Document):
    ip = db.StringField()
    sequence_num = db.SequenceField()
    created = db.DateTimeField(default=datetime.now())
    title = db.StringField()
    location = db.StringField()
    category = db.StringField()
    description = db.StringField()
    score = db.DecimalField(default=0)
    dead = db.BooleanField(default=False)
    deleted = db.BooleanField(default=False)

    flags = db.ListField(db.IntField())
    # user = db.ReferenceField(User)
    sockvotes = db.ListField(db.ReferenceField(Vote))
    votes = db.ListField(db.ReferenceField(Vote))


""""
Curtesy of python pretty

Formats dates, numbers, etc. in a pretty, human readable format.
"""
__author__ = "S Anand (sanand@s-anand.net)"
__copyright__ = "Copyright 2010, S Anand"
__license__ = "WTFPL"

from datetime import datetime


def _df(seconds, denominator=1, text='', past=True):
    if past:   return         str((seconds + denominator/2)/ denominator) + text + ' ago'
    else:      return 'in ' + str((seconds + denominator/2)/ denominator) + text


def pretty_date(time=False, asdays=False, short=False):
    '''Returns a pretty formatted date.
    Inputs:
        time is a datetime object or an int timestamp
        asdays is True if you only want to measure days, not seconds
        short is True if you want "1d ago", "2d ago", etc. False if you want
    '''

    now = datetime.now()
    if type(time) is int:   time = datetime.fromtimestamp(time)
    elif not time:          time = now

    if time > now:  past, diff = False, time - now
    else:           past, diff = True,  now - time
    seconds = diff.seconds
    days    = diff.days

    if short:
        if days == 0 and not asdays:
            if   seconds < 10:          return 'now'
            elif seconds < 60:          return _df(seconds, 1, 's', past)
            elif seconds < 3600:        return _df(seconds, 60, 'm', past)
            else:                       return _df(seconds, 3600, 'h', past)
        else:
            if   days   == 0:           return 'today'
            elif days   == 1:           return past and 'yest' or 'tom'
            elif days    < 7:           return _df(days, 1, 'd', past)
            elif days    < 31:          return _df(days, 7, 'wk', past)
            elif days    < 365:         return _df(days, 30, 'mo', past)
            else:                       return _df(days, 365, 'yr', past)
    else:
        if days == 0 and not asdays:
            if   seconds < 10:          return 'now'
            elif seconds < 60:          return _df(seconds, 1, ' seconds', past)
            elif seconds < 120:         return past and 'a minute ago' or 'in a minute'
            elif seconds < 3600:        return _df(seconds, 60, ' minutes', past)
            elif seconds < 7200:        return past and 'an hour ago' or'in an hour'
            else:                       return _df(seconds, 3600, ' hours', past)
        else:
            if   days   == 0:           return 'today'
            elif days   == 1:           return past and 'yesterday' or'tomorrow'
            #elif days   == 2:           return past and 'day before' or 'day after'
            elif days    < 7:           return _df(days, 1, ' days', past)
            elif days    < 14:          return past and 'last week' or 'next week'
            elif days    < 31:          return _df(days, 7, ' weeks', past)
            elif days    < 61:          return past and 'last month' or 'next month'
            elif days    < 365:         return _df(days, 30, ' months', past)
            elif days    < 730:         return past and 'last year' or 'next year'
            else:                       return _df(days, 365, ' years', past)
