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