"""Save the current screen's page source and screenshot, and print its locators.

  python tools/dump_screen.py <name>      -> tools/dumps/<name>.xml + .png

Read-only: attaches a short Appium session to the app as it is now (no reset, no taps).
"""
import re
import sys
from pathlib import Path

import yaml
from appium import webdriver
from appium.options.android import UiAutomator2Options

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "dumps"


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "screen"
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.app_package = cfg["APP_ID"]
    opts.no_reset = True
    opts.auto_launch = False          # don't restart the app: inspect what's on screen
    drv = webdriver.Remote(cfg["appium_server_url"], options=opts)
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        src = drv.page_source
        (OUT / f"{name}.xml").write_text(src, encoding="utf-8")
        drv.save_screenshot(str(OUT / f"{name}.png"))
        for m in re.finditer(r'<([\w.]+) [^>]*?(?:text="([^"]*)")?[^>]*?content-desc="([^"]*)"[^>]*?'
                             r'clickable="(\w+)"[^>]*?enabled="(\w+)"', src):
            cls, text, desc, clickable, enabled = m.groups()
            if desc or text:
                label = (desc or text).replace("&#10;", " / ")
                print(f"{cls.split('.')[-1]:<14} click={clickable[0]} enabled={enabled[0]}  {label[:110]}")
        print(f"\nsaved {OUT / (name + '.xml')} and .png")
    finally:
        drv.quit()


if __name__ == "__main__":
    main()
