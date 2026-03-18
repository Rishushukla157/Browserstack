import pytest
from browser.driver_factory import get_browserstack_driver
from config.browserstack_caps import BROWSER_CAPS
from main import run_pipeline


@pytest.mark.parametrize("capabilities", BROWSER_CAPS)
def test_el_pais_browserstack(capabilities):
    driver = get_browserstack_driver(capabilities)
    try:
        run_pipeline(driver)

        # Mark passed in BrowserStack
        driver.execute_script(
            'browserstack_executor: {"action": "setSessionStatus",'
            '"arguments": {"status": "passed", "reason": "Pipeline completed"}}'
        )

    except Exception as e:
        driver.execute_script(
            f'browserstack_executor: {{"action": "setSessionStatus",'
            f'"arguments": {{"status": "failed", "reason": "{str(e)[:100]}"}}}}'
        )
        raise

    finally:
        driver.quit()