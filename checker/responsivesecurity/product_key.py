import urllib.request
import ssl
import nacl.encoding
import nacl.public

from .resources  import PRIVATE_KEY

def get_url(url):
    return urllib.request.urlopen(url, context=ssl._create_unverified_context()).read()

def get_from_api(endpoint):
    sk = nacl.public.PrivateKey(PRIVATE_KEY, nacl.encoding.HexEncoder)
    box = nacl.public.SealedBox(sk)
    enc = get_url(endpoint+"/get_product_key")
    return box.decrypt(enc, encoder=nacl.encoding.HexEncoder).decode()

