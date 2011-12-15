from flask.ext.login import UserMixin
from werkzeug import check_password_hash, generate_password_hash

from helppme.globals import db, DATETIME_FORMAT, r
from helppme.models.deal import Deal
from datetime import datetime, timedelta

import uuid


class Password_Change_Request(db.Document):
    time_created = db.DateTimeField(default=datetime.now(), required=True)
    token = db.StringField(default=str(uuid.uuid1()), required=True)
    user = db.StringField(required=True)

    meta = {
        'indexes': ['token']
    }

    def within_time_limit(self):
        '''
        This methods checks to see if the request is older than 1 day.

        A request is considered valid if its less than 1 day old and invalid
        if otherwise
        '''
        one_day = timedelta(days=1)
        time_difference = datetime.now() - self.time_created
        if time_difference < one_day:
            return True
        return False


class User(db.Document, UserMixin):
    name = db.StringField()
    sequence_num = db.SequenceField()  # used for redis hash purposes
    created = db.DateTimeField(default=datetime.now())
    about = db.StringField()
    auth = db.IntField(default=0)
    admin = db.IntField(default=100)
    member = db.StringField()
    karma = db.IntField(default=1)
    avg = db.DecimalField()
    weight = db.DecimalField(default=0.5)
    ignored = db.BooleanField(default=False)
    email = db.StringField()
    password_hash = db.StringField()
    showdead = db.BooleanField(default=False)

    deals_flagged = db.ListField(db.StringField())
    deals_saved = db.ListField(db.StringField())
    deals_submitted = db.ListField(db.StringField())
    deals_voted = db.ListField(db.StringField())
    votes = db.ListField(db.StringField())

    meta = {
        'indexes': ['name', 'email', 'deals_flagged', 'deals_saved',
                    'deals_submitted', 'deals_voted', 'password_hash']
    }

    def change_password(self, new_password):
        '''
        This function changes the user's password tp new_password

        args:
            new_password: a plain password
        '''
        new_pwd_hash = generate_password_hash(new_password, method='sha1',
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

    def date_joined(self):
        return datetime.strftime(self.created, DATETIME_FORMAT)

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

        user = User.objects(name=username).only('password_hash').first()
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
        if email is None:
            return False

        key = 'email_available_' + email
        rv = r.get(key)
        if rv is not None:
            return rv

        if email is not None and User.objects(email=email).first() is None:
            r.set(key, False)
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
        if username is None:
            return False

        key = 'username_available_' + username
        rv = r.get(key)
        if rv is not None:
            return rv

        if username is not None and \
            User.objects(name=username).first() is None:
            r.set(key, False)
            return True
        else:
            return False

    def num_deals_liked(self):
        key = "".join([self.name, '_num_deals_liked'])
        if r.exists(key):
            return r.get(key)
        else:
            num_votes_given = len(self.deals_voted)
            r.setex(key, 3600, num_votes_given)
            return num_votes_given

    def num_deals_shared(self):
        key = "".join([self.name, '_num_deals_shared'])
        if r.exists(key):
            return r.get(key)
        else:
            num_votes_given = len(self.deals_submitted)
            r.setex(key, 3600, num_votes_given)
            return num_votes_given

    def num_likes_received(self):
        '''
        This method returns the total amounts of points that this user's
        submitted deal has received
        '''

        key = "".join([self.name, '_num_likes_received'])
        if r.exists(key):
            return r.get(key)
        else:
            # points = [deal.num_votes for deal in self.deals_submitted]
            # total_points = sum(points)
            deals = Deal.objects(id__in=self.deals_submitted)
            points = [deal.num_votes for deal in deals]
            total_points = sum(points)
            r.setex(key, 3600, total_points)
            return total_points
