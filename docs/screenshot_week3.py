from playwright.sync_api import sync_playwright

BASE = "http://localhost:5000"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = browser.new_page(viewport={"width": 1280, "height": 1000})

    page.goto(f"{BASE}/auth/login")
    page.fill('input[name="email"]', "week3test@example.com")
    page.fill('input[name="password"]', "TestPass123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard")
    page.screenshot(path="app_dashboard_recommendations.png", full_page=True)

    page.goto(f"{BASE}/timetable/")
    page.screenshot(path="app_timetable.png", full_page=True)

    browser.close()
    print("done")
