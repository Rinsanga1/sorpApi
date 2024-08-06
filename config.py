import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    sorp_db_path = os.path.join(basedir, "app", "sorp_db")
    os.makedirs(sorp_db_path, exist_ok=True)

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(sorp_db_path, "db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = "ismykey"
