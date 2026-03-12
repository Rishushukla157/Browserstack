import pytest
from browser.driver_factory import get_browserstack_driver
from config.browserstack_caps import BROWSER_CAPS
from backend.database import db
from main import run_pipeline


@pytest.mark.parametrize("capabilities", BROWSER_CAPS)
def test_el_pais_browserstack(capabilities):
    # Log the test run in Supabase
    browser  = capabilities.get("browserName", capabilities.get("deviceName", "Unknown"))
    platform = (
        capabilities.get("bstack:options", {}).get("os") or
        capabilities.get("bstack:options", {}).get("deviceName") or
        "Mobile"
    )

    test_run = db.create_test_run(browser=browser, platform=platform)
    run_id   = test_run.get("id", None)

    driver = get_browserstack_driver(capabilities)
    try:
        run_pipeline(driver, test_run_id=run_id)

        # Mark passed in BrowserStack + DB
        driver.execute_script(
            'browserstack_executor: {"action": "setSessionStatus",'
            '"arguments": {"status": "passed", "reason": "Pipeline completed"}}'
        )
        if run_id:
            db.update_test_run_status(run_id, "passed")

    except Exception as e:
        driver.execute_script(
            f'browserstack_executor: {{"action": "setSessionStatus",'
            f'"arguments": {{"status": "failed", "reason": "{str(e)[:100]}"}}}}'
        )
        if run_id:
            db.update_test_run_status(run_id, "failed")
        raise

    finally:
        driver.quit()