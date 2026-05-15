# Student Records Management

A simple CRUD web application built with **Python / Flask + MySQL**, used to
demonstrate a complete Jenkins CI/CD pipeline on AWS EC2.

> **Course:** CSE483 – Topics in Software Engineering II  
> **Assignment 3:** Jenkins CI/CD Pipeline

---

## Tech Stack

| Layer       | Technology                    |
|-------------|-------------------------------|
| Backend     | Python 3.11, Flask 3.0        |
| Database    | MySQL 8.0 (SQLAlchemy ORM)    |
| Unit Tests  | pytest + pytest-flask (SQLite)|
| E2E Tests   | Selenium 4, headless Chrome   |
| Container   | Docker + docker-compose       |
| CI/CD       | Jenkins (Declarative Pipeline)|
| Cloud       | AWS EC2 (Ubuntu 22.04)        |

---

## Architecture

```
                  ┌──────────────────────────────────────┐
                  │           GitHub Repository           │
                  │   (push triggers webhook → Jenkins)   │
                  └──────────────┬───────────────────────┘
                                 │ webhook
                  ┌──────────────▼───────────────────────┐
                  │          Jenkins on EC2 :8080         │
                  │                                       │
                  │  Stage 1: Code Build                  │
                  │    └─ docker build → app image        │
                  │                                       │
                  │  Stage 2: Unit Testing                │
                  │    └─ python:3.11-slim + pytest       │
                  │       (SQLite in-memory, no MySQL)    │
                  │                                       │
                  │  Stage 3: Containerized Deployment    │
                  │    ├─ MySQL 8.0 container             │
                  │    └─ Flask app container :5000       │
                  │       (waits for /health = 200)       │
                  │                                       │
                  │  Stage 4: Selenium Testing            │
                  │    └─ Selenium container              │
                  │       (headless Chrome, same network) │
                  └──────────────────────────────────────┘
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- MySQL 8.0 running locally (or skip and use Docker)
- Google Chrome installed (for local Selenium tests)

### 1. Clone & create virtual environment

```bash
git clone <your-repo-url>
cd student-records-app
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
```

### 3. Create the MySQL database

```sql
CREATE DATABASE student_records;
CREATE USER 'student_user'@'localhost' IDENTIFIED BY 'studentpass';
GRANT ALL PRIVILEGES ON student_records.* TO 'student_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Run the application

```bash
python app.py
# App is available at http://localhost:5000
# Login: admin / admin123
```

---

## Running Tests Locally

### Unit tests (no MySQL needed)

```bash
pytest tests/ -v
```

### Selenium tests (app must be running)

```bash
# In one terminal:
python app.py

# In another terminal:
APP_URL=http://localhost:5000 pytest selenium_tests/ -v
```

---

## Running with Docker Compose

### Start app + database

```bash
docker-compose up --build
# App: http://localhost:5000
```

### Run the full stack including Selenium tests

```bash
docker-compose --profile test up --build
```

### Tear everything down

```bash
docker-compose down -v
```

---

## Pipeline Stages

| # | Stage                         | What it does                                            |
|---|-------------------------------|---------------------------------------------------------|
| 1 | **Code Build**                | `git checkout` + `docker build` the Flask app image    |
| 2 | **Unit Testing**              | `pytest tests/` in a throwaway container (SQLite)      |
| 3 | **Containerized Deployment**  | Start MySQL + Flask, poll `/health` until ready         |
| 4 | **Selenium Testing**          | Build Selenium image, run E2E tests against live app   |

All cleanup (containers, network, images) runs in the `post { always }` block.

---

## Manual Configuration Required

After following the AWS/Jenkins setup guide, update these values before
pushing to GitHub:

| Item | Where | What to change |
|------|-------|----------------|
| GitHub repo URL | Jenkins job → SCM | Set to your actual repo URL |
| Webhook URL | GitHub → Settings → Webhooks | `http://<EC2-PUBLIC-IP>:8080/github-webhook/` |
| DB password | `docker-compose.yml` | Replace `rootpassword` / `studentpass` in production |
| `SECRET_KEY` | `docker-compose.yml` | Set a strong random value |

---

## Project Structure

```
student-records-app/
├── app.py                  # Application factory + route handlers
├── models.py               # SQLAlchemy Student model
├── config.py               # Config / TestConfig classes
├── requirements.txt
├── Dockerfile              # Flask app image
├── Dockerfile.selenium     # Headless Chrome + pytest image
├── docker-compose.yml      # Orchestrates db + app + selenium-tests
├── Jenkinsfile             # 4-stage declarative pipeline
├── templates/              # Jinja2 HTML templates (Bootstrap 5)
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── students.html
│   └── add_student.html
├── static/
│   └── style.css
├── tests/                  # pytest unit tests (SQLite)
│   ├── conftest.py
│   └── test_unit.py
└── selenium_tests/         # Selenium E2E tests
    ├── conftest.py
    └── test_selenium.py
```
