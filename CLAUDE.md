# CLAUDE.md — Mobile test automation for Module Action Lock (App)

You are helping a QA engineer automate manual test cases for the Caction Android app
(**Caction Staging**, package `com.connection.crm.dev`).
The phone is connected over **ADB wireless debugging**. Tests are written in **Python + pytest** and
drive the app through **Appium** (UiAutomator2 driver).

## Project layout

```
.
├── CLAUDE.md                     # this file
├── SETUP.md                      # one-time install and connection steps
├── config.yaml                   # app id, Appium URL, accounts, test data (filled in by the user)
├── requirements.txt              # Appium-Python-Client, pytest, pyyaml
├── conftest.py                   # loads config.yaml, creates the driver, screenshot on failure
├── pages/                        # shared steps (session/login check, logout, open_job, ...)
├── tools/
│   └── dump_screen.py            # saves page source + screenshot of the current screen
├── testcases/
│   └── Module_Action_Lock_App_Test_cases.csv   # source of truth (do not edit)
├── tests/
│   └── test_tc03_job_block_all_chip.py         # one test file per test case
├── screenshots/                  # evidence, one folder per test case (TC03/, TC04/, ...)
└── results/
    └── results.csv               # run results, written by you
```

## Lock names on staging

Status Settings → **Mode** on staging uses different names from the spec:

| Staging Mode | Spec lock value | Note |
|---|---|---|
| Normal | No lock | |
| Pause | Block creation / Block all | **Not confirmed yet** which of the two. Say so in Notes for any case that relies on it. |
| Terminate | Freeze | Customer and Project only |

When a test case says "Block all" or "Freeze", the user sets the matching staging Mode on web.

## Ground rules

1. **The CSV is the source of truth.** Read the Scenario, Preconditions, Steps and Expected Result
   of a test case before writing its test. Never change the CSV.
2. **One test case = one test file**, named `tests/test_tcXX_<short_snake_name>.py`, matching the
   CSV row number (row 1 = TC01). Put the full Scenario title in the module docstring, and the
   test function's docstring.
3. **Every numbered Expected Result line must become an assertion** (`assert` with a clear
   message). If one can't be asserted automatically (for example "greyed" or "keeps its own icon"),
   write a `# MANUAL CHECK: <expected line>` comment and save a screenshot at that moment.
   Label each block with its line, e.g. `# Expected 4: ...`.
4. **Never guess locators.** Before writing taps for a new screen, inspect the real UI:
   - `python tools/dump_screen.py <name>` (saves `driver.page_source` + screenshot), or
   - `adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml`
   This is a **Flutter app**: most elements have no `resource-id`. Locator order:
   1. `AppiumBy.ACCESSIBILITY_ID` (the app puts ids such as `more_btn`, `opt_edit`, `schedule_0`
      in `content-desc`)
   2. exact visible text (`//*[@text="…"]` or `@content-desc="…"`)
   3. XPath with `starts-with(@content-desc, …)` / `contains(…)`. Flutter often merges a card's
      texts into one `content-desc` joined by newlines (e.g. `J00297 - Site Visit\n…`)
   4. Screen coordinates only as a last resort, with a comment saying why.
   Some content is **not exposed at all** (e.g. the text and icons on Schedule job cards). Don't
   invent a locator for it: make it a MANUAL CHECK with a screenshot.
5. **Reuse, don't repeat.** Checking who is signed in, logout, switching role, opening a
   Job/Project/Customer/Form by ID go into `pages/` and are imported by the tests. Write a page
   helper only after inspecting the real screens it uses.
6. **Read accounts and record IDs from `config.yaml`** through the `config` fixture. Never
   hard-code account details or record IDs in test files.
   **Passwords:** Claude does not type passwords into the app. `pages/session.py` checks which
   account is signed in (Profile e-mail) and, if it isn't the one the test needs, the test stops
   (`pytest.skip`) and asks the user to sign in on the phone.
7. **Toasts disappear quickly.** Look for them straight after the tap that triggers them, with a
   short explicit wait (about 3 s, polling), and take a screenshot.
8. **Don't change data you weren't asked to change.** Only use the test records listed in
   `config.yaml`. Never delete, bulk edit or change status on other records. If a step only needs
   to *check* an action is blocked or allowed, open it and back out without saving.
