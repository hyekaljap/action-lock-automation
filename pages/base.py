"""Locator helpers for the Caction Flutter app.

The app exposes its ids in content-desc (accessibility id), e.g. "more_btn", "schedule_0".
Flutter reports every node as clickable="false" enabled="true", so "greyed out" can't be read
from attributes: treat it as a MANUAL CHECK with a screenshot.
"""
import time

from appium.webdriver.common.appiumby import AppiumBy


class BasePage:
    def __init__(self, driver):
        self.d = driver

    # --- finding -----------------------------------------------------------
    def _poll(self, by, value, timeout):
        end = time.time() + timeout
        while True:
            els = self.d.find_elements(by, value)
            if els:
                return els[0]
            if time.time() >= end:
                return None
            time.sleep(0.4)

    def by_id(self, acc_id, timeout=10):
        """Element whose content-desc is exactly acc_id (the app's ids)."""
        return self._poll(AppiumBy.ACCESSIBILITY_ID, acc_id, timeout)

    def by_text(self, text, timeout=10):
        """Element whose visible text or content-desc is exactly text."""
        return self._poll(AppiumBy.XPATH, f'//*[@text="{text}" or @content-desc="{text}"]', timeout)

    def by_prefix(self, prefix, timeout=10):
        """Element whose content-desc/text starts with prefix (Flutter merges texts with newlines)."""
        xp = f'//*[starts-with(@content-desc,"{prefix}") or starts-with(@text,"{prefix}")]'
        return self._poll(AppiumBy.XPATH, xp, timeout)

    def has_text(self, text, timeout=0):
        """True if any element's content-desc or text contains text."""
        xp = f'//*[contains(@content-desc,"{text}") or contains(@text,"{text}")]'
        return self._poll(AppiumBy.XPATH, xp, timeout) is not None

    def wait_text(self, text, timeout=3):
        """Poll for a short-lived text such as a toast; True if seen within timeout."""
        return self.has_text(text, timeout=timeout)

    # --- acting ------------------------------------------------------------
    def tap_id(self, acc_id, timeout=10, settle=1.5):
        el = self.by_id(acc_id, timeout)
        assert el is not None, f"'{acc_id}' not found on screen"
        el.click()
        time.sleep(settle)

    def tap_id_if_present(self, acc_id, timeout=3, settle=1.5):
        el = self.by_id(acc_id, timeout)
        if el is None:
            return False
        el.click()
        time.sleep(settle)
        return True

    def tap_text_if_present(self, text, timeout=3, settle=1.5):
        el = self.by_text(text, timeout)
        if el is None:
            return False
        el.click()
        time.sleep(settle)
        return True

    def back(self, settle=1.5):
        self.d.back()
        time.sleep(settle)

    def swipe_up(self, settle=1.0):
        size = self.d.get_window_size()
        x = size["width"] // 2
        self.d.swipe(x, int(size["height"] * 0.75), x, int(size["height"] * 0.35), 400)
        time.sleep(settle)
