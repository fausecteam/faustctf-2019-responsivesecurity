from browsermobproxy import Server
import threading
import random
import atexit

from . import resources
import logging

_server = None
_lock = threading.RLock()

def get_server():
    global _server
    with _lock:
        options = dict(port = random.randrange(2**15, 2**16))
        if _server is None:
            for i in range(3):
                try:
                    _server = Server(path = resources.BROWSERMOB_EXE, options = options)
                    break
                except Exception as e:
                    logging.get_logger(__name__).error(repr(e))
                    pass
        _server.start(options = options)
    return _server

def stop_server():
    print("stopping browsermobproxy server")
    if _server is not None:
        _server.stop()

atexit.register(stop_server)


class Proxy:

    def __init__(self):
        self.pro
        super().__init__(path=path, options=options)

def make_proxy():
    return get_server().create_proxy()

def restrict(proxy, hosts):
    if not hosts:
        rexexps = ["^$"]
    regexps = ["^http://%s/.*$" % h for h in hosts]
    proxy.whitelist(",".join(hosts), 451)
def unrestrict(self):
    proxy.whitelist(".*", 451)

