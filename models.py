from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class APIRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(50), nullable=False)
    is_valid = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<APIRequest {self.id}, Valid: {self.is_valid}>'


class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<APIRequest {self.id}, Valid: {self.is_valid}>'
