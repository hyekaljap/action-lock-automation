"""Customer and Project pages.

Screens inspected (26 Nov 2026, app 3.8.19, technician account, customer C00109 / project P00031):
  Customer tab: list customer_0, customer_1, ...; cust_quick_search; add_cust_floating.
                (Typing in cust_quick_search did not filter the list, so cards are opened in turn.)
  Customer page: header "<name>\n<ID> - <category>"; back_btn; more_btn; status_bar_btn_<status>;
                tabs "tab_details, Tab 1 of 5", "tab_metrics, ...", "tab_deal, Tab 3 of 5",
                "tab_job, Tab 4 of 5", "tab_comment, Tab 5 of 5"; main_fab (+) / close_fab.
                ⋯ menu: opt_cust_status, opt_duty_roster, opt_edit, opt_generate_qr, opt_add_pf,
                opt_share_link, opt_refresh.  (+) menu: Add Project, Add Job, Add Public Form.
                Back while the (+) menu is open LEAVES the page: close it with close_fab.
                main_fab only shows on the Details tab.
                Add Project -> "Create Project" form (save_btn); back -> "Your Project details
                have not been saved." cancel_btn / confirm_btn (Yes = leave without saving).
                Edit and Change status show "Authority Required" for the technician.
  Projects tab: deal_0, deal_1, ...; search_bar_deal; add_deal_btn.
  Project page: optional "Change Status" suggestion (Later); header "Project Details\n<ID> - <cat>";
                back-btn; more_btn; status_bar_btn_<status>; tabs "tab_details, Tab 1 of 3",
                "tab_metrics, Tab 2 of 3", "tab_job, Tab 3 of 3"; comment_textfield; main_fab.
                ⋯ menu: opt_deal_status, opt_duty_roster, opt_edit, opt_copy, opt_default,
                opt_share_link, opt_generate_qr, opt_add_pf, opt_alert, opt_tutorial, opt_refresh.
                (+) menu: Add Job, Add Public Form.  Add Job -> "Select Category" (back cancels).
"""
import time

from pages.record import RecordPage

MAX_CARDS = 20


class CustomerPage(RecordPage):
    BACK_ID = "back_btn"

    def is_open(self, customer_id, timeout=8):
        return self.has_text(f"{customer_id} - ", timeout=timeout)

    def open(self, customer_id):
        self.tap_id("customer")
        for i in range(MAX_CARDS):
            card = self.by_id(f"customer_{i}", timeout=5)
            if card is None:
                self.swipe_up()
                card = self.by_id(f"customer_{i}", timeout=3)
            if card is None:
                break
            card.click()
            time.sleep(2)
            if self.is_open(customer_id):
                return self
            self.tap_id(self.BACK_ID)
        raise AssertionError(f"Customer {customer_id} not found in this account's customer list")


class ProjectPage(RecordPage):
    BACK_ID = "back-btn"

    def is_open(self, project_id, timeout=8):
        return self.has_text(f"{project_id} - ", timeout=timeout)

    def open(self, customer_id, project_id):
        """Open project_id from its customer's Projects tab."""
        CustomerPage(self.d).open(customer_id)
        self.tap_id("tab_deal, Tab 3 of 5")
        for i in range(MAX_CARDS):
            card = self.by_id(f"deal_{i}", timeout=5)
            if card is None:
                break
            card.click()
            time.sleep(2)
            if self.by_text("Change to Next Status", timeout=3):
                self.tap_text_if_present("Later")
            if self.is_open(project_id):
                return self
            self.tap_id(self.BACK_ID)
        raise AssertionError(f"Project {project_id} not found under customer {customer_id}")
