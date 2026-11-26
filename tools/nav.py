"""Step-by-step navigation for inspecting screens (one Appium session kept between calls).

Usage:
  python tools/nav.py start                     open a session (kept alive between calls)
  python tools/nav.py screen [name]             print visible labels, save screenshot + source
  python tools/nav.py tap <key>                 tap by accessibility id / resource id / exact text
  python tools/nav.py tapcontains <text>        tap first element whose text/desc contains text
  python tools/nav.py type <key> <text>         type into a field (by id / desc)
  python tools/nav.py back                      press Android back
  python tools/nav.py tapxy <x> <y>             tap a screen coordinate
  python tools/nav.py swipe up|down             scroll the screen
  python tools/nav.py stop                      end the session
"""
import base64
import json
import os
import re
import sys
import time
import urllib.request

import yaml
from pathlib import Path

_CFG = yaml.safe_load((Path(__file__).resolve().parent.parent / "config.yaml").read_text(encoding="utf-8"))

HERE = os.path.dirname(os.path.abspath(__file__))
SID_FILE = os.path.join(HERE, ".session_id")
OUT = os.path.join(HERE, "dumps")
os.makedirs(OUT, exist_ok=True)
W3C_ELEMENT = "element-6066-11e4-a5c6-4874f954baf7"


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(_CFG["appium_server_url"] + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode() or "{}").get("value")
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:500]}


def sid():
    with open(SID_FILE) as f:
        return f.read().strip()


def s(path):
    return f"/session/{sid()}{path}"


def find(key):
    strategies = [
        ("accessibility id", key),
        ("id", key),
        ("xpath", f'//*[@resource-id="{key}"]'),
        ("xpath", f'//*[@text="{key}" or @content-desc="{key}"]'),
    ]
    for using, value in strategies:
        v = call("POST", s("/elements"), {"using": using, "value": value})
        if isinstance(v, list) and v:
            return v[0].get(W3C_ELEMENT) or v[0].get("ELEMENT")
    return None


def labels(src):
    found = re.findall(r'(?:text|content-desc|resource-id)="([^"]+)"', src)
    return [f.replace("&#10;", " / ") for f in dict.fromkeys(found)]


def screen(name):
    src = call("GET", s("/source"))
    shot = call("GET", s("/screenshot"))
    with open(os.path.join(OUT, f"{name}.xml"), "w", encoding="utf-8") as f:
        f.write(src)
    with open(os.path.join(OUT, f"{name}.png"), "wb") as f:
        f.write(base64.b64decode(shot))
    print(" | ".join(labels(src))[:4000])
    print(f"(saved tools/dumps/{name}.png)")


def main():
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "start":
        caps = {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "appium:deviceName": "Android",
            "appium:appPackage": _CFG["APP_ID"],
            "appium:appActivity": _CFG.get("APP_ACTIVITY", "com.connection.crm.MainActivity"),
            "appium:noReset": True,
            "appium:newCommandTimeout": 1800,
        }
        v = call("POST", "/session", {"capabilities": {"alwaysMatch": caps}})
        with open(SID_FILE, "w") as f:
            f.write(v["sessionId"])
        print("session", v["sessionId"], "package", call("GET", f"/session/{v['sessionId']}/appium/device/current_package"))
    elif cmd == "screen":
        screen(args[0] if args else time.strftime("screen_%H%M%S"))
    elif cmd == "tap":
        el = find(args[0])
        if not el:
            print("NOT FOUND:", args[0]); sys.exit(1)
        call("POST", s(f"/element/{el}/click"), {})
        time.sleep(2.5)
        print("tapped", args[0])
    elif cmd == "tapcontains":
        t = args[0]
        v = call("POST", s("/elements"), {"using": "xpath",
                 "value": f'//*[contains(@text,"{t}") or contains(@content-desc,"{t}")]'})
        if not v:
            print("NOT FOUND:", t); sys.exit(1)
        call("POST", s(f"/element/{v[0].get(W3C_ELEMENT) or v[0].get("ELEMENT")}/click"), {})
        time.sleep(2.5)
        print("tapped element containing", t)
    elif cmd == "type":
        el = find(args[0])
        if not el:
            print("NOT FOUND:", args[0]); sys.exit(1)
        call("POST", s(f"/element/{el}/click"), {})
        call("POST", s(f"/element/{el}/value"), {"text": " ".join(args[1:])})
        time.sleep(2.5)
        print("typed into", args[0])
    elif cmd == "back":
        call("POST", s("/back"), {})
        time.sleep(2)
        print("back")
    elif cmd == "tapxy":
        x, y = int(args[0]), int(args[1])
        call("POST", s("/actions"), {"actions": [{"type": "pointer", "id": "f", "parameters": {"pointerType": "touch"},
             "actions": [{"type": "pointerMove", "x": x, "y": y}, {"type": "pointerDown"},
                         {"type": "pause", "duration": 80}, {"type": "pointerUp"}]}]})
        time.sleep(2.5)
        print("tapped", x, y)
    elif cmd == "swipe":
        y1, y2 = (1800, 700) if args[0] == "up" else (700, 1800)
        call("POST", s("/actions"), {"actions": [{"type": "pointer", "id": "f", "parameters": {"pointerType": "touch"},
             "actions": [{"type": "pointerMove", "x": 540, "y": y1}, {"type": "pointerDown"},
                         {"type": "pointerMove", "duration": 400, "x": 540, "y": y2}, {"type": "pointerUp"}]}]})
        time.sleep(1.5)
        print("swiped", args[0])
    elif cmd == "stop":
        call("DELETE", f"/session/{sid()}")
        print("stopped")


if __name__ == "__main__":
    main()
