"""Who is signed in, and signing out.

Claude never types passwords, so there is no automated login: if the wrong account (or none)
is signed in, the test is skipped with a message asking the user to sign in on the phone.

Screens inspected (26 Nov 2026, app 3.8.19):
  Home:     go_to_profile, dashboard (Home tab)
  Profile:  e-mail shown as plain text under "Email Address"; profile_backbutton; switch_account
  Switch Account sheet: "Select Account" + one row "select_account" per account. The row's
            "Sign Out" button is NOT exposed as its own element.
  Login:    email_select, phone_select, email_address, password_field, login_button
"""
import re
import time

import pytest

from pages.base import BasePage

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Session(BasePage):
    def on_login_screen(self, timeout=3):
        return self.by_id("login_button", timeout) is not None

    def go_home(self):
        # The Home tab is "dashboard". From a sub page, back out first.
        for _ in range(4):
            if self.by_id("dashboard", timeout=2):
                break
            self.back()
        self.tap_id("dashboard")

    def signed_in_email(self):
        """E-mail of the signed-in account, read from Profile. None if on the login screen."""
        if self.on_login_screen():
            return None
        self.go_home()
        self.tap_id("go_to_profile")
        email = None
        for el in self.d.find_elements("xpath", "//*[@content-desc or @text]"):
            value = (el.get_attribute("content-desc") or el.text or "").strip()
            if EMAIL_RE.match(value):
                email = value
                break
        self.tap_id_if_present("profile_backbutton")
        return email

    def logout(self):
        """Sign out the current account.

        Partly inspected: the Sign Out button sits at the right end of the "select_account" row
        and isn't exposed as an element, so it is tapped by position inside that row (last
        resort, see CLAUDE.md rule 4). What appears after tapping it (confirm dialog or straight
        to login) has NOT been inspected yet; this asserts the login screen and fails clearly
        otherwise. Inspect and finish this before using it in a test.
        """
        self.go_home()
        self.tap_id("go_to_profile")
        self.tap_id("switch_account")
        row = self.by_id("select_account")
        assert row is not None, "Select Account sheet didn't open"
        r = row.rect
        # Sign Out button: right ~20% of the row, vertically centred.
        self.d.tap([(r["x"] + int(r["width"] * 0.88), r["y"] + r["height"] // 2)], 100)
        time.sleep(3)
        assert self.on_login_screen(timeout=10), (
            "After Sign Out the login screen didn't appear (an uninspected confirm dialog?). "
            "Inspect this screen and finish Session.logout()."
        )


def require_account(driver, config, role):
    """Skip the test unless the account for `role` (config.yaml > accounts) is signed in."""
    wanted = ((config.get("accounts") or {}).get(role) or {}).get("username") or ""
    if not wanted:
        pytest.skip(f"config.yaml > accounts > {role} > username is empty. "
                    f"Add the {role} account's e-mail (as shown on the app's Profile).")
    current = Session(driver).signed_in_email()
    if (current or "").lower() != wanted.lower():
        pytest.skip(f"Needs the {role} account ({wanted}) signed in on the phone; "
                    f"currently signed in: {current or 'nobody'}. Sign in on the phone and rerun.")
