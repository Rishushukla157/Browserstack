import os
from dotenv import load_dotenv

load_dotenv()

# BrowserStack
BROWSERSTACK_USERNAME  = os.getenv("BROWSERSTACK_USERNAME")
BROWSERSTACK_ACCESS_KEY = os.getenv("BROWSERSTACK_ACCESS_KEY")

# Google Translate (replacing Rapid API)
TRANSLATE_API_KEY = os.getenv("TRANSLATE_API_KEY")
TRANSLATE_API_URL = "https://translation.googleapis.com/language/translate/v2"



# Output
OUTPUT_DIR = "output"