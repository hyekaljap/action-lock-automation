# CLAUDE.md — Mobile test automation for Module Action Lock (App)

You are helping a QA engineer automate manual test cases for the Caction Android app.
The phone is connected over **ADB wireless debugging**. Tests are written and run with **Maestro**.

## Project layout

```
.
├── CLAUDE.md                     # this file
├── config.yaml                   # app id, accounts, test data (filled in by the user)
├── testcases/
│   └── Module_Action_Lock_App_Test_Cases.csv   # source of truth (do not edit)
├── flows/
│   ├── common/                   # reusable sub-flows (login, logout, open_job, ...)
│   └── TC03_job_block_all_chip.yaml            # one flow per test case
├── screenshots/                  # evidence, one folder per test case
└── results/
    └── results.csv               # run results, written by you
```

## Ground rules

1. **The CSV is the source of truth.** Read the Scenario, Preconditions, Steps and Expected Result
   of a test case before writing its flow. Never change the CSV.
2. **One test case = one flow file**, named `TCxx_<short_snake_name>.yaml`, matching the CSV row
   number (row 1 = TC01). Put the full Scenario title in a comment at the top of the file.
3. **Every numbered Expected Result line must become an assertion** (`assertVisible`,
   `assertNotVisible`, or a screenshot check). If one can't be asserted automatically, add a
   `# MANUAL CHECK:` comment and take a screenshot at that moment.
4. **Never guess selectors.** Before writing taps for a new screen, inspect the real UI:
   - `maestro hierarchy` (preferred), or
   - `adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml`
   Prefer `id:` selectors, then exact visible text, then relative selectors (`below:`, `rightOf:`).
   Use tap points only as a last resort, and comment why.
5. **Reuse, don't repeat.** Login, logout, switching role, opening a Job/Project/Customer/Form by
   ID go into `flows/common/` and are called with `runFlow`.
6. **Read accounts and record IDs from `config.yaml`.** Pass them to flows with `env:`.
   Never hard-code passwords in flow files.
7. **Toasts disappear quickly.** Assert them straight after the tap that triggers them, using
   `extendedWaitUntil` with a short timeout (about 3000 ms), and take a screenshot.
8. **Don't change data you weren't asked to change.** Only use the test records listed in
   `config.yaml`. Never delete, bulk edit or change status on other records.
9. **Preconditions on web/admin are out of scope for the app flows.** If a test case needs a
   Status Settings lock (Block creation, Block all, Freeze) or a feature flag, don't automate it on
   the phone: check `config.yaml > preconditions_ready`. If it isn't marked ready, stop and tell the
   user exactly what to set up on web.

## Workflow for each test case

1. Read the row in the CSV. Summarise in 2–3 lines what the flow will do.
2. Check the device: `adb devices` must show the phone as `device`. If not, ask the user to
   reconnect (see "Connection" below).
3. Inspect the screens involved (rule 4).
4. Write the flow file.
5. Run it: `maestro --device <DEVICE_ID> test flows/TCxx_*.yaml --format junit --output results/TCxx.xml`
6. If it fails:
   - Selector/timing problem → fix the flow and run again (max 3 attempts).
   - The app behaves differently from Expected Result → **don't "fix" the flow to make it pass.**
     Record it as Failed, with the actual behaviour and a screenshot.
7. Append a row to `results/results.csv`:
   `Scenario,Status,Actual Result,Screenshot,Notes`
   - Status is one of: `Passed`, `Failed`, `Blocked` (preconditions/data missing), `Manual` (can't be automated).
   - Actual Result: one or two plain sentences on what the app actually did.
8. Move to the next test case only when the user says so, unless they asked for a batch run.

## Test cases that are NOT fully automatable — mark as Manual or partial

- **Two users at once** (record locked by another user while the page is open): automate only the
  phone side, after the user has changed the status on web, and say so in Notes.
- **Offline sync**: toggling the network is possible with `adb shell svc wifi disable/enable`, but
  **ask the user first**, because wireless debugging drops when Wi-Fi turns off. Default to Manual.
- **Smart To-do / automation behaviour**: check the visible result only; the server-side log is
  out of reach.
- **Status Settings (web only)**: never on the app.

## Connection (wireless debugging)

The user's phone: Developer options → Wireless debugging → "Pair device with pairing code".
```
adb pair <PHONE_IP>:<PAIRING_PORT>      # enter the 6-digit code
adb connect <PHONE_IP>:<CONNECT_PORT>   # the port shown on the Wireless debugging screen
adb devices                             # note the device id, e.g. 192.168.1.23:41235
```
The connect port changes when wireless debugging restarts. If `adb devices` is empty, ask the user
for the new port instead of retrying blindly.

## Flow template

```yaml
# TC03 - Job in Block all status shows Locked chip and greyed controls
appId: ${APP_ID}
env:
  USERNAME: ${USER_USERNAME}
  PASSWORD: ${USER_PASSWORD}
  JOB_ID: ${LOCKED_JOB_ID}
---
- launchApp:
    clearState: false
- runFlow: common/login.yaml
- runFlow:
    file: common/open_job.yaml
    env:
      JOB_ID: ${JOB_ID}
# Expected 1: 'Locked' chip shown beside Edit
- assertVisible: "Locked"
- takeScreenshot: screenshots/TC03/01_locked_chip
# Expected 4: tapping Edit shows the lock toast
- tapOn: "Edit"
- extendedWaitUntil:
    visible: "Completed status is locked"
    timeout: 3000
- takeScreenshot: screenshots/TC03/02_edit_toast
# MANUAL CHECK: buttons greyed but keep their own icon (visual) — see screenshot 01
```

## Reporting at the end of a run

Give the user a short summary: how many Passed / Failed / Blocked / Manual, then list each
Failed case with its Actual Result in one line. The user copies Status and Actual Result into Notion.
