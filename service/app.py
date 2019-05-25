import flask
import os

app = flask.Flask(__name__)

from client import client
from pwned_passwords import pwned
from storage import storage

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/storage.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False # quiet the startup warning
    SQLALCHEMY_ECHO = False # enable to see sql queries made by storage module

app.config.from_object(Config)

app.register_blueprint(client, url_prefix = "/client")
app.register_blueprint(pwned, url_prefix = "/pwned")
app.register_blueprint(storage, url_prefix = "/storage")

@app.route("/")
def index():
    return flask.redirect(flask.url_for("client.send_page", page="entry.html"))

@app.route("/favicon.<suffix>")
def favicon(suffix):
    return flask.redirect(flask.url_for("static", filename="favicon."+suffix), code=301)
