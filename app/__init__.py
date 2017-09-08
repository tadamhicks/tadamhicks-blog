# third-party imports
from flask import Flask
from peewee import *
from playhouse.flask_utils import FlaskDB

# db variable initialization

app = Flask(__name__)
app.config.from_object('config')
db = FlaskDB(app)
database = db.database

from app import views, models