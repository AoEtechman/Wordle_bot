from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

PATH = "C:\Program Files (x86)\chromedriver.exe"
driver = webdriver.Chrome(PATH)
driver.get("https://www.nytimes.com/games/wordle/index.html")
# try:
#     search = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.ID, "search"))
#     )
#     # button.click()
# except:
#     driver.close()
search = driver.find_element_by_xpath("//[local-name()='svg'")
search.send_keys("coding")
search.send_keys(Keys.RETURN)
time.sleep(10)
driver.close()