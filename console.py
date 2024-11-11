from datetime import datetime
import json
import os
from typing import List, Dict, Optional

class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

class Student(User):
    def __init__(self, username: str, password: str, roll_number: str, cgpa: float, branch: str):
        super().__init__(username, password)
        self.roll_number = roll_number
        self.cgpa = cgpa
        self.branch = branch
        self.applied_jobs: List[str] = []  # List of job IDs

class Company(User):
    def __init__(self, username: str, password: str, company_name: str):
        super().__init__(username, password)
        self.company_name = company_name
        self.posted_jobs: List[str] = []  # List of job IDs

class Job:
    def __init__(self, job_id: str, company_name: str, role: str, compensation: float, 
                 min_cgpa: float, eligible_branches: List[str], interview_process: str,
                 interview_date: datetime):
        self.job_id = job_id
        self.company_name = company_name
        self.role = role
        self.compensation = compensation
        self.min_cgpa = min_cgpa
        self.eligible_branches = eligible_branches
        self.interview_process = interview_process
        self.interview_date = interview_date
        self.applicants: List[str] = []  # List of student usernames

class PlacementPortal:
    def __init__(self):
        self.students: Dict[str, Student] = {}
        self.companies: Dict[str, Company] = {}
        self.jobs: Dict[str, Job] = {}
        self.load_data()

    def load_data(self):
        # In a real application, this would load from a database
        # For this example, we'll create some sample data
        self._create_sample_data()

    def _create_sample_data(self):
        # Create sample students
        student1 = Student("john_doe", "password123", "2024001", 8.5, "Computer Science")
        student2 = Student("jane_smith", "password456", "2024002", 9.0, "Electronics")
        self.students[student1.username] = student1
        self.students[student2.username] = student2

        # Create sample companies
        company1 = Company("techcorp", "companypass1", "TechCorp")
        company2 = Company("innovatech", "companypass2", "InnovaTech")
        self.companies[company1.username] = company1
        self.companies[company2.username] = company2

        # Create sample jobs
        job1 = Job(
            "TC001", "TechCorp", "Software Engineer",
            100000, 7.5, ["Computer Science", "Electronics"],
            "1. Online test\n2. Technical interview\n3. HR interview",
            datetime.strptime("2024-11-15", "%Y-%m-%d")
        )
        job2 = Job(
            "IT001", "InnovaTech", "Data Scientist",
            120000, 8.0, ["Computer Science"],
            "1. Coding challenge\n2. Machine learning project\n3. Technical discussion",
            datetime.strptime("2024-11-20", "%Y-%m-%d")
        )
        self.jobs[job1.job_id] = job1
        self.jobs[job2.job_id] = job2

    def student_login(self, username: str, password: str) -> Optional[Student]:
        student = self.students.get(username)
        if student and student.password == password:
            return student
        return None

    def company_login(self, username: str, password: str) -> Optional[Company]:
        company = self.companies.get(username)
        if company and company.password == password:
            return company
        return None

    def get_eligible_jobs(self, student: Student) -> List[Job]:
        eligible_jobs = []
        for job in self.jobs.values():
            if (student.cgpa >= job.min_cgpa and 
                student.branch in job.eligible_branches):
                eligible_jobs.append(job)
        return eligible_jobs

    def apply_for_job(self, student: Student, job_id: str) -> bool:
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job_id not in student.applied_jobs:
                student.applied_jobs.append(job_id)
                job.applicants.append(student.username)
                return True
        return False

    def post_job(self, company: Company, job_details: dict) -> str:
        job_id = f"{company.company_name[:2].upper()}{len(self.jobs) + 1:03d}"
        job = Job(
            job_id=job_id,
            company_name=company.company_name,
            **job_details
        )
        self.jobs[job_id] = job
        company.posted_jobs.append(job_id)
        return job_id

    def get_company_jobs(self, company: Company) -> List[Job]:
        return [self.jobs[job_id] for job_id in company.posted_jobs]

    def get_job_applicants(self, job_id: str) -> List[Student]:
        if job_id in self.jobs:
            job = self.jobs[job_id]
            return [self.students[username] for username in job.applicants]
        return []

