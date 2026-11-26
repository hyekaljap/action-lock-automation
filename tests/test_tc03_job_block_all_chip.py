"""TC03 - Job in Block all status shows Locked chip and greyed controls

CSV row 3. Job whose own status is set to Block all is locked for a non-override role; controls
stay visible but greyed (AC-15, FR-06).

Preconditions (web, by the user):
  1. Job status Completed = Block all (staging Mode: Pause, not confirmed), Override = Admin only
  2. Job config.records.locked_job_id is Completed
  3. Signed in on the app as the User account (config.accounts.user)

Locator notes:
  - Edit is inside the ⋯ menu on mobile (opt_edit); there is no separate Edit button.
  - The lock chip and toast couldn't be inspected (Action Lock was off), so they are matched
    on the spec's wording ("Locked", "Locked: you can't edit details. ..."). Re-check with
    tools/dump_screen.py the first time the lock is on, before trusting a failure here.
  - No (+) button was found on the job page for the technician account, so "(+) is hidden"
    is a MANUAL CHECK.
  - Flutter reports every control as enabled, so "greyed" is a MANUAL CHECK.
Nothing is saved: Edit is only tapped to see the toast; if the editor opens, it's left unsaved.
"""
import pytest

from pages.job import JobPage
from pages.session import require_account

EDIT_TOAST = "Locked: you can't edit details."
EDIT_TOAST_REASON = "Completed status is locked."


def test_tc03_job_block_all_chip(driver, config, evidence):
    """TC03 - Job in Block all status shows Locked chip and greyed controls"""
    ready = config.get("preconditions_ready") or {}
    if not (ready.get("feature_flag_on") and ready.get("job_completed_block_all")):
        pytest.skip("Web setup needed: switch Action Lock on for the company, set Job status "
                    "Completed = Block all (Override = Admin only), put the job in "
                    "config.records.locked_job_id into Completed, then set "
                    "preconditions_ready.feature_flag_on and .job_completed_block_all to true.")
    require_account(driver, config, "user")

    job_id = config["records"]["locked_job_id"]
    job = JobPage(driver)
    try:
        # Step 1: Open the job
        job.open(job_id)

        # Step 2 / Expected 1: 'Locked' chip shown beside Edit
        evidence("01_job_page")
        assert job.has_text("Locked", timeout=5), "Expected 1: no 'Locked' chip on the job page"
        # MANUAL CHECK: Expected 1 - the chip sits in the header beside Edit (⋯) - see 01_job_page.png

        # Step 3 / Expected 2: locked buttons are greyed, visible and keep their own icon
        assert job.by_id("tapopen_float", timeout=3) is not None, \
            "Expected 2: Check-in button is not visible"
        job.open_more_menu()
        evidence("02_more_menu")
        for item in ("opt_edit", "opt_copy"):
            assert job.by_id(item, timeout=3) is not None, f"Expected 2: '{item}' is not visible"
        # MANUAL CHECK: Expected 2 - Edit, Change status, Assign, Copy, Delete, Check-in are greyed
        #   and keep their own icon, with no lock icon on the buttons - see 01_job_page.png and
        #   02_more_menu.png (Assign/Delete aren't in this account's menu; note it if still absent)

        # Expected 3: (+) button is hidden because all its items are locked
        # MANUAL CHECK: Expected 3 - no (+) create button on the job page - see 01_job_page.png

        # Step 4 / Expected 4: tapping Edit shows the lock toast
        job.tap_id("opt_edit", settle=0)
        toast_seen = job.wait_text(EDIT_TOAST, timeout=3)
        reason_seen = job.has_text(EDIT_TOAST_REASON)
        evidence("03_edit_toast")
        editor_opened = job.by_id("save_btn", timeout=1) is not None
        if editor_opened:
            job.leave_edit_without_saving()
        assert not editor_opened, "Expected 4: Edit opened the editor instead of being blocked"
        assert toast_seen and reason_seen, (
            f'Expected 4: toast "{EDIT_TOAST} {EDIT_TOAST_REASON}" not seen within 3 s')

        # Expected 5: status pill shows a lock icon
        assert job.status_pill(timeout=5) is not None, "Expected 5: status pill not found"
        evidence("04_status_pill")
        # MANUAL CHECK: Expected 5 - lock icon on the status pill (icon not exposed) - see 04_status_pill.png
    finally:
        try:
            job.back()
            job.restore_schedule_filter()
        except Exception:
            pass
