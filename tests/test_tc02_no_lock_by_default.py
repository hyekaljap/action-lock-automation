"""TC02 - No status is locked by default after enabling the feature

CSV row 2. Every status starts at No lock for new and existing companies; nothing is migrated or
seeded (AC-30, BR-18).

Preconditions (web, by the admin):
  1. enable_action_lock switched ON for the company        -> preconditions_ready.feature_flag_on
  2. No status has a lock (every Status Settings Mode = Normal) -> preconditions_ready.no_locks_set
  3. Logged in on app as User. The user asked for this run as the technician account, so
     RUN_AS = "technician"; the technician has no Edit / Change status authority on customers.

Steps: open a Customer, Project, Job and Digital Form; try edit, change status, post update and
create. Every action is opened and backed out of: nothing is saved, changed, sent or created.

Expected 1 (no lock chip) and Expected 2 (actions work as before) are checked on each record.
"As before" = the action opens, or shows the existing "Authority Required" role dialog (that
dialog is the pre-existing permission, not Action Lock, and is reported in the notes).
"""
import pytest

from pages.customer import CustomerPage, ProjectPage
from pages.job import JobPage
from pages.session import require_account

RUN_AS = "technician"            # CSV says User; this run was requested as the technician
AS_BEFORE = ("opened", "no_authority")


@pytest.fixture
def ready(driver, config):
    flags = config.get("preconditions_ready") or {}
    if not (flags.get("feature_flag_on") and flags.get("no_locks_set")):
        pytest.skip("Web setup needed: switch Action Lock on for the company, set every status "
                    "(Customer, Project, Job, Digital Form) to Mode = Normal, then set "
                    "preconditions_ready.feature_flag_on and .no_locks_set to true.")
    require_account(driver, config, RUN_AS)
    return config["records"]


def _check(results, record_property, record):
    """Expected 2: each action behaved as before; collect role-permission notes."""
    notes = [f"{record} {action}: Authority Required (role permission, not a lock)"
             for action, outcome in results.items() if outcome == "no_authority"]
    for n in notes:
        print("NOTE:", n)
    record_property(f"{record}_outcomes", results)
    bad = {a: o for a, o in results.items() if o not in AS_BEFORE}
    assert not bad, f"Expected 2: {record} actions not working as before: {bad}"


def test_tc02_customer(driver, ready, evidence, record_property):
    """TC02 - No status is locked by default after enabling the feature (Customer)"""
    page = CustomerPage(driver).open(ready["tc02_customer_id"])
    evidence("01_customer")
    # Expected 1: no lock chip
    assert not page.lock_shown(), "Expected 1: lock chip/text on the customer page"
    results = {
        "edit": page.try_edit(),
        "change_status": page.try_change_status(),
        # Customer has no updates in the spec (FR-03), so no post update here
        # (+) > Add Project opens "Create Project"; left via back + "not been saved" > Yes
        "create_project": page.try_create("Add Project", "Create Project"),
    }
    evidence("02_customer_after_actions")
    page.tap_id_if_present(CustomerPage.BACK_ID)
    _check(results, record_property, "Customer")


def test_tc02_project(driver, ready, evidence, record_property):
    """TC02 - No status is locked by default after enabling the feature (Project)"""
    page = ProjectPage(driver).open(ready["tc02_customer_id"], ready["tc02_project_id"])
    evidence("03_project")
    # Expected 1: no lock chip
    assert not page.lock_shown(), "Expected 1: lock chip/text on the project page"
    results = {
        "edit": page.try_edit(),
        "change_status": page.try_change_status(),
        "post_update": page.try_post_update(),
        "create_job": page.try_create("Add Job", "Select Category"),
    }
    evidence("04_project_after_actions")
    page.tap_id_if_present(ProjectPage.BACK_ID)
    page.tap_id_if_present(CustomerPage.BACK_ID)
    _check(results, record_property, "Project")


def test_tc02_job(driver, ready, evidence, record_property):
    """TC02 - No status is locked by default after enabling the feature (Job)"""
    page = JobPage(driver)
    try:
        page.open(ready["tc02_job_id"])
        evidence("05_job")
        # Expected 1: no lock chip
        assert not page.lock_shown(), "Expected 1: lock chip/text on the job page"
        results = {
            "edit": page.try_edit(),
            "change_status": page.try_change_status(),
            "post_update": page.try_post_update(),
            # No (+) create menu on the job page for the technician account (inspected)
        }
        evidence("06_job_after_actions")
        _check(results, record_property, "Job")
    finally:
        page.tap_id_if_present(JobPage.BACK_ID)
        page.restore_schedule_filter()


def test_tc02_digital_form(driver, ready):
    """TC02 - No status is locked by default after enabling the feature (Digital Form)"""
    if not ready.get("tc02_form_id"):
        pytest.skip("No Digital Form yet: J00297 has none. Create one the technician can open, put "
                    "its ID in records.tc02_form_id, and Claude will inspect the form screens.")
    pytest.skip("Digital Form screens not inspected yet (rule 4): inspect, then write this part.")
