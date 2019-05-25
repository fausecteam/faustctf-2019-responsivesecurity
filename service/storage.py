import flask
from flask_sqlalchemy import SQLAlchemy


import werkzeug.routing
import datetime
from werkzeug.exceptions import Forbidden, NotFound
import re

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship


EXPIRE = datetime.timedelta(minutes = 20)

storage = flask.Blueprint("storage", __name__)


@storage.record_once
def setup_db(state):
    db = SQLAlchemy(state.app)

    with state.app.app_context():
        Model.metadata.create_all(bind=db.engine)

    state.app.config["storage.db"] = db

def db_session():
    return flask.current_app.config["storage.db"].session


USER_REGEX = r"(?P<user>[a-f0-9]{20})"
DIR_REGEX = r"(?P<dirname>([^/]+/)*)"
FILE_REGEX = USER_REGEX + "/" + DIR_REGEX + r"(?P<basename>[^/]+)"

def nonames(r):
    """Remove named groups from a regex string to use it in an URL converter"""
    return re.sub(r"\(\?P<[^>]+>", "(", r)

assert re.match("^"+USER_REGEX+"$", "aaaaabbbbbcccccddddd")
assert re.match("^"+DIR_REGEX+"$", "")
assert re.match("^"+DIR_REGEX+"$", "a/")
assert re.match("^"+DIR_REGEX+"$", "a/bbb/")
assert re.match("^"+FILE_REGEX+"$", "aaaaabbbbbcccccddddd/asdf")
assert re.match("^"+FILE_REGEX+"$", "aaaaabbbbbcccccddddd/asdf/89cadv")


class Promise:
    def __init__(self, callme):
        self.callme = callme

@storage.before_request
def resolve_promises():
    for k in list(flask.request.view_args.keys()):
        if isinstance(flask.request.view_args[k], Promise):
            flask.request.view_args[k] = flask.request.view_args[k].callme()

Model = declarative_base()

class User(Model):
    __tablename__ = "user"
    key = Column(String(40), primary_key = True)
    expire = Column(DateTime)
    entries = relationship("Entry", back_populates = "user")
    def refresh(self):
        self.expire = datetime.datetime.now() + EXPIRE


def query_user(key, create = False):
    u = db_session().query(User).filter_by(key = key).first()
    if u is None:
        if create:
            u = User(key = key, expire = datetime.datetime.now() + EXPIRE)
            db_session().add(u)
    if u is None:
        raise NotFound("invalid user key")
    return u

class UserConverter(werkzeug.routing.BaseConverter):
    regex = nonames(USER_REGEX)
    def __init__(self, url_map, create = False):
        super().__init__(url_map)
        self.__create = create
    def to_python(self, s):
        def get_user():
            return query_user(key = s, create = self.__create)
        return Promise(get_user)
    def to_url(u):
        return u.key

class Entry(Model):
    __tablename__ = "entry"
    user_key = Column(String(40), ForeignKey("user.key"), primary_key = True)
    path = Column(String(100), primary_key = True)
    payload = Column(String(300))
    
    user = relationship("User", back_populates = "entries")


class EntryConverter(werkzeug.routing.PathConverter):
    regex = nonames(FILE_REGEX)
    def __init__(self, url_map, create = False):
        self.__create = create
    def to_url(self, entry):
        return entry.user_key + "/" + entry.path
    def to_python(self, urlpart):
        m = re.match(FILE_REGEX, urlpart)
        def get_entry():
            u = query_user(m.group("user"), create = self.__create)
            e = query_entry(u, m.group("dirname")+m.group("basename"), create = self.__create)
            u.refresh()
            return e
        return Promise(get_entry)


def query_entry(user, path, create = False):
    e = db_session().query(Entry).filter_by(user_key = user.key, path = path).first()
    if e is None and create:
        e = Entry(user_key = user.key, user = user, path = path, payload = "")
        db_session().add(e)
    if e is None:
        raise NotFound("invalid entry path")
    return e

class DirConverter(werkzeug.routing.BaseConverter):
    regex = nonames(DIR_REGEX)


@storage.record_once
def register_converters(state):
    state.app.url_map.converters["entry"] = EntryConverter
    state.app.url_map.converters["user"] = UserConverter
    state.app.url_map.converters["dir"] = DirConverter



# all routes are allowed cross origin.
@storage.after_request
def cross_origin(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    if flask.request.method == "OPTIONS":
        if "Allow" in r.headers:
            r.headers["Access-Control-Allow-Methods"] = r.headers["Allow"]
        else:
            r.headers["Access-Control-Allow-Methods"] = "PUT, GET, DELETE, OPTIONS"
        r.status_code = 200
    return r


@storage.route("/", methods=["GET"])
def index():
    return flask.redirect(flask.url_for("static", filename="api_doc.html"))

@storage.route("/<entry:entry>", methods = ["GET"])
def get(entry):
    return flask.Response(entry.payload, mimetype = "text/plain")


@storage.route("/<entry(create=True):entry>", methods = ["PUT"])
def put(entry):
    entry.payload = flask.request.get_data()
    db_session().add(entry)
    db_session().add(entry.user)
    db_session().commit()
    return "Ok"

@storage.route("/<entry:entry>", methods = ["DELETE"])
def delete(entry):
    db_session().delete(entry)
    db_session().commit()
    return "Ok"

@storage.route("/<user:user>/<dir:dirname>")
def ls(user, dirname):
    pattern = flask.request.args.get("pattern", "%")
    limit = flask.request.args.get("limit", None)
    offset = flask.request.args.get("offset", None)
    q = db_session().query(Entry).\
            filter(Entry.user_key == user.key).\
            filter(Entry.path.like(pattern)).\
            filter(Entry.path.startswith(dirname))
    print("pattern", pattern)
    print("limit", limit)
    print("offset", limit)
    if limit is not None:
        q = q.limit(int(limit))
    if offset is not None:
        q = q.offset(int(offset))

    result = q.all()
    return flask.render_template("dirlisting.html", ls = result, user = user, dirname = dirname, pattern = pattern)



@storage.before_request
def cleanup():
    # TODO: delete expired users
    pass
