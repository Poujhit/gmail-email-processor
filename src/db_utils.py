from peewee import SqliteDatabase, Model, CharField, TextField, DateTimeField

db = SqliteDatabase("emails.db")


class Email(Model):
    id = CharField(primary_key=True)
    sender = CharField()
    subject = CharField()
    body = TextField()
    received_at = DateTimeField()

    class Meta:
        database = db


def setup_database():
    db.connect()
    db.create_tables([Email], safe=True)
    db.close()
