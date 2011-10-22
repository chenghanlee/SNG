from helppme.models.user import User, Vote
from datetime import datetime
from mongoengine import Document, BooleanField, DecimalField, DateTimeField, \
                        IntField, ListField, ReferenceField, StringField, \
                        SequenceField

class Item(Document):
  ip = StringField()
  sequence_num = SequenceField()
  created = DateTimeField(default=datetime.now())
  title = StringField()
  store = StringField()
  category = IntField()
  description = StringField()
  score = DecimalField(default=0)
  dead = BooleanField(default=False)
  deleted = BooleanField(default=False)

  flags = ListField(IntField())
  profile = ReferenceField(User)
  sockvotes = ListField(ReferenceField(Vote))
  votes = ListField(ReferenceField(Vote))