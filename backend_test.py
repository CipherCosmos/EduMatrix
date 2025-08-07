#!/usr/bin/env python3
"""
Comprehensive Backend Test Suite for CO-PO Student Performance Tracker
Tests all backend API endpoints and functionality
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://9a8a4b19-324e-495e-ab32-6bb98440713f.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.teacher_token = None
        self.student_token = None
        self.test_data = {}
        self.failed_tests = []
        self.passed_tests = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        if success:
            self.passed_tests.append(test_name)
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.failed_tests.append(test_name)
            print(f"❌ {test_name}: FAILED {message}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{BACKEND_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                return False, {"error": "Invalid method"}, 400
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return response.status_code < 400, response_data, response.status_code
        except Exception as e:
            return False, {"error": str(e)}, 500

    def test_jwt_authentication(self):
        """Test JWT Authentication System"""
        print("\n🔐 Testing JWT Authentication System...")
        
        # Test user registration - Admin
        admin_data = {
            "name": "Dr. Sarah Johnson",
            "email": "admin@university.edu",
            "password": "SecureAdmin123!",
            "role": "admin"
        }
        
        success, response, status = self.make_request("POST", "/auth/register", admin_data)
        if success and "access_token" in response:
            self.admin_token = response["access_token"]
            self.log_result("Admin Registration", True, f"Token received")
        else:
            self.log_result("Admin Registration", False, f"Status: {status}, Response: {response}")
        
        # Test user registration - Teacher
        teacher_data = {
            "name": "Prof. Michael Chen",
            "email": "teacher@university.edu", 
            "password": "TeacherPass456!",
            "role": "teacher"
        }
        
        success, response, status = self.make_request("POST", "/auth/register", teacher_data)
        if success and "access_token" in response:
            self.teacher_token = response["access_token"]
            self.log_result("Teacher Registration", True, f"Token received")
        else:
            self.log_result("Teacher Registration", False, f"Status: {status}, Response: {response}")
        
        # Test user registration - Student
        student_data = {
            "name": "Alice Smith",
            "email": "alice.smith@student.edu",
            "password": "StudentPass789!",
            "role": "student",
            "semester": 6,
            "program_id": "temp_program_id"
        }
        
        success, response, status = self.make_request("POST", "/auth/register", student_data)
        if success and "access_token" in response:
            self.student_token = response["access_token"]
            self.log_result("Student Registration", True, f"Token received")
        else:
            self.log_result("Student Registration", False, f"Status: {status}, Response: {response}")
        
        # Test login
        login_data = {
            "email": "admin@university.edu",
            "password": "SecureAdmin123!"
        }
        
        success, response, status = self.make_request("POST", "/auth/login", login_data)
        if success and "access_token" in response:
            self.log_result("Admin Login", True, "Login successful")
        else:
            self.log_result("Admin Login", False, f"Status: {status}, Response: {response}")
        
        # Test get current user
        success, response, status = self.make_request("GET", "/auth/me", token=self.admin_token)
        if success and "email" in response:
            self.log_result("Get Current User", True, f"User: {response.get('name', 'Unknown')}")
        else:
            self.log_result("Get Current User", False, f"Status: {status}, Response: {response}")
        
        # Test invalid credentials
        invalid_login = {
            "email": "admin@university.edu",
            "password": "wrongpassword"
        }
        
        success, response, status = self.make_request("POST", "/auth/login", invalid_login)
        if not success and status == 401:
            self.log_result("Invalid Login Rejection", True, "Correctly rejected invalid credentials")
        else:
            self.log_result("Invalid Login Rejection", False, f"Should have rejected invalid credentials")

    def test_academic_structure(self):
        """Test Academic Structure (Programs, Courses)"""
        print("\n🏫 Testing Academic Structure...")
        
        # Test create program (Admin only)
        program_data = {
            "name": "Computer Science Engineering"
        }
        
        success, response, status = self.make_request("POST", "/programs", program_data, self.admin_token)
        if success and "id" in response:
            self.test_data["program_id"] = response["id"]
            self.log_result("Create Program", True, f"Program ID: {response['id']}")
        else:
            self.log_result("Create Program", False, f"Status: {status}, Response: {response}")
        
        # Test get programs
        success, response, status = self.make_request("GET", "/programs", token=self.admin_token)
        if success and isinstance(response, list):
            self.log_result("Get Programs", True, f"Found {len(response)} programs")
        else:
            self.log_result("Get Programs", False, f"Status: {status}, Response: {response}")
        
        # Test create course (Admin only)
        if "program_id" in self.test_data:
            course_data = {
                "name": "Data Structures and Algorithms",
                "semester": 4,
                "program_id": self.test_data["program_id"]
            }
            
            success, response, status = self.make_request("POST", "/courses", course_data, self.admin_token)
            if success and "id" in response:
                self.test_data["course_id"] = response["id"]
                self.log_result("Create Course", True, f"Course ID: {response['id']}")
            else:
                self.log_result("Create Course", False, f"Status: {status}, Response: {response}")
        
        # Test get courses
        success, response, status = self.make_request("GET", "/courses", token=self.admin_token)
        if success and isinstance(response, list):
            self.log_result("Get Courses", True, f"Found {len(response)} courses")
        else:
            self.log_result("Get Courses", False, f"Status: {status}, Response: {response}")
        
        # Test get courses by program
        if "program_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/courses/program/{self.test_data['program_id']}", token=self.admin_token)
            if success and isinstance(response, list):
                self.log_result("Get Courses by Program", True, f"Found {len(response)} courses for program")
            else:
                self.log_result("Get Courses by Program", False, f"Status: {status}, Response: {response}")

    def test_course_program_outcomes(self):
        """Test Course and Program Outcomes"""
        print("\n🎯 Testing Course and Program Outcomes...")
        
        # Test create program outcome (Admin only)
        po_data = {
            "po_code": "PO1",
            "description": "Engineering knowledge: Apply the knowledge of mathematics, science, engineering fundamentals"
        }
        
        success, response, status = self.make_request("POST", "/program-outcomes", po_data, self.admin_token)
        if success and "id" in response:
            self.test_data["po_id"] = response["id"]
            self.log_result("Create Program Outcome", True, f"PO ID: {response['id']}")
        else:
            self.log_result("Create Program Outcome", False, f"Status: {status}, Response: {response}")
        
        # Test get program outcomes
        success, response, status = self.make_request("GET", "/program-outcomes", token=self.admin_token)
        if success and isinstance(response, list):
            self.log_result("Get Program Outcomes", True, f"Found {len(response)} program outcomes")
        else:
            self.log_result("Get Program Outcomes", False, f"Status: {status}, Response: {response}")
        
        # Test create course outcome (Teacher only)
        if "course_id" in self.test_data:
            co_data = {
                "course_id": self.test_data["course_id"],
                "co_code": "CO1",
                "description": "Understand fundamental concepts of data structures"
            }
            
            success, response, status = self.make_request("POST", "/course-outcomes", co_data, self.teacher_token)
            if success and "id" in response:
                self.test_data["co_id"] = response["id"]
                self.log_result("Create Course Outcome", True, f"CO ID: {response['id']}")
            else:
                self.log_result("Create Course Outcome", False, f"Status: {status}, Response: {response}")
        
        # Test get course outcomes by course
        if "course_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/course-outcomes/course/{self.test_data['course_id']}", token=self.teacher_token)
            if success and isinstance(response, list):
                self.log_result("Get Course Outcomes by Course", True, f"Found {len(response)} course outcomes")
            else:
                self.log_result("Get Course Outcomes by Course", False, f"Status: {status}, Response: {response}")
        
        # Test CO-PO mapping (Teacher only)
        if "co_id" in self.test_data and "po_id" in self.test_data:
            mapping_data = {
                "co_id": self.test_data["co_id"],
                "po_id": self.test_data["po_id"]
            }
            
            success, response, status = self.make_request("POST", "/co-po-map", mapping_data, self.teacher_token)
            if success and "id" in response:
                self.log_result("Create CO-PO Mapping", True, f"Mapping ID: {response['id']}")
            else:
                self.log_result("Create CO-PO Mapping", False, f"Status: {status}, Response: {response}")
        
        # Test get CO-PO mappings
        if "co_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/co-po-map/co/{self.test_data['co_id']}", token=self.teacher_token)
            if success and isinstance(response, list):
                self.log_result("Get CO-PO Mappings", True, f"Found {len(response)} mappings")
            else:
                self.log_result("Get CO-PO Mappings", False, f"Status: {status}, Response: {response}")

    def test_exam_question_management(self):
        """Test Exam and Question Management"""
        print("\n📝 Testing Exam and Question Management...")
        
        # Test create exam (Teacher only)
        if "course_id" in self.test_data:
            exam_data = {
                "course_id": self.test_data["course_id"],
                "exam_type": "Internal",
                "exam_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            success, response, status = self.make_request("POST", "/exams", exam_data, self.teacher_token)
            if success and "id" in response:
                self.test_data["exam_id"] = response["id"]
                self.log_result("Create Exam", True, f"Exam ID: {response['id']}")
            else:
                self.log_result("Create Exam", False, f"Status: {status}, Response: {response}")
        
        # Test get exams by course
        if "course_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/exams/course/{self.test_data['course_id']}", token=self.teacher_token)
            if success and isinstance(response, list):
                self.log_result("Get Exams by Course", True, f"Found {len(response)} exams")
            else:
                self.log_result("Get Exams by Course", False, f"Status: {status}, Response: {response}")
        
        # Test create question (Teacher only)
        if "exam_id" in self.test_data and "co_id" in self.test_data and "po_id" in self.test_data:
            question_data = {
                "exam_id": self.test_data["exam_id"],
                "text": "Implement a binary search tree and explain its time complexity",
                "max_marks": 10.0,
                "co_id": self.test_data["co_id"],
                "po_ids": [self.test_data["po_id"]]
            }
            
            success, response, status = self.make_request("POST", "/questions", question_data, self.teacher_token)
            if success and "id" in response:
                self.test_data["question_id"] = response["id"]
                self.log_result("Create Question", True, f"Question ID: {response['id']}")
            else:
                self.log_result("Create Question", False, f"Status: {status}, Response: {response}")
        
        # Test get questions by exam
        if "exam_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/questions/exam/{self.test_data['exam_id']}", token=self.teacher_token)
            if success and isinstance(response, list):
                self.log_result("Get Questions by Exam", True, f"Found {len(response)} questions")
            else:
                self.log_result("Get Questions by Exam", False, f"Status: {status}, Response: {response}")

    def test_user_management(self):
        """Test User Management (Students, Teachers, Admins)"""
        print("\n👥 Testing User Management...")
        
        # Test create student (Admin only)
        if "program_id" in self.test_data and "course_id" in self.test_data:
            student_data = {
                "name": "John Doe",
                "roll_number": "CS2021001",
                "email": "john.doe@student.edu",
                "password": "StudentPass123!",
                "semester": 6,
                "program_id": self.test_data["program_id"],
                "course_ids": [self.test_data["course_id"]]
            }
            
            success, response, status = self.make_request("POST", "/admin/students", student_data, self.admin_token)
            if success and "id" in response:
                self.test_data["student_id"] = response["id"]
                self.log_result("Create Student (Admin)", True, f"Student ID: {response['id']}")
            else:
                self.log_result("Create Student (Admin)", False, f"Status: {status}, Response: {response}")
        
        # Test get all students (Admin only)
        success, response, status = self.make_request("GET", "/admin/students", token=self.admin_token)
        if success and isinstance(response, list):
            self.log_result("Get All Students", True, f"Found {len(response)} students")
        else:
            self.log_result("Get All Students", False, f"Status: {status}, Response: {response}")
        
        # Test create teacher (Admin only)
        if "course_id" in self.test_data:
            teacher_data = {
                "name": "Dr. Emily Wilson",
                "email": "emily.wilson@university.edu",
                "password": "TeacherPass456!",
                "assigned_courses": [self.test_data["course_id"]]
            }
            
            success, response, status = self.make_request("POST", "/admin/teachers", teacher_data, self.admin_token)
            if success and "id" in response:
                self.log_result("Create Teacher (Admin)", True, f"Teacher ID: {response['id']}")
            else:
                self.log_result("Create Teacher (Admin)", False, f"Status: {status}, Response: {response}")
        
        # Test get all teachers (Admin only)
        success, response, status = self.make_request("GET", "/admin/teachers", token=self.admin_token)
        if success and isinstance(response, list):
            self.log_result("Get All Teachers", True, f"Found {len(response)} teachers")
        else:
            self.log_result("Get All Teachers", False, f"Status: {status}, Response: {response}")

    def test_student_marks_tracking(self):
        """Test Student Marks Tracking"""
        print("\n📊 Testing Student Marks Tracking...")
        
        # Test create student marks (Teacher only)
        if "student_id" in self.test_data and "question_id" in self.test_data:
            marks_data = {
                "student_id": self.test_data["student_id"],
                "question_id": self.test_data["question_id"],
                "marks_obtained": 8.5
            }
            
            success, response, status = self.make_request("POST", "/student-marks", marks_data, self.teacher_token)
            if success and "id" in response:
                self.log_result("Create Student Marks", True, f"Marks ID: {response['id']}")
            else:
                self.log_result("Create Student Marks", False, f"Status: {status}, Response: {response}")
        
        # Test get student marks
        if "student_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/student-marks/student/{self.test_data['student_id']}", token=self.teacher_token)
            if success and isinstance(response, list):
                self.log_result("Get Student Marks", True, f"Found {len(response)} marks records")
            else:
                self.log_result("Get Student Marks", False, f"Status: {status}, Response: {response}")

    def test_performance_analytics(self):
        """Test Performance Analytics (CO Attainment)"""
        print("\n📈 Testing Performance Analytics...")
        
        # Test student CO attainment
        if "student_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/analytics/student/{self.test_data['student_id']}/co-attainment", token=self.student_token)
            if success and isinstance(response, dict):
                self.log_result("Student CO Attainment", True, f"CO attainment data retrieved")
            else:
                self.log_result("Student CO Attainment", False, f"Status: {status}, Response: {response}")
        
        # Test class CO attainment (Teacher only)
        if "course_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/analytics/course/{self.test_data['course_id']}/class-co-attainment", token=self.teacher_token)
            if success and isinstance(response, dict):
                self.log_result("Class CO Attainment", True, f"Class attainment data retrieved")
            else:
                self.log_result("Class CO Attainment", False, f"Status: {status}, Response: {response}")

    def test_csv_report_generation(self):
        """Test CSV Report Generation"""
        print("\n📄 Testing CSV Report Generation...")
        
        # Test student performance report download
        if "student_id" in self.test_data:
            success, response, status = self.make_request("GET", f"/reports/student/{self.test_data['student_id']}/performance", token=self.admin_token)
            if success or status == 200:
                self.log_result("CSV Report Generation", True, "Report generated successfully")
            else:
                self.log_result("CSV Report Generation", False, f"Status: {status}, Response: {response}")

    def test_role_based_access(self):
        """Test Role-based Access Control"""
        print("\n🔒 Testing Role-based Access Control...")
        
        # Test student trying to access admin endpoint (should fail)
        success, response, status = self.make_request("GET", "/admin/students", token=self.student_token)
        if not success and status == 403:
            self.log_result("Student Access Control", True, "Correctly denied admin access to student")
        else:
            self.log_result("Student Access Control", False, f"Should have denied access. Status: {status}")
        
        # Test teacher trying to create program (should fail - admin only)
        program_data = {"name": "Test Program"}
        success, response, status = self.make_request("POST", "/programs", program_data, self.teacher_token)
        if not success and status == 403:
            self.log_result("Teacher Access Control", True, "Correctly denied program creation to teacher")
        else:
            self.log_result("Teacher Access Control", False, f"Should have denied access. Status: {status}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Comprehensive Backend Testing for CO-PO Student Performance Tracker")
        print("=" * 80)
        
        # Run tests in logical order
        self.test_jwt_authentication()
        self.test_academic_structure()
        self.test_course_program_outcomes()
        self.test_exam_question_management()
        self.test_user_management()
        self.test_student_marks_tracking()
        self.test_performance_analytics()
        self.test_csv_report_generation()
        self.test_role_based_access()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        print(f"📊 Total: {len(self.passed_tests) + len(self.failed_tests)}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        if self.passed_tests:
            print(f"\n✅ Passed Tests:")
            for test in self.passed_tests:
                print(f"   - {test}")
        
        success_rate = len(self.passed_tests) / (len(self.passed_tests) + len(self.failed_tests)) * 100 if (len(self.passed_tests) + len(self.failed_tests)) > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        return len(self.failed_tests) == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)