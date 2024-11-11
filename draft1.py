# # Directory structure:
# launchpad/
# ├── requirements.txt
# ├── config.py
# ├── run.py
# ├── app/
# │   ├── __init__.py
# │   ├── models.py
# │   ├── routes/
# │   │   ├── __init__.py
# │   │   ├── auth.py
# │   │   ├── student.py
# │   │   └── company.py
# │   ├── utils/
# │   │   ├── __init__.py
# │   │   ├── email.py
# │   │   └── decorators.py
# │   └── templates/
# │       ├── base.html
# │       ├── auth/
# │       │   ├── login.html
# │       │   └── register.html
# │       ├── student/
# │       │   ├── dashboard.html
# │       │   └── jobs.html
# │       └── company/
# │           ├── dashboard.html
# │           └── post_job.html


# app/models.py
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(20), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(User):
    __tablename__ = 'student'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    resume_url = db.Column(db.String(200))
    
    applications = db.relationship('JobApplication', backref='student', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }

class Company(User):
    __tablename__ = 'company'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    website = db.Column(db.String(200))
    
    jobs = db.relationship('Job', backref='company', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'company',
    }

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    compensation = db.Column(db.Float, nullable=False)
    min_cgpa = db.Column(db.Float, nullable=False)
    eligible_branches = db.Column(db.String(200), nullable=False)
    interview_process = db.Column(db.Text, nullable=False)
    interview_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    applications = db.relationship('JobApplication', backref='job', lazy=True)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

# app/utils/email.py
from flask_mail import Message
from app import mail
from flask import current_app, render_template

def send_job_notification(student, job):
    msg = Message(
        f'New Job Opportunity: {job.title} at {job.company.company_name}',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[student.email]
    )
    msg.body = render_template('email/job_notification.txt', student=student, job=job)
    msg.html = render_template('email/job_notification.html', student=student, job=job)
    mail.send(msg)

def send_application_notification(company, student, job):
    msg = Message(
        f'New Application: {student.name} for {job.title}',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[company.email]
    )
    msg.body = render_template('email/application_notification.txt', 
                              company=company, student=student, job=job)
    msg.html = render_template('email/application_notification.html', 
                              company=company, student=student, job=job)
    mail.send(msg)

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

# app/routes/company.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Job, Student
from app.utils.email import send_job_notification
from app import db

bp = Blueprint('company', __name__)

@bp.route('/company/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Company):
        return redirect(url_for('index'))
    
    jobs = Job.query.filter_by(company_id=current_user.id).all()
    return render_template('company/dashboard.html', jobs=jobs)

@bp.route('/company/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    if not isinstance(current_user, Company):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        job = Job(
            company_id=current_user.id,
            title=request.form['title'],
            description=request.form['description'],
            compensation=float(request.form['compensation']),
            min_cgpa=float(request.form['min_cgpa']),
            eligible_branches=request.form['eligible_branches'],
            interview_process=request.form['interview_process'],
            interview_date=datetime.strptime(request.form['interview_date'], '%Y-%m-%d')
        )
        db.session.add(job)
        db.session.commit()
        
        # Notify eligible students
        eligible_students = Student.query.filter(
            Student.cgpa >= job.min_cgpa,
            Student.branch.in_(job.eligible_branches.split(','))
        ).all()
        
        for student in eligible_students:
            send_job_notification(student, job)
        
        flash('Job posted successfully!')
        return redirect(url_for('company.dashboard'))
    
    return render_template('company/post_job.html')

# run.py
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


# ---------------------------------------------------

# Additional models in app/models.py

class Alumni(User):
    __tablename__ = 'alumni'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    company = db.Column(db.String(100))
    position = db.Column(db.String(100))
    linkedin_url = db.Column(db.String(200))
    is_mentor = db.Column(db.Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'alumni',
    }

class MentorshipRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    alumni_id = db.Column(db.Integer, db.ForeignKey('alumni.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.Text)

class ATSScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# New routes in app/routes/analytics.py
from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Job, JobApplication, Student, Company, Alumni
from sqlalchemy import func

bp = Blueprint('analytics', __name__)

@bp.route('/analytics')
@login_required
def dashboard():
    # Placement statistics
    total_students = Student.query.count()
    placed_students = JobApplication.query.filter_by(status='accepted').distinct(JobApplication.student_id).count()
    placement_ratio = placed_students / total_students if total_students > 0 else 0
    
    # Company participation
    total_companies = Company.query.count()
    active_companies = Company.query.join(Job).distinct().count()
    
    # Average package
    avg_package = db.session.query(func.avg(Job.compensation)).join(JobApplication).filter(JobApplication.status == 'accepted').scalar() or 0
    
    # Branch-wise placement
    branch_placements = db.session.query(
        Student.branch, 
        func.count(distinct(JobApplication.student_id)).label('placed')
    ).join(JobApplication).filter(JobApplication.status == 'accepted').group_by(Student.branch).all()
    
    return render_template('analytics/dashboard.html',
                          placement_ratio=placement_ratio,
                          total_companies=total_companies,
                          active_companies=active_companies,
                          avg_package=avg_package,
                          branch_placements=branch_placements)

# New routes in app/routes/alumni.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Alumni, MentorshipRequest

bp = Blueprint('alumni', __name__)

@bp.route('/alumni/network')
@login_required
def network():
    alumni = Alumni.query.filter_by(is_mentor=True).all()
    return render_template('alumni/network.html', alumni=alumni)

@bp.route('/alumni/request_mentorship/<int:alumni_id>', methods=['POST'])
@login_required
def request_mentorship(alumni_id):
    if not isinstance(current_user, Student):
        flash('Only students can request mentorship')
        return redirect(url_for('alumni.network'))
    
    existing_request = MentorshipRequest.query.filter_by(
        student_id=current_user.id, alumni_id=alumni_id
    ).first()
    
    if existing_request:
        flash('You have already requested mentorship from this alumni')
        return redirect(url_for('alumni.network'))
    
    mentorship_request = MentorshipRequest(
        student_id=current_user.id,
        alumni_id=alumni_id,
        message=request.form.get('message', '')
    )
    db.session.add(mentorship_request)
    db.session.commit()
    
    flash('Mentorship request sent successfully')
    return redirect(url_for('alumni.network'))