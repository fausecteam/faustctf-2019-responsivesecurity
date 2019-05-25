import os  
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options  

chrome_options = Options()  
chrome_options.add_argument("--headless")  

driver = webdriver.Chrome(chrome_options=chrome_options)

driver.get("http://www.fau.de")
print(driver.page_source)

search_field = driver.find_element_by_id("headsearchinput")  
search_field.clear()
search_field.send_keys("Mathematik")
search_field.send_keys(Keys.RETURN)
assert "Supercomputer" in driver.page_source
driver.close()
