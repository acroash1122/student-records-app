"""
Unit tests for Student Records Management app.
All tests use an in-memory SQLite database — no MySQL connection required.
"""
import json
import pytest


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

class TestHomePage:
    def test_home_page_loads(self, client):
        """GET / returns HTTP 200 and renders the home template."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Student Records' in response.data

    def test_home_page_shows_login_link_when_not_logged_in(self, client):
        """Unauthenticated home page shows a get-started / login link."""
        response = client.get('/')
        assert response.status_code == 200
        # The 'get-started-btn' id is present when not logged in
        assert b'get-started-btn' in response.data


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------

class TestLoginPage:
    def test_login_page_loads(self, client):
        """GET /login returns HTTP 200 and renders the login form."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'username' in response.data
        assert b'password' in response.data
        assert b'login-btn' in response.data

    def test_login_with_valid_credentials(self, client):
        """POST /login with correct credentials redirects to students list."""
        response = client.post(
            '/login',
            data={'username': 'admin', 'password': 'admin123'},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # After login the students list page loads
        assert b'Students' in response.data or b'Login successful' in response.data

    def test_login_with_invalid_credentials(self, client):
        """POST /login with wrong credentials shows an error message."""
        response = client.post(
            '/login',
            data={'username': 'wrong', 'password': 'badpass'},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b'Invalid' in response.data


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_endpoint_returns_200(self, client):
        """GET /health returns HTTP 200."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_endpoint_returns_json_ok(self, client):
        """GET /health returns JSON body {"status": "ok"}."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert data['status'] == 'ok'


# ---------------------------------------------------------------------------
# Access control & form validation
# ---------------------------------------------------------------------------

class TestAccessControl:
    def test_students_list_requires_login(self, client):
        """GET /students without a session redirects to /login."""
        response = client.get('/students', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_add_student_page_requires_login(self, client):
        """GET /students/add without a session redirects to /login."""
        response = client.get('/students/add', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


class TestStudentFormValidation:
    def test_add_student_empty_form_returns_400(self, client):
        """POST /students/add with all-empty fields returns HTTP 400."""
        # Manually set session to simulate a logged-in user
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'admin'

        response = client.post(
            '/students/add',
            data={'name': '', 'roll_number': '', 'email': '', 'department': ''},
        )
        assert response.status_code == 400

    def test_add_student_partial_form_returns_400(self, client):
        """POST /students/add with some fields missing returns HTTP 400."""
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'admin'

        response = client.post(
            '/students/add',
            data={'name': 'Alice', 'roll_number': '', 'email': '', 'department': ''},
        )
        assert response.status_code == 400
