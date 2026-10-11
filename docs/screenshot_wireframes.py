from playwright.sync_api import sync_playwright
import os

path = "file://" + os.path.abspath("wireframes.html")
frames = ["f1", "f2", "f3", "f4"]
names = ["01_login_register", "02_dashboard", "03_module_task_management", "04_timetable"]

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = browser.new_page(viewport={"width": 1300, "height": 900})
    page.goto(path)
    for fid, name in zip(frames, names):
        el = page.locator(f"#{fid}")
        el.screenshot(path=f"wireframe_{name}.png")
        print(f"saved wireframe_{name}.png")
    browser.close()
