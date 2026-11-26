"""Actions shared by Customer, Project and Job pages.

Each try_* method opens an action, records what the app did, then backs out WITHOUT saving,
changing a status or sending anything.

Outcomes, inspected 26 Nov 2026 (app 3.8.19, technician account):
  - "opened":     the action's own screen appeared (editor, Select Status, Select Category, ...)
  - "no_authority": "Authority Required / Please contact your admin for permission" dialog
                  (close_btn). That's the existing role permission, NOT Action Lock.
  - "locked":     a lock toast/chip text appeared (spec wording "Locked", "New work blocked").
                  Not inspected yet (Action Lock was off); matched on the spec's text.
  - "unknown":    none of the above within the wait.
"""
import time

from pages.base import BasePage

LOCK_TEXTS = ("Locked", "New work blocked")
AUTHORITY_TEXT = "Authority Required"


class RecordPage(BasePage):
    BACK_ID = "back-btn"            # Job and Project pages; Customer page uses "back_btn"

    def lock_shown(self):
        return any(self.has_text(t) for t in LOCK_TEXTS)

    def _outcome(self, opened_id, timeout=5):
        end = time.time() + timeout
        while time.time() < end:
            if self.by_id(opened_id, timeout=0) is not None or self.by_text(opened_id, timeout=0):
                return "opened"
            if self.has_text(AUTHORITY_TEXT):
                return "no_authority"
            if self.has_text("Locked:") or self.lock_shown():
                return "locked"
            time.sleep(0.4)
        return "unknown"

    def _close_authority_dialog(self):
        self.tap_id_if_present("close_btn", timeout=2)

    # --- actions -------------------------------------------------------------
    def try_edit(self):
        """⋯ > Edit. Leaves the editor without saving."""
        self.tap_id("more_btn")
        self.tap_id("opt_edit", settle=0)
        result = self._outcome("save_btn")
        if result == "opened":
            self.back()
            self.tap_id_if_present("confirm_btn")      # "...not been saved." -> Yes, leave
        elif result == "no_authority":
            self._close_authority_dialog()
        return result

    def try_change_status(self):
        """Opens the status picker from the status pill, closes it without choosing."""
        pill = self.by_prefix("status_bar_btn_")
        assert pill is not None, "status pill not found"
        pill.click()
        result = self._outcome("Select Status")
        if result == "opened":
            self.back()
        elif result == "no_authority":
            self._close_authority_dialog()
        return result

    def try_post_update(self):
        """Opens the comment box (Category field appears), closes it without sending."""
        self.tap_id("comment_textfield", settle=0)
        result = self._outcome("Category")
        if result == "opened":
            if not self.tap_id_if_present("close_comment_btn"):
                self.back()
        return result

    def create_menu_items(self, items):
        """Opens the (+) create menu (main_fab), returns which of `items` are listed, closes it."""
        self.tap_id("main_fab")
        found = [i for i in items if self.by_text(i, timeout=2) is not None]
        self.tap_id_if_present("close_fab")             # back would leave the page
        return found

    def try_create(self, menu_item, first_screen):
        """(+) > menu_item, checks its first screen opens, backs out before anything is created."""
        self.tap_id("main_fab")
        el = self.by_text(menu_item, timeout=3)
        assert el is not None, f"'{menu_item}' not in the (+) menu"
        el.click()
        result = self._outcome(first_screen)
        if result == "opened":
            self.back()                                   # cancels the picker / form
            self.tap_id_if_present("confirm_btn")         # "...not been saved." -> Yes, leave
        elif result == "no_authority":
            self._close_authority_dialog()
        return result
