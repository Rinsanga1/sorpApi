from flask import Flask
from flask_restx import Api
from config import Config

app = Flask(__name__)
api = Api(app)
app.config.from_object(Config)

from app import resources
