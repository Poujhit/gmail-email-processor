from peewee import SqliteDatabase
from src.models.email import Email

db = SqliteDatabase("emails.db")


def setup_database():
    db.connect()
    db.create_tables([Email], safe=True)
    db.close()
