from . import control

#from .proxy import make_proxy, restrict, unrestrict

import hashlib
import secrets
import random
import os
import sys
import time

BLINDTEXT = """
Lyrisch: Hinter den Wortbergen

Weit hinten, hinter den Wortbergen, fern der Länder Vokalien und Konsonantien leben die Blindtexte. Abgeschieden wohnen Sie in Buchstabhausen an der Küste des Semantik, eines großen Sprachozeans. Ein kleines Bächlein namens Duden fließt durch ihren Ort und versorgt sie mit den nötigen Regelialien. Es ist ein paradiesmatisches Land, in dem einem gebratene Satzteile in den Mund fliegen. Nicht einmal von der allmächtigen Interpunktion werden die Blindtexte beherrscht – ein geradezu unorthographisches Leben. Eines Tages aber beschloss eine kleine Zeile Blindtext, ihr Name war Lorem Ipsum, hinaus zu gehen in die weite Grammatik. Der große Oxmox riet ihr davon ab, da es dort wimmele von bösen Kommata, wilden Fragezeichen und hinterhältigen Semikoli, doch das Blindtextchen ließ sich nicht beirren. Es packte seine sieben Versalien, schob sich sein Initial in den Gürtel und machte sich auf den Weg. Als es die ersten Hügel des Kursivgebirges erklommen hatte, warf es einen letzten Blick zurück auf die Skyline seiner Heimatstadt Buchstabhausen, die Headline von Alphabetdorf und die Subline seiner eigenen Straße, der Zeilengasse. Wehmütig lief ihm eine rethorische Frage über die Wange, dann setzte es seinen Weg fort. Unterwegs traf es eine Copy. Die Copy warnte das Blindtextchen, da, wo sie herkäme wäre sie zigmal umgeschrieben worden und alles, was von ihrem Ursprung noch übrig wäre, sei das Wort „und“ und das Blindtextchen solle umkehren und wieder in sein eigenes, sicheres Land zurückkehren. Doch alles Gutzureden konnte es nicht überzeugen und so dauerte es nicht lange, bis ihm ein paar heimtückische Werbetexter auflauerten, es mit Longe und Parole betrunken machten und es dann in ihre Agentur schleppten, wo sie es für ihre Projekte wieder und wieder missbrauchten. Und wenn es nicht umgeschrieben wurde, dann benutzen Sie es immer noch.
"""


def gen_text():
    a = random.randrange(len(BLINDTEXT) - 1)
    b = random.randrange(a, len(BLINDTEXT))
    return BLINDTEXT[a:b]


def user_from_flag(flag):
    return "account_" + hashlib.sha512(("final(tm)secretsalt3" + flag).encode()).hexdigest()[:12]


def gen_username():
    return "user_" + secrets.token_hex(8)

def gen_website():
    front = random.choice(["faust", "example", "fau", "ctftime"])
    tld = random.choice(["com", "de", "ru", "edu", "gov", "ninja"])
    return front + "." + tld


def gen_password():
    return "pw_" + secrets.token_hex(8)

try:
    from ctf_gameserver.checker import BaseChecker, OK, NOTFOUND, NOTWORKING
except ImportError:
    BaseChecker = object

class Checker(BaseChecker):
    @property
    def client(self):
        if self._client is None:
            self._client = control.Client(self._baseurl, logger = self.logger)
            self._client.screenshot("after_init")
        return self._client

    def __init__(self, tick, team, service, ip):
        BaseChecker.__init__(self, tick, team, service, ip)
        self._baseurl = 'https://%s:5003/responsivesecurity' % ip
        self._client = None


    def get_online_teams(self):
        import requests
        import json
        self.logger.info("getting online teams")
        j = json.loads(requests.get("https://2019.faustctf.net/flagid.json").text)
        self.logger.info("loaded flagid.json")
        j = list(j.get("responsivesecurity", {}).keys() or ["10.66.1.2"])
        j = [i.split(".")[2] for i in j]
        self.logger.info("teams %r...", j[:10])
        return j

    def place_flag(self):
        import requests
        r = requests.get(self._baseurl + "/", verify = False)
        if r.status_code != 503:
            self.store_blob('flagid_%03d' % self.tick, b"online")

        flag = self.get_flag(self.tick)
        self.logger.info("placing %s", flag)
        fuser = user_from_flag(flag)


        username = gen_username()
        password = gen_password()

        self.client.reset()
        ts = self.get_online_teams()
        self.logger.info("got_online")
        random.shuffle(ts)
        self.logger.info("shuffled")
        ts = ts[:10]
        self.logger.info("truncated")
        self.store_yaml('ts_%d'%self.tick, ts)
        self.logger.info("stored_yaml")
        self.client.select_endpoints(ts)
        self.logger.info("selected_online %r", ts)
        self.client.delete_unselected_endpoints()
        self.logger.info("deleted_offline %r", ts)
        self.client.create_account(fuser, flag)
        row = control.Row(username = username, password = flag, site = gen_website(), notes = gen_text())
        self.client.store(row)

        return OK


    def check_flag(self, tick):

        #try:
        self.client.reset()
        #ts = self.get_online_teams()
        ts = self.retrieve_yaml("ts_%d"%self.tick)
        self.client.select_endpoints(ts)
        self.client.delete_unselected_endpoints()
        self.logger.info("selected %r", ts)
        flag = self.get_flag(tick)
        fuser = user_from_flag(flag)
        self.client.screenshot("before_login")
        self.client.login(fuser, flag)
        self.client.screenshot("after_login")
        for row in self.client.read_table():
            for word in row:
                if flag in word:
                    return OK
        import NOTFOUND


    def check_service(self):
        if not self.client:
            return NOTWORKING

        if not self.client.check_endpoint_list():
            return NOTWORKING
        return OK


