"""Full integration walkthrough: registers a brand-new user and performs
the complete journey a real student would, as described in the proposal.
Fails loudly (assert) if anything doesn't work end-to-end.
"""
from playwright.sync_api import sync_playwright, expect

BASE = "http://localhost:5000"
EMAIL = "integration_test@example.com"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    page = browser.new_page(viewport={"width": 1280, "height": 1000})

    # 1. Register
    page.goto(f"{BASE}/auth/register")
    page.fill('input[name="name"]', "Integration Tester")
    page.fill('input[name="email"]', EMAIL)
    page.fill('input[name="password"]', "TestPass123")
    page.click('button[type="submit"]')
    expect(page).to_have_url(f"{BASE}/auth/login")
    print("[OK] Registration -> redirected to login")

    # 2. Login
    page.fill('input[name="email"]', EMAIL)
    page.fill('input[name="password"]', "TestPass123")
    page.click('button[type="submit"]')
    expect(page).to_have_url(f"{BASE}/dashboard")
    print("[OK] Login -> dashboard")

    # 3. Top nav present and correct
    expect(page.locator(".topnav")).to_contain_text("Dashboard")
    expect(page.locator(".topnav")).to_contain_text("Modules")
    expect(page.locator(".topnav")).to_contain_text("Timetable")
    print("[OK] Top nav renders with all links")

    # 4. Add a module via the nav
    page.click("text=Modules")
    page.click("text=+ Add Module")
    page.fill('input[name="name"]', "Software Development")
    page.fill('textarea[name="description"]', "Agile, patterns, testing")
    page.click('button[type="submit"]')
    expect(page.locator(".card h3")).to_contain_text("Software Development")
    print("[OK] Module created and visible")

    # 5. Add tasks
    page.click("text=View Tasks")
    for title, due, pri, diff, hrs, struggling in [
        ("Design Patterns Essay", "2026-09-20", "high", "5", "6", True),
        ("Unit Testing Lab", "2026-10-15", "low", "2", "3", False),
    ]:
        page.click("text=+ Add Task")
        page.fill('input[name="title"]', title)
        page.fill('input[name="due_date"]', due)
        page.select_option('select[name="priority"]', pri)
        page.fill('input[name="difficulty"]', diff)
        page.fill('input[name="estimated_hours"]', hrs)
        if struggling:
            page.check('input[name="is_struggling"]')
        page.click('button[type="submit"]')
    expect(page.locator("table.data-table")).to_contain_text("Design Patterns Essay")
    expect(page.locator("table.data-table")).to_contain_text("Unit Testing Lab")
    print("[OK] Both tasks created and visible")

    # 6. Log some hours on the overdue task
    row = page.locator("tr", has_text="Design Patterns Essay")
    row.locator('input[name="hours"]').fill("2")
    row.locator("text=Log").click()
    expect(page.locator("tr", has_text="Design Patterns Essay")).to_contain_text("33%")
    print("[OK] Logged hours -> progress bar updated")

    # 7. Check dashboard recommendation ranks the overdue+struggling task first
    page.click("text=Dashboard")
    first_rec = page.locator(".card.recommend-top h3")
    expect(first_rec).to_contain_text("Design Patterns Essay")
    print("[OK] Recommendation engine correctly ranks overdue+struggling task #1")

    # 8. Generate timetable
    page.click("text=Timetable")
    page.click("text=Regenerate Timetable")
    expect(page.locator(".flash-success, .flash-error")).to_be_visible()
    expect(page.locator(".timetable-grid")).to_be_visible()
    print("[OK] Timetable generated and rendered")

    # 9. Mark a task complete and confirm dashboard reflects it
    page.click("text=Modules")
    page.click("text=View Tasks")
    row = page.locator("tr", has_text="Unit Testing Lab")
    row.locator("text=Mark Done").click()
    page.click("text=Dashboard")
    expect(page.locator(".card", has_text="Tasks completed")).to_contain_text("1 / 2")
    print("[OK] Mark-complete reflected correctly on dashboard")

    # 10. Logout
    page.click("text=Logout")
    expect(page).to_have_url(f"{BASE}/auth/login")
    print("[OK] Logout works")

    page.screenshot(path="full_journey_final_dashboard_state.png", full_page=True)
    browser.close()
    print("\nALL INTEGRATION CHECKS PASSED")
