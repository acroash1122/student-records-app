"""
Selenium conftest — creates a headless Chrome WebDriver.

Docker (Dockerfile.selenium) sets:
  CHROME_BIN=/usr/bin/chromium
  CHROMEDRIVER_PATH=/usr/bin/chromedriver

Local development falls back to webdriver-manager, which auto-downloads
the correct ChromeDriver for the installed Chrome version.
"""
import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def _build_options() -> Options:
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    return options


@pytest.fixture(scope='module')
def driver():
    """Yield a headless Chrome WebDriver; quit when the module finishes."""
    options = _build_options()

    chrome_bin = os.environ.get('CHROME_BIN')
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')

    if chromedriver_path and os.path.exists(chromedriver_path):
        # Docker path — use system-installed chromium/chromedriver
        service = Service(chromedriver_path)
        if chrome_bin:
            options.binary_location = chrome_bin
    else:
        # Local path — let webdriver-manager download the right driver
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())

    _driver = webdriver.Chrome(service=service, options=options)
    _driver.implicitly_wait(10)
    yield _driver
    _driver.quit()
