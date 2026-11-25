# Setup: run the Action Lock test cases with Claude Code + wireless debugging

## 1. Install (once, on your laptop)
1. **Android platform-tools** (adb), and add the folder to PATH. Check: `adb version`
2. **Java 17+**. Check: `java -version`
3. **Maestro**. See https://maestro.mobile.dev for the install command for your OS. Check: `maestro --version`
4. **Claude Code**. See https://docs.anthropic.com/en/docs/claude-code/overview

## 2. Make the project folder
```
action-lock-automation/
├── CLAUDE.md
├── config.yaml
└── testcases/Module_Action_Lock_App_Test_Cases.csv
```
Fill in `config.yaml`: app id, test accounts, test record IDs. Use **staging and test accounts only**.

## 3. Connect the phone over Wi-Fi (laptop and phone on the same network)
1. Phone: Settings → Developer options → **Wireless debugging** ON
2. Tap **Pair device with pairing code**, then on the laptop:
   ```
   adb pair 192.168.x.x:PAIRING_PORT
   adb connect 192.168.x.x:CONNECT_PORT
   adb devices
   ```
3. Put the device id from `adb devices` into `config.yaml`.

## 4. Set up the preconditions on web
In Status Settings, set the locks the test cases need (e.g. Job Completed = Block all), then flip the
matching `preconditions_ready` entries in `config.yaml` to `true`.

## 5. Start Claude Code in the folder
```
cd action-lock-automation
claude
```
First prompt to give it:

> Read CLAUDE.md and config.yaml, then check the phone is connected with adb devices.
> Start with TC03 only: inspect the screens, write the Maestro flow, run it, and record the result.
> Show me the flow before running it.

When TC03 works, continue in small batches:

> Do TC04 to TC09 the same way, one at a time, and give me the summary at the end.

## 6. Put the results back into Notion
Open `results/results.csv` and copy **Status** and **Actual Result** into each test case in Notion.
Attach screenshots from `screenshots/TCxx/` for any Failed case.

## Good first candidates
Single-user cases on the app: TC03–TC09, TC14–TC15, TC17–TC18.
Keep these manual for now: TC12 (two users at once), TC25–TC26 (Freeze prompt), TC30 (offline).
