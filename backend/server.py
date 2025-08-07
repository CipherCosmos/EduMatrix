from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import csv
import io
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
from functools import lru_cache

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with optimized settings
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,  # Increased connection pool
    minPoolSize=10,  # Minimum connections
    maxIdleTimeMS=30000,  # Keep connections alive longer
    serverSelectionTimeoutMS=5000,  # Faster server selection
    connectTimeoutMS=10000,  # Faster connection timeout
    socketTimeoutMS=30000,  # Socket timeout
    waitQueueTimeoutMS=5000,  # Wait queue timeout
    retryWrites=True,  # Enable retry writes
    retryReads=True,  # Enable retry reads
)
db = client[os.environ.get('DB_NAME', 'edumatrix')]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Create indexes for better query performance
    try:
        await db.users.create_index("email", unique=True)
        await db.users.create_index("role")
        await db.programs.create_index("name")
        await db.courses.create_index("program_id")
        await db.courses.create_index("semester")
        await db.course_outcomes.create_index("course_id")
        await db.program_outcomes.create_index("po_code")
        await db.co_po_maps.create_index("co_id")
        await db.co_po_maps.create_index("po_id")
        await db.exams.create_index("course_id")
        await db.questions.create_index("exam_id")
        await db.questions.create_index("co_id")
        await db.student_marks.create_index("student_id")
        await db.student_marks.create_index("question_id")
        logging.info("Database indexes created successfully")
    except Exception as e:
        logging.warning(f"Some indexes may already exist: {e}")
    
    yield
    # Shutdown
    client.close()

