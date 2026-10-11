from playwright.sync_api import sync_playwright

BASE = "http://localhost:5000"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    page.goto(f"{BASE}/auth/login")
    page.fill('input[name="email"]', "amartest@example.com")
    page.fill('input[name="password"]', "TestPass123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard")
    page.screenshot(path="app_dashboard.png", full_page=True)

    page.goto(f"{BASE}/modules/")
    page.screenshot(path="app_modules.png", full_page=True)

    page.goto(f"{BASE}/tasks/module/2")
    page.screenshot(path="app_tasks.png", full_page=True)

    browser.close()
    print("done")