class ConsoleInterface:
    def __init__(self):
        self.portal = PlacementPortal()
        self.current_user = None

    def start(self):
        while True:
            if not self.current_user:
                self.show_login_menu()
            elif isinstance(self.current_user, Student):
                self.show_student_menu()
            elif isinstance(self.current_user, Company):
                self.show_company_menu()

    def show_login_menu(self):
        print("\n=== Placement Portal Login ===")
        print("1. Student Login")
        print("2. Company Login")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            self.student_login()
        elif choice == "2":
            self.company_login()
        elif choice == "3":
            print("Thank you for using the Placement Portal!")
            exit()

    def student_login(self):
        username = input("Username: ")
        password = input("Password: ")
        student = self.portal.student_login(username, password)
        if student:
            self.current_user = student
            print(f"Welcome, {student.username}!")
        else:
            print("Invalid credentials!")

    def company_login(self):
        username = input("Username: ")
        password = input("Password: ")
        company = self.portal.company_login(username, password)
        if company:
            self.current_user = company
            print(f"Welcome, {company.company_name}!")
        else:
            print("Invalid credentials!")

    def show_student_menu(self):
        student = self.current_user
        while True:
            print("\n=== Student Menu ===")
            print("1. View Eligible Jobs")
            print("2. Apply for a Job")
            print("3. View Applied Jobs")
            print("4. Logout")
            choice = input("Enter your choice: ")

            if choice == "1":
                self.show_eligible_jobs()
            elif choice == "2":
                self.apply_for_job()
            elif choice == "3":
                self.show_applied_jobs()
            elif choice == "4":
                self.current_user = None
                break

    def show_company_menu(self):
        company = self.current_user
        while True:
            print("\n=== Company Menu ===")
            print("1. Post New Job")
            print("2. View Posted Jobs")
            print("3. View Job Applicants")
            print("4. Logout")
            choice = input("Enter your choice: ")

            if choice == "1":
                self.post_new_job()
            elif choice == "2":
                self.show_posted_jobs()
            elif choice == "3":
                self.show_job_applicants()
            elif choice == "4":
                self.current_user = None
                break

    def show_eligible_jobs(self):
        student = self.current_user
        eligible_jobs = self.portal.get_eligible_jobs(student)
        if not eligible_jobs:
            print("No eligible jobs found.")
            return

        print("\n=== Eligible Jobs ===")
        for job in eligible_jobs:
            print(f"\nJob ID: {job.job_id}")
            print(f"Company: {job.company_name}")
            print(f"Role: {job.role}")
            print(f"Compensation: ${job.compensation:,.2f}")
            print(f"Interview Date: {job.interview_date.strftime('%Y-%m-%d')}")
            print(f"Interview Process:\n{job.interview_process}")

    def apply_for_job(self):
        job_id = input("Enter Job ID to apply: ")
        if self.portal.apply_for_job(self.current_user, job_id):
            print("Successfully applied for the job!")
        else:
            print("Failed to apply. Please check the job ID or if you've already applied.")

    def show_applied_jobs(self):
        student = self.current_user
        print("\n=== Applied Jobs ===")
        for job_id in student.applied_jobs:
            job = self.portal.jobs.get(job_id)
            if job:
                print(f"\nJob ID: {job.job_id}")
                print(f"Company: {job.company_name}")
                print(f"Role: {job.role}")
                print(f"Interview Date: {job.interview_date.strftime('%Y-%m-%d')}")

    def post_new_job(self):
        company = self.current_user
        print("\n=== Post New Job ===")
        job_details = {
            'role': input("Job Role: "),
            'compensation': float(input("Compensation: ")),
            'min_cgpa': float(input("Minimum CGPA required: ")),
            'eligible_branches': input("Eligible branches (comma-separated): ").split(','),
            'interview_process': input("Interview process description: "),
            'interview_date': datetime.strptime(input("Interview date (YYYY-MM-DD): "), "%Y-%m-%d")
        }
        job_id = self.portal.post_job(company, job_details)
        print(f"Job posted successfully! Job ID: {job_id}")

    def show_posted_jobs(self):
        company = self.current_user
        jobs = self.portal.get_company_jobs(company)
        print("\n=== Posted Jobs ===")
        for job in jobs:
            print(f"\nJob ID: {job.job_id}")
            print(f"Role: {job.role}")
            print(f"Applicants: {len(job.applicants)}")

    def show_job_applicants(self):
        job_id = input("Enter Job ID to view applicants: ")
        applicants = self.portal.get_job_applicants(job_id)
        if not applicants:
            print("No applicants found for this job.")
            return

        print(f"\n=== Applicants for Job {job_id} ===")
        for student in applicants:
            print(f"\nUsername: {student.username}")
            print(f"Roll Number: {student.roll_number}")
            print(f"CGPA: {student.cgpa}")
            print(f"Branch: {student.branch}")

if __name__ == "__main__":
    interface = ConsoleInterface()
    interface.start()