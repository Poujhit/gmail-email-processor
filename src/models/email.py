from peewee import Model, CharField, TextField, DateTimeField

from database import db


class Email(Model):
    id = CharField(primary_key=True)
    sender = CharField()
    subject = CharField()
    snippet = TextField()
    body = TextField()
    received_at = DateTimeField()

    class Meta:
        database = db