# Create the main app with performance optimizations
app = FastAPI(
    title="CO-PO Student Performance Tracker", 
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add GZip compression middleware for faster responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket endpoint to handle connection attempts
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Keep the connection alive but don't process any messages
            data = await websocket.receive_text()
            # Echo back to acknowledge receipt
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        # Connection closed normally
        pass
    except Exception as e:
        # Handle any other errors
        logging.warning(f"WebSocket error: {e}")

# Auth configuration
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cache for frequently accessed data
_cache = {}

def get_cache_key(prefix: str, key: str) -> str:
    return f"{prefix}:{key}"

async def get_cached_data(cache_key: str, ttl: int = 300):
    """Get data from cache with TTL"""
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if datetime.utcnow().timestamp() - timestamp < ttl:
            return data
        else:
            del _cache[cache_key]
    return None

def set_cached_data(cache_key: str, data: Any):
    """Set data in cache with timestamp"""
    _cache[cache_key] = (data, datetime.utcnow().timestamp())

# Optimized Pydantic Models with better performance
class UserBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    role: str  # student, teacher, admin
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True  # Faster serialization

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    semester: Optional[int] = None
    program_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
    class Config:
        from_attributes = True

class Program(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class ProgramCreate(BaseModel):
    name: str
    
    class Config:
        from_attributes = True

class Course(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    semester: int
    program_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    name: str
    semester: int
    program_id: str
    
    class Config:
        from_attributes = True

class CourseOutcome(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    course_id: str
    co_code: str  # CO1, CO2, etc.
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class CourseOutcomeCreate(BaseModel):
    course_id: str
    co_code: str
    description: str
    
    class Config:
        from_attributes = True

class ProgramOutcome(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    po_code: str  # PO1, PO2, etc.
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class ProgramOutcomeCreate(BaseModel):
    po_code: str
    description: str
    
    class Config:
        from_attributes = True

class COPOMap(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    co_id: str
    po_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class COPOMapCreate(BaseModel):
    co_id: str
    po_id: str
    
    class Config:
        from_attributes = True

class Exam(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    course_id: str
    exam_type: str  # Internal, Final
    exam_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class ExamCreate(BaseModel):
    course_id: str
    exam_type: str
    exam_date: datetime
    
    class Config:
        from_attributes = True

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exam_id: str
    text: str
    max_marks: float
    co_id: str
    po_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    exam_id: str
    text: str
    max_marks: float
    co_id: str
    po_ids: List[str] = []
    
    class Config:
        from_attributes = True

class StudentMarks(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    question_id: str
    marks_obtained: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class StudentMarksCreate(BaseModel):
    student_id: str
    question_id: str
    marks_obtained: float
    
    class Config:
        from_attributes = True

class Student(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    roll_number: str
    email: EmailStr
    password_hash: str
    semester: int
    program_id: str
    course_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class StudentCreate(BaseModel):
    name: str
    roll_number: str
    email: EmailStr
    password: str
    semester: int
    program_id: str
    course_ids: List[str] = []
    
    class Config:
        from_attributes = True

class Teacher(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    password_hash: str
    assigned_courses: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    assigned_courses: List[str] = []
    
    class Config:
        from_attributes = True

# Auth helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return user

def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user
    return role_checker

# Authentication routes
@api_router.post("/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict.pop("password")
    user_dict["password_hash"] = hashed_password
    user_dict["id"] = str(uuid.uuid4())
    user_dict["created_at"] = datetime.utcnow()
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # Remove MongoDB ObjectId for JSON serialization
    user_data = current_user.copy()
    user_data.pop("_id", None)
    user_data.pop("password_hash", None)
    return user_data

# Program routes
@api_router.post("/programs", response_model=Program)
async def create_program(program: ProgramCreate, current_user: dict = Depends(require_role("admin"))):
    program_dict = program.dict()
    program_obj = Program(**program_dict)
    await db.programs.insert_one(program_obj.dict())
    return program_obj

@api_router.get("/programs", response_model=List[Program])
async def get_programs(current_user: dict = Depends(get_current_user)):
    # Check cache first
    cache_key = get_cache_key("programs", "all")
    cached_data = await get_cached_data(cache_key, ttl=60)  # Cache for 1 minute
    if cached_data:
        return cached_data
    
    # Optimized query with projection
    programs = await db.programs.find({}, {"_id": 0}).to_list(1000)
    result = [Program(**program) for program in programs]
    
    # Cache the result
    set_cached_data(cache_key, result)
    return result

@api_router.get("/public/programs", response_model=List[Program])
async def get_public_programs():
    # Check cache first
    cache_key = get_cache_key("public_programs", "all")
    cached_data = await get_cached_data(cache_key, ttl=60)  # Cache for 1 minute
    if cached_data:
        return cached_data
    
    # Optimized query with projection
    programs = await db.programs.find({}, {"_id": 0}).to_list(1000)
    result = [Program(**program) for program in programs]
    
    # Cache the result
    set_cached_data(cache_key, result)
    return result

# Course routes
@api_router.post("/courses", response_model=Course)
async def create_course(course: CourseCreate, current_user: dict = Depends(require_role("admin"))):
    course_dict = course.dict()
    course_obj = Course(**course_dict)
    await db.courses.insert_one(course_obj.dict())
    return course_obj

@api_router.get("/courses", response_model=List[Course])
async def get_courses(current_user: dict = Depends(get_current_user)):
    # Check cache first
    cache_key = get_cache_key("courses", "all")
    cached_data = await get_cached_data(cache_key, ttl=60)  # Cache for 1 minute
    if cached_data:
        return cached_data
    
    # Optimized query with projection
    courses = await db.courses.find({}, {"_id": 0}).to_list(1000)
    result = [Course(**course) for course in courses]
    
    # Cache the result
    set_cached_data(cache_key, result)
    return result

@api_router.get("/courses/program/{program_id}", response_model=List[Course])
async def get_courses_by_program(program_id: str, current_user: dict = Depends(get_current_user)):
    # Check cache first
    cache_key = get_cache_key("courses", f"program_{program_id}")
    cached_data = await get_cached_data(cache_key, ttl=60)  # Cache for 1 minute
    if cached_data:
        return cached_data
    
    # Optimized query with projection and index usage
    courses = await db.courses.find({"program_id": program_id}, {"_id": 0}).to_list(1000)
    result = [Course(**course) for course in courses]
    
    # Cache the result
    set_cached_data(cache_key, result)
    return result

# Course Outcome routes
@api_router.post("/course-outcomes", response_model=CourseOutcome)
async def create_course_outcome(co: CourseOutcomeCreate, current_user: dict = Depends(require_role("teacher"))):
    co_dict = co.dict()
    co_obj = CourseOutcome(**co_dict)
    await db.course_outcomes.insert_one(co_obj.dict())
    return co_obj

@api_router.get("/course-outcomes/course/{course_id}", response_model=List[CourseOutcome])
async def get_course_outcomes_by_course(course_id: str, current_user: dict = Depends(get_current_user)):
    # Check cache first
    cache_key = get_cache_key("course_outcomes", f"course_{course_id}")
    cached_data = await get_cached_data(cache_key, ttl=60)  # Cache for 1 minute
    if cached_data:
        return cached_data
    
    # Optimized query with projection and index usage
    cos = await db.course_outcomes.find({"course_id": course_id}, {"_id": 0}).to_list(1000)
    result = [CourseOutcome(**co) for co in cos]
    
    # Cache the result
    set_cached_data(cache_key, result)
    return result

# Program Outcome routes
@api_router.post("/program-outcomes", response_model=ProgramOutcome)
async def create_program_outcome(po: ProgramOutcomeCreate, current_user: dict = Depends(require_role("admin"))):
    po_dict = po.dict()
    po_obj = ProgramOutcome(**po_dict)
    await db.program_outcomes.insert_one(po_obj.dict())
    
    # Clear cache after creating new program outcome
    cache_key = get_cache_key("program_outcomes", "all")
    if cache_key in _cache:
        del _cache[cache_key]
    
    return po_obj

@api_router.get("/program-outcomes", response_model=List[ProgramOutcome])
async def get_program_outcomes(current_user: dict = Depends(get_current_user)):
    # Check cache first
    cache_key = get_cache_key("program_outcomes", "all")
    cached_data = await get_cached_data(cache_key, ttl=60)  # Cache for 1 minute
    if cached_data:
        return cached_data
    
    # Optimized query with projection
    pos = await db.program_outcomes.find({}, {"_id": 0}).to_list(1000)
    result = [ProgramOutcome(**po) for po in pos]
    
    # Cache the result
    set_cached_data(cache_key, result)
    return result

# CO-PO Mapping routes
@api_router.post("/co-po-map", response_model=COPOMap)
async def create_co_po_mapping(mapping: COPOMapCreate, current_user: dict = Depends(require_role("teacher"))):
    mapping_dict = mapping.dict()
    mapping_obj = COPOMap(**mapping_dict)
    await db.co_po_maps.insert_one(mapping_obj.dict())
    return mapping_obj

@api_router.get("/co-po-map/co/{co_id}", response_model=List[COPOMap])
async def get_co_po_mappings_by_co(co_id: str, current_user: dict = Depends(get_current_user)):
    mappings = await db.co_po_maps.find({"co_id": co_id}).to_list(1000)
    return [COPOMap(**mapping) for mapping in mappings]

# Exam routes
@api_router.post("/exams", response_model=Exam)
async def create_exam(exam: ExamCreate, current_user: dict = Depends(require_role("teacher"))):
    exam_dict = exam.dict()
    exam_obj = Exam(**exam_dict)
    await db.exams.insert_one(exam_obj.dict())
    return exam_obj

@api_router.get("/exams/course/{course_id}", response_model=List[Exam])
async def get_exams_by_course(course_id: str, current_user: dict = Depends(get_current_user)):
    exams = await db.exams.find({"course_id": course_id}).to_list(1000)
    return [Exam(**exam) for exam in exams]

# Question routes
@api_router.post("/questions", response_model=Question)
async def create_question(question: QuestionCreate, current_user: dict = Depends(require_role("teacher"))):
    question_dict = question.dict()
    question_obj = Question(**question_dict)
    await db.questions.insert_one(question_obj.dict())
    return question_obj

@api_router.get("/questions/exam/{exam_id}", response_model=List[Question])
async def get_questions_by_exam(exam_id: str, current_user: dict = Depends(get_current_user)):
    questions = await db.questions.find({"exam_id": exam_id}).to_list(1000)
    return [Question(**question) for question in questions]

# Student Marks routes
@api_router.post("/student-marks", response_model=StudentMarks)
async def create_student_marks(marks: StudentMarksCreate, current_user: dict = Depends(require_role("teacher"))):
    marks_dict = marks.dict()
    marks_obj = StudentMarks(**marks_dict)
    await db.student_marks.insert_one(marks_obj.dict())
    return marks_obj

@api_router.get("/student-marks/student/{student_id}", response_model=List[StudentMarks])
async def get_student_marks(student_id: str, current_user: dict = Depends(get_current_user)):
    marks = await db.student_marks.find({"student_id": student_id}).to_list(1000)
    return [StudentMarks(**mark) for mark in marks]

# Performance Analytics routes
@api_router.get("/analytics/student/{student_id}/co-attainment")
async def get_student_co_attainment(student_id: str, current_user: dict = Depends(get_current_user)):
    # Calculate CO attainment for a student
    student_marks = await db.student_marks.find({"student_id": student_id}).to_list(1000)
    
    co_performance = {}
    for mark in student_marks:
        # Get question details
        question = await db.questions.find_one({"id": mark["question_id"]})
        if question:
            co_id = question["co_id"]
            if co_id not in co_performance:
                co_performance[co_id] = {"total_marks": 0, "obtained_marks": 0}
            
            co_performance[co_id]["total_marks"] += question["max_marks"]
            co_performance[co_id]["obtained_marks"] += mark["marks_obtained"]
    
    # Calculate attainment percentages
    attainment_data = {}
    for co_id, data in co_performance.items():
        attainment_percentage = (data["obtained_marks"] / data["total_marks"]) * 100 if data["total_marks"] > 0 else 0
        co = await db.course_outcomes.find_one({"id": co_id})
        attainment_data[co_id] = {
            "co_code": co["co_code"] if co else "Unknown",
            "description": co["description"] if co else "Unknown",
            "attainment_percentage": round(attainment_percentage, 2),
            "total_marks": data["total_marks"],
            "obtained_marks": data["obtained_marks"]
        }
    
    return attainment_data

@api_router.get("/analytics/course/{course_id}/class-co-attainment")
async def get_class_co_attainment(course_id: str, current_user: dict = Depends(require_role("teacher"))):
    # Get all students enrolled in the course
    students = await db.users.find({
        "role": "student",
        "course_ids": {"$in": [course_id]}
    }).to_list(1000)
    
    class_co_attainment = {}
    
    for student in students:
        student_attainment = await get_student_co_attainment(student["id"], current_user)
        
        for co_id, data in student_attainment.items():
            if co_id not in class_co_attainment:
                class_co_attainment[co_id] = {
                    "co_code": data["co_code"],
                    "description": data["description"],
                    "student_attainments": []
                }
            
            class_co_attainment[co_id]["student_attainments"].append({
                "student_name": student["name"],
                "attainment_percentage": data["attainment_percentage"]
            })
    
    # Calculate class average for each CO
    for co_id, data in class_co_attainment.items():
        attainments = [s["attainment_percentage"] for s in data["student_attainments"]]
        data["class_average"] = round(sum(attainments) / len(attainments), 2) if attainments else 0
    
    return class_co_attainment

# Report generation routes
@api_router.get("/reports/student/{student_id}/performance")
async def download_student_performance_report(student_id: str, current_user: dict = Depends(get_current_user)):
    # Get student details
    student = await db.users.find_one({"id": student_id, "role": "student"})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get CO attainment
    co_attainment = await get_student_co_attainment(student_id, current_user)
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["Student Performance Report"])
    writer.writerow(["Student Name", student["name"]])
    writer.writerow(["Email", student["email"]])
    writer.writerow(["Semester", student.get("semester", "N/A")])
    writer.writerow([])
    writer.writerow(["CO Code", "Description", "Total Marks", "Obtained Marks", "Attainment %"])
    
    # Write CO attainment data
    for co_id, data in co_attainment.items():
        writer.writerow([
            data["co_code"],
            data["description"],
            data["total_marks"],
            data["obtained_marks"],
            data["attainment_percentage"]
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=student_{student_id}_performance.csv"}
    )

# Student management routes (Admin only)
@api_router.post("/admin/students", response_model=Student)
async def create_student(student: StudentCreate, current_user: dict = Depends(require_role("admin"))):
    # Check if student already exists
    existing_student = await db.users.find_one({"email": student.email})
    if existing_student:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create student
    hashed_password = get_password_hash(student.password)
    student_dict = student.dict()
    student_dict.pop("password")
    student_dict["password_hash"] = hashed_password
    student_dict["id"] = str(uuid.uuid4())
    student_dict["role"] = "student"
    student_dict["created_at"] = datetime.utcnow()
    
    await db.users.insert_one(student_dict)
    return Student(**student_dict)

@api_router.get("/admin/students", response_model=List[dict])
async def get_all_students(current_user: dict = Depends(require_role("admin"))):
    # Check cache first
    cache_key = get_cache_key("admin_students", "all")
    cached_data = await get_cached_data(cache_key, ttl=30)  # Cache for 30 seconds
    if cached_data:
        return cached_data
    
    # Optimized query with projection to exclude sensitive data
    students = await db.users.find(
        {"role": "student"}, 
        {"password_hash": 0, "_id": 0}
    ).to_list(1000)
    
    # Cache the result
    set_cached_data(cache_key, students)
    return students

# Teacher management routes (Admin only)
@api_router.post("/admin/teachers", response_model=Teacher)
async def create_teacher(teacher: TeacherCreate, current_user: dict = Depends(require_role("admin"))):
    # Check if teacher already exists
    existing_teacher = await db.users.find_one({"email": teacher.email})
    if existing_teacher:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create teacher
    hashed_password = get_password_hash(teacher.password)
    teacher_dict = teacher.dict()
    teacher_dict.pop("password")
    teacher_dict["password_hash"] = hashed_password
    teacher_dict["id"] = str(uuid.uuid4())
    teacher_dict["role"] = "teacher"
    teacher_dict["created_at"] = datetime.utcnow()
    
    await db.users.insert_one(teacher_dict)
    
    # Clear cache after creating new teacher
    cache_key = get_cache_key("admin_teachers", "all")
    if cache_key in _cache:
        del _cache[cache_key]
    
    return Teacher(**teacher_dict)

@api_router.get("/admin/teachers", response_model=List[dict])
async def get_all_teachers(current_user: dict = Depends(require_role("admin"))):
    # Check cache first
    cache_key = get_cache_key("admin_teachers", "all")
    cached_data = await get_cached_data(cache_key, ttl=30)  # Cache for 30 seconds
    if cached_data:
        return cached_data
    
    # Optimized query with projection to exclude sensitive data
    teachers = await db.users.find(
        {"role": "teacher"}, 
        {"password_hash": 0, "_id": 0}
    ).to_list(1000)
    
    # Cache the result
    set_cached_data(cache_key, teachers)
    return teachers

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging with performance optimizations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Performance monitoring
import time
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > 1.0:  # Log slow operations
                logger.warning(f"Slow operation detected: {func.__name__} took {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {execution_time:.2f}s: {e}")
            raise
    return wrapper

# Apply performance monitoring to key endpoints

# Add main block to run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )