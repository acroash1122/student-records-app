import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, Student
from config import Config


def create_app(config_object=None):
    """Application factory — accepts a config class for testing."""
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    db.init_app(app)

    with app.app_context():
        # Retry loop so the app survives a slow MySQL startup
        for attempt in range(10):
            try:
                db.create_all()
                break
            except Exception:
                if attempt < 9:
                    time.sleep(3)
                else:
                    raise

    _register_routes(app)
    return app


def _register_routes(app):
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['logged_in'] = True
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('students'))
            flash('Invalid credentials. Try admin / admin123.', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('Logged out successfully.', 'info')
        return redirect(url_for('index'))

    @app.route('/students')
    def students():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        all_students = Student.query.order_by(Student.created_at.desc()).all()
        return render_template('students.html', students=all_students)

    @app.route('/students/add', methods=['GET', 'POST'])
    def add_student():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            roll_number = request.form.get('roll_number', '').strip()
            email = request.form.get('email', '').strip()
            department = request.form.get('department', '').strip()
            if not name or not roll_number or not email or not department:
                flash('All fields are required.', 'danger')
                return render_template('add_student.html'), 400
            student = Student(
                name=name,
                roll_number=roll_number,
                email=email,
                department=department,
            )
            db.session.add(student)
            db.session.commit()
            flash(f'Student {name} added successfully!', 'success')
            return redirect(url_for('students'))
        return render_template('add_student.html')

    @app.route('/students/delete/<int:student_id>', methods=['POST'])
    def delete_student(student_id):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully.', 'success')
        return redirect(url_for('students'))

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})


if __name__ == '__main__':
    application = create_app()
    application.run(host='0.0.0.0', port=5000, debug=False)
