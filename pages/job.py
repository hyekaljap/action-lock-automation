"""Opening a Job by ID, and the Job page's controls.

Screens inspected (26 Nov 2026, app 3.8.19, job J00297):
  Bottom tabs:  dashboard, metric, schedule, customer, notification
  Schedule:     job cards schedule_0, schedule_1, ...; filter button configfavfilter_sch.
                The card's own text and icons are NOT exposed (screenshot only).
  Job Filter:   filter_by_date -> "Select Date Range" list date_range_0..11
                (0 = Daily, 1 = Most Recent (+-6 months)); seqno_min / seqno_max; reset; search.
                The JOB SEQ NO filter did not narrow results reliably, so it isn't used.
  On open:      optional "Change Status" suggestion with "Later" / "Change to Next Status".
  Job page:     header "J00297 - Site Visit\n<customer>" (content-desc starts with "<ID> - ");
                back-btn; more_btn; status pill status_bar_btn_<status>;
                tabs tab_detail / tab_todolist / tab_comment / tab_digital_form;
                tapopen_float = check-in/out dialog (close_dialog, checkin_out_btn);
                scroll_to_todo_list; comment_textfield.
  ⋯ menu:       opt_job_status, opt_duty_roster, opt_edit, opt_copy, opt_share_detail,
                opt_share_link, opt_generate_qr, opt_link_qr, opt_add_pf, opt_alert,
                opt_tutorial, opt_refresh  (no Delete / Assign for the technician account).
  Edit Job:     save_btn, change_customer, change_deal; back -> "Your Job details have not been
                saved." with cancel_btn / confirm_btn (Yes = leave without saving).
NOT inspected yet (Action Lock wasn't on): lock chip, lock toast, (+) create button.
"""
import time

from pages.record import RecordPage

DATE_RANGE_DAILY = "date_range_0"
DATE_RANGE_MOST_RECENT = "date_range_1"     # "Most Recent (+-6 months)"
MAX_CARDS = 15


class JobPage(RecordPage):
    """Job page. No (+) create menu was found on it for the technician account."""

    # --- opening -----------------------------------------------------------
    def _set_schedule_range(self, range_id):
        self.tap_id("schedule")
        self.tap_id("configfavfilter_sch")
        self.tap_id("filter_by_date")
        self.tap_id(range_id)
        self.tap_id("search")

    def restore_schedule_filter(self):
        """Put the Schedule filter back to the default (Daily, no other filters)."""
        self.tap_id("schedule")
        self.tap_id("configfavfilter_sch")
        self.tap_id("reset")
        self.tap_id("search")

    def _dismiss_status_suggestion(self):
        if self.by_text("Change to Next Status", timeout=3):
            self.tap_text_if_present("Later")

    def is_open(self, job_id, timeout=10):
        return self.by_prefix(f"{job_id} - ", timeout) is not None

    def open(self, job_id):
        """Open job_id from the Schedule (Most Recent +-6 months).

        Card text isn't exposed, so each card is opened in turn until the job page header
        matches. Opening a job changes nothing. Call restore_schedule_filter() afterwards.
        """
        self._set_schedule_range(DATE_RANGE_MOST_RECENT)
        for i in range(MAX_CARDS):
            card = self.by_id(f"schedule_{i}", timeout=5)
            if card is None:
                self.swipe_up()
                card = self.by_id(f"schedule_{i}", timeout=3)
            if card is None:
                break
            card.click()
            time.sleep(2)
            self._dismiss_status_suggestion()
            if self.is_open(job_id, timeout=8):
                return self
            self.tap_id("back-btn")
        raise AssertionError(
            f"Job {job_id} not found in the first {MAX_CARDS} jobs of Schedule > Most Recent "
            f"(+-6 months). Is it assigned to this account and dated within 6 months?")

    # --- job page controls ---------------------------------------------------
    def status_pill(self, timeout=10):
        return self.by_prefix("status_bar_btn_", timeout)

    def open_more_menu(self):
        self.tap_id("more_btn")

    def close_more_menu(self):
        self.back()

    def leave_edit_without_saving(self):
        self.back()
        self.tap_id_if_present("confirm_btn")   # "Your Job details have not been saved." -> Yes
