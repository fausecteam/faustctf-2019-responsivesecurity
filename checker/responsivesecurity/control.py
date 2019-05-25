from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging
from selenium.common.exceptions import TimeoutException
import os
import tempfile
import subprocess
import time
import random

from selenium.webdriver.support.ui import Select


from collections import namedtuple


from . import product_key
from . import reference

Row = namedtuple("Row", "site username password notes")

default_logger = logging.getLogger(__name__)

class Client:
    def __init__(self, url = "http://localhost/responsivesecurity", logger = default_logger, proxy = None):
        options = webdriver.ChromeOptions()
        self.logger = logger
        self.logger.info("using chromium version %s", subprocess.getoutput("chromium --version"))
        options.headless = True
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-running-insecure-content")
        self.url = url
        self.logger.info("using api %s", self.url)
        self.logger.info("querying for product key")
        key = product_key.get_from_api(url + "/client")
        self.logger.info("product key: %s", key)
        self.browser = webdriver.Chrome(options = options)
        self.logger.info("opened browser")
        self.browser.get(url)
        self.screenshot("enter_product_key")
        self.browser.add_cookie({"name": "product_key", "value": key})
        self.logger.info("added cookie")
        self.reset()

    def screenshot(self, name):
        if True:
            self.logger.info("saving screenshot %s", name)
            screenshot = self.browser.get_screenshot_as_png()
            link = reference.store(self.url, "636865636b65726f7574", "/"+name+".png", screenshot)
            self.logger.info("saved as %s", link)

    def reset(self):
        self.browser.get(self.url)
        self.logger.info("loaded page")
        
    def login(self, user, password):
        u = self.browser.find_element_by_id("account_username")
        u.send_keys(user)
        p = self.browser.find_element_by_id("account_password")
        p.send_keys(password)
        self.screenshot("login_before_submit")
        p.submit()
        self.screenshot("login_after_submit")
        time.sleep(0.3)
        self.screenshot("login_after_submit2")

        try:
            self.wait_for_message("invalid password")
        except:
            pass
        else:
            raise ValueError("invalid password")
        m = self.browser.find_element_by_id("manager")
        #if not m.is_displayed():
        #    raise RuntimeError("something went wrong, could not find manager table")
        try:
            self.logger.info("waiting for manager table to appear")
            # TODO: handle error case
            WebDriverWait(self.browser, 10).until(
                    EC.visibility_of(m)
                )
            assert m.is_displayed()
        except:
            self.logger.info("manager table did not appear")
            raise

    def create_account(self, user, password):
        u = self.browser.find_element_by_id("account_username")
        u.send_keys(user)
        p = self.browser.find_element_by_id("account_password")
        p.send_keys(password)
        c = self.browser.find_element_by_id("create_account")
        c.click()
        r = self.browser.find_element_by_id("confirm_password")
        r.send_keys(password)
        self.screenshot("create_account_before_submit")
        p.submit()
        self.screenshot("create_account_after_submit")
        try:
            self.wait_for_message("invalid password")
        except:
            pass
        else:
            raise ValueError("invalid password")
        m = self.browser.find_element_by_id("manager")
        #if not m.is_displayed():
        #    raise RuntimeError("something went wrong, could not find manager table")
        try:
            self.logger.info("waiting for manager table to appear")
            # TODO: handle error case
            WebDriverWait(self.browser, 10).until(
                    EC.visibility_of(m)
                )
            assert m.is_displayed()
        except:
            self.screenshot("create_account_wait_failed")
            self.logger.info("manager table did not appear")
            raise
        self.screenshot("create_account_success")

    def read_table(self):
        manager = self.browser.find_element_by_id("manager")
        hrows = manager.find_elements_by_css_selector(".pw-row")
        vrows = []
        for row in hrows:
            hcols = row.find_elements_by_css_selector(".td")
            vcols = []
            vrows.append(vcols)
            for c in hcols:
                v = ""
                for e in c.find_elements_by_css_selector("input[type=text], input[type=password], [contenteditable]"):
                    v = e.get_attribute("value") or e.text.strip()
                    if v: break
                vcols.append(v)
        prows = [Row(*row[1:]) for row in vrows]
        return prows
    def check_endpoint_list(self):
        endpoints = {}
        manager = self.browser.find_element_by_id("manager")
        values_page = {o.get_attribute("value") for o in manager.find_elements_by_css_selector("#config > select > option")}
        values_expected = {"https://10.66.%s.2:5003/responsivesecurity/%s"%(i,a) for i in range(1, 256) for a in ("storage", "pwned")}
        return values_expected == values_expected

    def store(self, row):
        manager = self.browser.find_element_by_id("manager")
        new = manager.find_element_by_css_selector('input[type="button"][value="New Entry"')
        new.click()
        hrow = manager.find_element_by_css_selector(".pw-row:last-child")
        for i,value in enumerate(row):
            inputElem = hrow.find_element_by_css_selector(".td:nth-child({n}) [contenteditable], .td:nth-child({n}) input".format(n=i+2))
            inputElem.send_keys(value)
        s = hrow.find_element_by_css_selector('input[type="submit"][value="save"]')
        s.click()
        self.wait_for_message("saved")

    def wait_for_message(self, message):
        self.logger.info("waiting for message %r", message)
        panel = self.browser.find_element_by_id("messages-bottom")
        WebDriverWait(self.browser, 5).until(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#messages-bottom div"), message))
        self.logger.info("message appeared, waiting for it to disappear")
        
        WebDriverWait(self.browser, 10).until_not(
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#messages-bottom div"), message))
        self.logger.info("message disappeared: %r", message)
    def select_endpoints(self, liste):
        teamnames = ["Team "+str(i) if str(i) != "1" else "NOP-Team" for i in liste]
        storage_endpoints = Select(self.browser.find_element_by_css_selector("[name=storage_endpoints]"))
        storage_endpoints.deselect_all()
        for t in teamnames:
            storage_endpoints.select_by_visible_text(t)

        pwned_endpoints = Select(self.browser.find_element_by_css_selector("[name=pwned_endpoint]"))
        t = random.choice(teamnames)
        pwned_endpoints.select_by_visible_text(t)
    def delete_unselected_endpoints(self):
        self.browser.execute_script("""
                for(let o of document.querySelectorAll("[name=storage_endpoints] option:not(:checked)")){
                    o.parentNode.removeChild(o);
                }
                """)


    def close(self):
        if self.browser is not None:
            self.browser.quit()
            self.browser = None
    def __del__(self):
        try: self.close()
        except: pass

                    
if __name__ == "__main__":
    import secrets
    user = secrets.token_hex(8)
    pw = secrets.token_hex(8)

    logging.basicConfig(level=logging.INFO)
    c = Client()
    c.create_user(user, pw)
    
    print(c.read_table())
