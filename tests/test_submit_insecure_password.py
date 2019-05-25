from selenium import webdriver

import product_key

endpoint = "http://localhost:5000"

PRODUCT_KEY = product_key.get_product_key_from_api(endpoint + "/client", "../gameserver_private_key.txt")
print(PRODUCT_KEY)

browser = webdriver.Firefox()
browser.get(endpoint)
browser.add_cookie({"name": "product_key", "value": PRODUCT_KEY})
browser.get(endpoint)

