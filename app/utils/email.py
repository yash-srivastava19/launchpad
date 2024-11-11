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