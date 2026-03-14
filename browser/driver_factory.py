from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config.settings import BROWSERSTACK_USERNAME, BROWSERSTACK_ACCESS_KEY


def _get_base_options():
    """
    Shared anti-detection Chrome options for both
    local and BrowserStack drivers.
    """
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return options


def get_local_driver():
    """
    Local Chrome driver with anti-detection flags.
    Uses webdriver_manager to auto-install ChromeDriver.
    """
    options = _get_base_options()
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)

    # Hide Selenium signature from website JS checks
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def get_browserstack_driver(capabilities_dict):
    """
    BrowserStack remote driver with anti-detection flags.
    Capabilities come from config/browserstack_caps.py
    """
    url     = f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"
    options = _get_base_options()

    for key, value in capabilities_dict.items():
        options.set_capability(key, value)

    driver = webdriver.Remote(
        command_executor=url,
        options=options
    )

    # Hide Selenium signature on remote browser too
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver
