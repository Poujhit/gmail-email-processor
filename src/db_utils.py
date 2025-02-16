from peewee import (
    SqliteDatabase, Model, CharField, TextField, DateTimeField, DatabaseProxy
)

db_proxy = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db_proxy


class Email(BaseModel):
    id = CharField(primary_key=True)
    sender = CharField()
    subject = CharField()
    body = TextField()
    received_at = DateTimeField()


def get_or_initialize_db(testing=False):
    """
    Initialize and return a database connection. If connection already exists, reuse it.

    If `testing` is True, it uses a test database; otherwise, it defaults to 'emails.db'.
    Reuses an existing database connection if available; otherwise, initializes a new one.

    Args:
        testing (bool): Whether to use a test database.

    Returns:
        SqliteDatabase: The initialized database connection.
    """

    db_name = "test_database.db" if testing else "emails.db"

    if db_proxy.obj and isinstance(db_proxy.obj, SqliteDatabase):
        if db_proxy.obj.database == db_name:
            return db_proxy.obj  # Reuse existing DB instance

    db = SqliteDatabase(db_name)
    db_proxy.initialize(db)

    if db.is_closed():
        db.connect(reuse_if_open=True)
    db.create_tables([Email], safe=True)

    return db
