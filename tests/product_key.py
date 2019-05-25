import urllib.request
import nacl.encoding
import nacl.signing

def get_url(url):
    return urllib.request.urlopen(url).read()

def get_product_key_from_api(endpoint, keyfile):
    with open(keyfile, "rb") as kf:
        sk = nacl.signing.SigningKey(kf.read().strip(), nacl.encoding.HexEncoder)
    h = get_url(endpoint+"/get_product_key/hash")
    s = sk.sign(h).signature.hex()
    p = get_url(endpoint+"/get_product_key/"+h.decode()+s).strip()
    return p.decode()

def get_product_key_from_file(fname):
    with open(fname, "r") as f: return f.read().strip()


