"""pytest setup: config.yaml, the Appium driver, evidence screenshots."""
import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest
import yaml
from appium import webdriver
from appium.options.android import UiAutomator2Options

ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"


@pytest.fixture(scope="session")
def config():
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _appium_ready(url):
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/status", timeout=3) as r:
            return bool(json.loads(r.read().decode()).get("value", {}).get("ready"))
    except Exception:
        return False


def _connected_devices():
    out = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
    return [line.split("\t")[0] for line in out.splitlines()[1:] if line.endswith("\tdevice")]


@pytest.fixture(scope="session")
def driver(config):
    url = config["appium_server_url"]
    if not _appium_ready(url):
        pytest.exit(f"Appium server is not running at {url}. Start it with: appium", returncode=3)

    devices = _connected_devices()
    if not devices:
        pytest.exit("No phone in `adb devices`. Reconnect wireless debugging first.", returncode=3)
    udid = str(config.get("DEVICE_ID") or "")
    if udid not in devices:
        udid = devices[0]

    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.automation_name = "UiAutomator2"
    opts.udid = udid
    opts.app_package = config["APP_ID"]
    opts.app_activity = config.get("APP_ACTIVITY", "com.connection.crm.MainActivity")
    opts.no_reset = True                     # keep the signed-in session and app data
    opts.auto_grant_permissions = True
    opts.new_command_timeout = 300
    drv = webdriver.Remote(url, options=opts)
    drv.implicitly_wait(0)                   # pages/ use explicit polling waits
    yield drv
    drv.quit()


@pytest.fixture(autouse=True)
def _app_in_front(request, config):
    """Bring the staging app to the front before each test that uses the driver."""
    if "driver" in request.fixturenames:
        drv = request.getfixturevalue("driver")
        drv.activate_app(config["APP_ID"])
        time.sleep(2)
    yield


def _case_id(nodeid):
    m = re.search(r"test_(tc\d+)", nodeid, re.IGNORECASE)
    return m.group(1).upper() if m else "misc"


@pytest.fixture
def evidence(request, driver):
    """evidence("01_job_page") -> screenshots/TC03/01_job_page.png; returns the path."""
    folder = SCREENSHOTS / _case_id(request.node.nodeid)
    folder.mkdir(parents=True, exist_ok=True)
    taken = []

    def shoot(name):
        path = folder / f"{name}.png"
        driver.save_screenshot(str(path))
        taken.append(path)
        return path

    shoot.taken = taken
    return shoot


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed and "driver" in item.fixturenames:
        drv = item.funcargs.get("driver")
        if drv is not None:
            folder = SCREENSHOTS / _case_id(item.nodeid)
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"FAILED_{time.strftime('%Y%m%d_%H%M%S')}.png"
            try:
                drv.save_screenshot(str(path))
                report.sections.append(("failure screenshot", str(path)))
            except Exception as e:  # session may already be gone
                report.sections.append(("failure screenshot", f"could not save: {e}"))
