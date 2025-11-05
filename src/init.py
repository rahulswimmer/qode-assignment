from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time

def get_driver():
    optn = Options()
    optn.add_argument("--disable-gpu")
    optn.add_argument("--no-sandbox")
    optn.add_argument("--disable-dev-shm-usage")

    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=optn)
    return driver

if __name__ == "__main__":
    driver = get_driver()
    driver.get("x.com")
    driver.quit()
