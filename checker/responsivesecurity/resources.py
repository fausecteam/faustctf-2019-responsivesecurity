import pkg_resources
import os

PRIVATE_KEY = pkg_resources.resource_string(__name__, "gameserver_private_key.txt").strip()
BROWSERMOB_EXE = pkg_resources.resource_filename(__name__, "browsermob-proxy-2.1.4/bin/browsermob-proxy")
