"""
Selenium end-to-end tests for Student Records Management app.

APP_URL is read from the environment so tests work both locally
(http://localhost:5000) and inside the Jenkins Docker network
(http://app:5000 — the Flask container's service name).
"""
import os
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _login(driver, wait):
    """Navigate to /login and log in with the demo admin account."""
    driver.get(f'{APP_URL}/login')
    wait.until(EC.presence_of_element_located((By.ID, 'username'))).clear()
    driver.find_element(By.ID, 'username').send_keys('admin')
    driver.find_element(By.ID, 'password').clear()
    driver.find_element(By.ID, 'password').send_keys('admin123')
    driver.find_element(By.ID, 'login-btn').click()


# ---------------------------------------------------------------------------
# Test: homepage navigation
# ---------------------------------------------------------------------------

class TestHomepageNavigation:
    def test_homepage_title_and_navigation(self, driver):
        """
        Verify the homepage loads with the correct title, shows the
        navbar brand, and the 'Get Started' button navigates to /login.
        """
        driver.get(APP_URL)
        wait = WebDriverWait(driver, 10)

        # Page title
        assert 'Student Records Management' in driver.title

        # Navbar brand is visible
        brand = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'navbar-brand')))
        assert 'Student Records' in brand.text

        # 'Get Started' button is present and clickable
        get_started = wait.until(EC.element_to_be_clickable((By.ID, 'get-started-btn')))
        assert get_started.is_displayed()
        get_started.click()

        # Should land on the login page
        wait.until(EC.title_contains('Login'))
        assert 'Login' in driver.title


# ---------------------------------------------------------------------------
# Test: login flows
# ---------------------------------------------------------------------------

class TestLoginFlow:
    def test_login_with_invalid_credentials_shows_error(self, driver):
        """
        Verify that submitting wrong credentials keeps the user on the
        login page and shows a flash error message containing 'Invalid'.
        """
        driver.get(f'{APP_URL}/login')
        wait = WebDriverWait(driver, 10)

        username_field = wait.until(EC.presence_of_element_located((By.ID, 'username')))
        username_field.clear()
        username_field.send_keys('hacker')

        driver.find_element(By.ID, 'password').clear()
        driver.find_element(By.ID, 'password').send_keys('wrongpassword')
        driver.find_element(By.ID, 'login-btn').click()

        # Flash message with 'Invalid' must appear
        flash = wait.until(EC.visibility_of_element_located((By.ID, 'flash-message')))
        assert 'Invalid' in flash.text or 'invalid' in flash.text.lower()
        # Still on the login page
        assert 'Login' in driver.title

    def test_login_and_add_student_flow(self, driver):
        """
        Full happy-path E2E:
        1. Log in with valid credentials
        2. Navigate to Add Student
        3. Fill in the form and submit
        4. Verify the new student appears in the Students List
        """
        wait = WebDriverWait(driver, 15)

        # --- Step 1: Login ---
        _login(driver, wait)
        wait.until(EC.title_contains('Students'))
        assert 'Students' in driver.title

        # --- Step 2: Go to Add Student page ---
        add_btn = wait.until(EC.element_to_be_clickable((By.ID, 'add-new-btn')))
        add_btn.click()
        wait.until(EC.title_contains('Add Student'))
        assert 'Add Student' in driver.title

        # --- Step 3: Fill the form ---
        wait.until(EC.presence_of_element_located((By.ID, 'name'))).send_keys(
            'Selenium Test Student'
        )
        driver.find_element(By.ID, 'roll_number').send_keys('SE-2024-999')
        driver.find_element(By.ID, 'email').send_keys('selenium.test@university.edu')
        Select(driver.find_element(By.ID, 'department')).select_by_visible_text(
            'Computer Science'
        )

        # --- Step 4: Submit and verify ---
        driver.find_element(By.ID, 'submit-btn').click()
        wait.until(EC.title_contains('Students List'))

        page_source = driver.page_source
        assert 'Selenium Test Student' in page_source
        assert 'SE-2024-999' in page_source

    def test_logout_redirects_to_home(self, driver):
        """
        After logging in, clicking logout should redirect back to the
        homepage and remove the authenticated nav links.
        """
        wait = WebDriverWait(driver, 10)

        # Ensure we are logged in
        driver.get(f'{APP_URL}/students')
        if 'Login' in driver.title:
            _login(driver, wait)
            wait.until(EC.title_contains('Students'))

        # Click the logout link in the navbar
        logout_link = wait.until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Logout'))
        )
        logout_link.click()

        # Should land on home (or login) page
        wait.until(EC.title_contains('Student Records Management'))
        assert 'Student Records Management' in driver.title

        # 'Get Started' button should be visible again (user is logged out)
        assert driver.find_element(By.ID, 'get-started-btn').is_displayed()
