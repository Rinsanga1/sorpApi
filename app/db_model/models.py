from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(session_options={"autoflush": True})


class APIRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(50), nullable=False)
    is_valid = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)


class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(50), nullable=False)
    key_maker = db.Column(db.String(50), nullable=False)


class AdminUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50), unique=True)
