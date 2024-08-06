from flask import Flask
from flask_restx import Api
from flask_jwt_extended import JWTManager
from config import Config

app = Flask(__name__)
api = Api(app)
app.config.from_object(Config)
jwt = JWTManager(app)

from app import resources