9. **Preconditions on web/admin are out of scope for the app tests.** If a test case needs a
   Status Settings lock or a feature flag, don't automate it on the phone: the test checks
   `config.yaml > preconditions_ready` and skips with the exact web setup needed if it isn't
   `true`. When that happens, stop and tell the user what to set up on web.
10. **Never change a test just to make it pass.** A failing assertion that matches what the app
    really does is a Failed result, not a locator problem.

## Workflow for each test case

1. Read the row in the CSV. Summarise in 2–3 lines what the test will do.
2. Check the device: `adb devices` must show the phone as `device`. If not, ask the user to
   reconnect (see "Connection" below).
3. Check the Appium server: `http://127.0.0.1:4723/status` must return `ready: true`.
4. Inspect the screens involved (rule 4).
5. Write the test file. **Show it to the user before running it.**
6. Run it: `python -m pytest tests/test_tcXX_*.py -v --junitxml=results/TCxx.xml`
7. If it fails:
   - Locator/timing problem → fix the test and run again (max 3 attempts).
   - The app behaves differently from Expected Result → **don't "fix" the test to make it pass.**
     Record it as Failed, with the actual behaviour and a screenshot (conftest saves one on failure).
8. Append a row to `results/results.csv`:
   `Scenario,Status,Actual Result,Screenshot,Notes`
   - Status is one of: `Passed`, `Failed`, `Blocked` (preconditions/data missing), `Manual` (can't be automated).
   - Actual Result: one or two plain sentences on what the app actually did.
   - Screenshot: path(s) under `screenshots/TCxx/`.
   - A run with MANUAL CHECKs is `Passed` only after the user confirms the screenshots;
     until then record the automated part and say "manual check pending" in Notes.
9. Move to the next test case only when the user says so, unless they asked for a batch run.

## Test cases that are NOT fully automatable — mark as Manual or partial

- **Two users at once** (record locked by another user while the page is open): automate only the
  phone side, after the user has changed the status on web, and say so in Notes.
- **Offline sync**: toggling the network is possible with `adb shell svc wifi disable/enable`, but
  **ask the user first**, because wireless debugging drops when Wi-Fi turns off. Default to Manual.
- **Smart To-do / automation behaviour**: check the visible result only; the server-side log is
  out of reach.
- **Status Settings (web only)**: never on the app.
- **Visual-only results** (greyed controls, icons, colours): MANUAL CHECK + screenshot.

## Phone notes (Xiaomi / MIUI)

- MIUI blocks installing apps over USB/adb without a SIM card ("Install via USB"), so tools that
  install a helper app on every run don't work here. Appium's UiAutomator2 server apps are already
  installed on the phone; keep `noReset: true` and don't uninstall them.
- Some apps don't come to the front when started in the background; if a session starts on the
  launcher, start the app with `adb shell am start -n com.connection.crm.dev/com.connection.crm.MainActivity`.

## Connection (wireless debugging)

The user's phone: Developer options → Wireless debugging → "Pair device with pairing code".
```
adb pair <PHONE_IP>:<PAIRING_PORT>      # enter the 6-digit code
adb connect <PHONE_IP>:<CONNECT_PORT>   # the port shown on the Wireless debugging screen
adb devices                             # note the device id
```
The connect port changes when wireless debugging restarts. `adb mdns services` often finds the
phone again on its own. If `adb devices` is still empty, ask the user for the new port instead of
retrying blindly.

## Test template

```python
"""TC03 - Job in Block all status shows Locked chip and greyed controls"""
import pytest

from pages.job import JobPage
from pages.session import require_account


def test_tc03_job_block_all_chip(driver, config, evidence):
    """TC03 - Job in Block all status shows Locked chip and greyed controls"""
    require_account(driver, config, "user")
    if not config["preconditions_ready"]["job_completed_block_all"]:
        pytest.skip("Set Job status Completed = Block all (Override Admin only) on web first")

    job = JobPage(driver).open(config["records"]["locked_job_id"])

    # Expected 1: 'Locked' chip shown beside Edit
    assert job.has_text("Locked"), "No 'Locked' chip on the job page"
    evidence("01_job_page")
    # MANUAL CHECK: buttons greyed but keep their own icon — see 01_job_page.png
```

## Reporting at the end of a run

Give the user a short summary: how many Passed / Failed / Blocked / Manual, then list each
Failed case with its Actual Result in one line. The user copies Status and Actual Result into Notion.
