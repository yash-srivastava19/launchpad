# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.models import Student, Company
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        user = None
        if user_type == 'student':
            user = Student.query.filter_by(email=email).first()
        elif user_type == 'company':
            user = Company.query.filter_by(email=email).first()
            
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# app/routes/student.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Job, JobApplication
from app.utils.email import send_application_notification
from app import db

bp = Blueprint('student', __name__)

@bp.route('/student/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Student):
        return redirect(url_for('index'))
    
    applied_jobs = JobApplication.query.filter_by(student_id=current_user.id).all()
    return render_template('student/dashboard.html', applied_jobs=applied_jobs)

@bp.route('/student/jobs')
@login_required
def jobs():
    if not isinstance(current_user, Student):
        return redirect(url_for('index'))
    
    eligible_jobs = Job.query.filter(
        Job.min_cgpa <= current_user.cgpa,
        Job.eligible_branches.contains(current_user.branch)
    ).all()
    
    return render_template('student/jobs.html', jobs=eligible_jobs)

@bp.route('/student/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if not isinstance(current_user, Student):
        return redirect(url_for('index'))
    
    job = Job.query.get_or_404(job_id)
    existing_application = JobApplication.query.filter_by(
        student_id=current_user.id, job_id=job_id
    ).first()
    
    if existing_application:
        flash('You have already applied for this job.')
        return redirect(url_for('student.jobs'))
    
    application = JobApplication(student_id=current_user.id, job_id=job_id)
    db.session.add(application)
    db.session.commit()
    
    send_application_notification(job.company, current_user, job)
    flash('Successfully applied for the job!')
    return redirect(url_for('student.dashboard'))