from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config.settings import BROWSERSTACK_USERNAME, BROWSERSTACK_ACCESS_KEY

def get_local_driver():
    """Returns a local Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_browserstack_driver(capabilities_dict):
    url = f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"

    options = Options()
    for key, value in capabilities_dict.items():
        options.set_capability(key, value)

    driver = webdriver.Remote(
        command_executor=url,
        options=options  
    )

    return driver