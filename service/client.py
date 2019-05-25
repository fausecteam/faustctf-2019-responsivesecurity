"""
The real application code is javascript.
The /client path should only be accessible by the owning team and the gameserver.

 - the team can access the file where the product key is stored.
 - the gameserver queries /client/get_prodcut_key to receive an encrypted copy that it can decrypt.

The endpoints defined in other modules are accessible by everyone.

"""

import flask
import secrets
import os
import hashlib
import nacl.encoding
import nacl.public
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCT_KEY_FILE = os.path.join(DIR, "data/product_key.txt")
GAMESERVER_PUBLIC_KEY_FILE = os.path.join(DIR, "gameserver_public_key.txt")

def ensure_product_key_exists():
    """atomically create a product key file
    - first, generate a fresh product key
    - then, try to link it to the known position.
        if the target file already exists, discard the generated key"""
    l = secrets.token_hex(8).upper()
    PRODUCT_KEY = "{}-{}-{}-{}".format(l[0:4], l[4:8], l[8:12], l[12:16])
    with tempfile.NamedTemporaryFile(dir=os.path.join(DIR, "data")) as f:
        f.write(PRODUCT_KEY.encode() + b"\n")
        f.flush()
        try:
            os.link(f.name, PRODUCT_KEY_FILE)
        except FileExistsError: pass

# load PRODUCT_KEY from file
ensure_product_key_exists()
with open(PRODUCT_KEY_FILE) as f:
    PRODUCT_KEY = f.read().strip()

# load gameserver GAMESERVER_PUBLIC_KEY from file
with open(GAMESERVER_PUBLIC_KEY_FILE) as f:
    GAMESERVER_PUBLIC_KEY = nacl.public.PublicKey(
            f.read().strip(),
            encoder = nacl.encoding.HexEncoder)


client = flask.Blueprint("client", __name__)

@client.route("/")
def index():
    return flask.redirect(flask.url_for("client.send_page", page="entry.html"))

@client.route("/<path:page>")
def send_page(page):
    flask.g.product_key = flask.request.args.get("product_key", "") or flask.request.cookies.get("product_key", "")
    
    if flask.g.product_key.lower() != PRODUCT_KEY.lower():
        return flask.render_template("product_key.html", PRODUCT_KEY_FILE = PRODUCT_KEY_FILE), 401
    return flask.send_from_directory(os.path.join(client.root_path, "client"), page)

@client.route("/get_product_key")
def get_prodcut_key():
    box = nacl.public.SealedBox(GAMESERVER_PUBLIC_KEY)
    encrypted = box.encrypt(PRODUCT_KEY.encode(), encoder = nacl.encoding.HexEncoder)
    return encrypted
