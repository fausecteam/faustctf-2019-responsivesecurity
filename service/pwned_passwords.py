import flask
import os
import mmap



hash_file = open("hashes.lst.sorted", "rb")
mm = mmap.mmap(hash_file.fileno(), 0, access=mmap.ACCESS_READ)
nhashes = len(mm) // 41 # 41 = length of sha1-hash + newline
print("nhashes", nhashes)

pwned = flask.Blueprint("pwned", __name__)

@pwned.route("/")
def index():
    return "TODO: link api doc"

@pwned.route("/range/<prefix>")
def hash_range(prefix):
    prefix = prefix.encode()
    if len(prefix) != 5:
        return "bad request", 400
    first = 0
    count = nhashes
    while count > 0:
        step = count // 2
        mid = first + step
        if mm[41 * mid : 41*mid + 5] < prefix:
            first = mid+1
            count -= step+1
        else:
            count = step
    def generate():
        i = first
        while True:
            line = mm[41*i : 41*i + 41]
            if line[:5] != prefix:
                break
            yield line[5:]
            i += 1

    r = flask.Response(generate(), mimetype = "text/plain")
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


