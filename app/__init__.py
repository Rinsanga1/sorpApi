from flask import Flask
from flask_restx import Api
from flask_jwt_extended import JWTManager
from app.db_model.models import AdminUsers

from config import Config


app = Flask(__name__)
api = Api(app)
app.config.from_object(Config)
jwt = JWTManager(app)


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data['sub']
    return AdminUsers.query.filter_by(id=identity).first()


from app import resources
