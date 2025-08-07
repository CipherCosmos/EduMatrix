import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserProfile();
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      logout();
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      await fetchUserProfile();
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      await fetchUserProfile();
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Components
const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [registerData, setRegisterData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'student',
    semester: 1,
    program_id: ''
  });
  const [programs, setPrograms] = useState([]);
  const { login, register } = useAuth();

  useEffect(() => {
    fetchPrograms();
  }, []);

  const fetchPrograms = async () => {
    try {
      const response = await axios.get(`${API}/programs`);
      setPrograms(response.data);
    } catch (error) {
      console.error('Failed to fetch programs:', error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const success = await login(email, password);
    if (!success) {
      alert('Login failed. Please check your credentials.');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    const success = await register(registerData);
    if (!success) {
      alert('Registration failed. Please try again.');
    }
  };

  if (isRegister) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Register</h2>
          <form onSubmit={handleRegister} className="space-y-4">
            <input
              type="text"
              placeholder="Full Name"
              value={registerData.name}
              onChange={(e) => setRegisterData({...registerData, name: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <input
              type="email"
              placeholder="Email"
              value={registerData.email}
              onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={registerData.password}
              onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <select
              value={registerData.role}
              onChange={(e) => setRegisterData({...registerData, role: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
              <option value="admin">Admin</option>
            </select>
            {registerData.role === 'student' && (
              <>
                <input
                  type="number"
                  placeholder="Semester"
                  value={registerData.semester}
                  onChange={(e) => setRegisterData({...registerData, semester: parseInt(e.target.value)})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <select
                  value={registerData.program_id}
                  onChange={(e) => setRegisterData({...registerData, program_id: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select Program</option>
                  {programs.map(program => (
                    <option key={program.id} value={program.id}>{program.name}</option>
                  ))}
                </select>
              </>
            )}
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition duration-300"
            >
              Register
            </button>
          </form>
          <p className="text-center mt-4 text-gray-600">
            Already have an account?{' '}
            <button
              onClick={() => setIsRegister(false)}
              className="text-blue-600 hover:underline"
            >
              Login
            </button>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
        <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Login</h2>
        <form onSubmit={handleLogin} className="space-y-6">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition duration-300"
          >
            Login
          </button>
        </form>
        <p className="text-center mt-4 text-gray-600">
          Don't have an account?{' '}
          <button
            onClick={() => setIsRegister(true)}
            className="text-blue-600 hover:underline"
          >
            Register
          </button>
        </p>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user, logout } = useAuth();

  const renderUserDashboard = () => {
    switch (user.role) {
      case 'admin':
        return <AdminDashboard />;
      case 'teacher':
        return <TeacherDashboard />;
      case 'student':
        return <StudentDashboard />;
      default:
        return <div>Unknown role</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">CO-PO Performance Tracker</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Welcome, {user.name}</span>
              <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
              </span>
              <button
                onClick={logout}
                className="text-sm text-gray-700 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {renderUserDashboard()}
      </main>
    </div>
  );
};

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('programs');
  const [programs, setPrograms] = useState([]);
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [programOutcomes, setProgramOutcomes] = useState([]);

  useEffect(() => {
    fetchPrograms();
    fetchCourses();
    fetchStudents();
    fetchTeachers();
    fetchProgramOutcomes();
  }, []);

  const fetchPrograms = async () => {
    try {
      const response = await axios.get(`${API}/programs`);
      setPrograms(response.data);
    } catch (error) {
      console.error('Failed to fetch programs:', error);
    }
  };

  const fetchCourses = async () => {
    try {
      const response = await axios.get(`${API}/courses`);
      setCourses(response.data);
    } catch (error) {
      console.error('Failed to fetch courses:', error);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/admin/students`);
      setStudents(response.data);
    } catch (error) {
      console.error('Failed to fetch students:', error);
    }
  };

  const fetchTeachers = async () => {
    try {
      const response = await axios.get(`${API}/admin/teachers`);
      setTeachers(response.data);
    } catch (error) {
      console.error('Failed to fetch teachers:', error);
    }
  };

  const fetchProgramOutcomes = async () => {
    try {
      const response = await axios.get(`${API}/program-outcomes`);
      setProgramOutcomes(response.data);
    } catch (error) {
      console.error('Failed to fetch program outcomes:', error);
    }
  };

  const createProgram = async (name) => {
    try {
      await axios.post(`${API}/programs`, { name });
      fetchPrograms();
    } catch (error) {
      console.error('Failed to create program:', error);
    }
  };

  const createCourse = async (courseData) => {
    try {
      await axios.post(`${API}/courses`, courseData);
      fetchCourses();
    } catch (error) {
      console.error('Failed to create course:', error);
    }
  };

  const createProgramOutcome = async (poData) => {
    try {
      await axios.post(`${API}/program-outcomes`, poData);
      fetchProgramOutcomes();
    } catch (error) {
      console.error('Failed to create program outcome:', error);
    }
  };

  const tabs = [
    { id: 'programs', label: 'Programs', icon: '🎓' },
    { id: 'courses', label: 'Courses', icon: '📚' },
    { id: 'students', label: 'Students', icon: '👨‍🎓' },
    { id: 'teachers', label: 'Teachers', icon: '👩‍🏫' },
    { id: 'outcomes', label: 'Program Outcomes', icon: '🎯' }
  ];

  return (
    <div className="space-y-6">
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'programs' && (
        <ProgramsTab programs={programs} onCreateProgram={createProgram} />
      )}

      {activeTab === 'courses' && (
        <CoursesTab courses={courses} programs={programs} onCreateCourse={createCourse} />
      )}

      {activeTab === 'students' && (
        <StudentsTab students={students} programs={programs} />
      )}

      {activeTab === 'teachers' && (
        <TeachersTab teachers={teachers} />
      )}

      {activeTab === 'outcomes' && (
        <ProgramOutcomesTab programOutcomes={programOutcomes} onCreatePO={createProgramOutcome} />
      )}
    </div>
  );
};

const ProgramsTab = ({ programs, onCreateProgram }) => {
  const [showForm, setShowForm] = useState(false);
  const [programName, setProgramName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreateProgram(programName);
    setProgramName('');
    setShowForm(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Programs</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Add Program
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow">
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Program Name (e.g., BCA, MCA)"
              value={programName}
              onChange={(e) => setProgramName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
            <div className="flex space-x-4">
              <button
                type="submit"
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                Create Program
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {programs.map((program) => (
          <div key={program.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-semibold text-gray-800">{program.name}</h3>
            <p className="text-gray-600 text-sm mt-2">
              Created: {new Date(program.created_at).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

const CoursesTab = ({ courses, programs, onCreateCourse }) => {
  const [showForm, setShowForm] = useState(false);
  const [courseData, setCourseData] = useState({
    name: '',
    semester: 1,
    program_id: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreateCourse(courseData);
    setCourseData({ name: '', semester: 1, program_id: '' });
    setShowForm(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Courses</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Add Course
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Course Name"
              value={courseData.name}
              onChange={(e) => setCourseData({...courseData, name: e.target.value})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
            <input
              type="number"
              placeholder="Semester"
              value={courseData.semester}
              onChange={(e) => setCourseData({...courseData, semester: parseInt(e.target.value)})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
            <select
              value={courseData.program_id}
              onChange={(e) => setCourseData({...courseData, program_id: e.target.value})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select Program</option>
              {programs.map(program => (
                <option key={program.id} value={program.id}>{program.name}</option>
              ))}
            </select>
          </div>
          <div className="flex space-x-4 mt-4">
            <button
              type="submit"
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              Create Course
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {courses.map((course) => {
          const program = programs.find(p => p.id === course.program_id);
          return (
            <div key={course.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
              <h3 className="text-xl font-semibold text-gray-800">{course.name}</h3>
              <p className="text-gray-600">Semester: {course.semester}</p>
              <p className="text-gray-600">Program: {program?.name || 'Unknown'}</p>
              <p className="text-gray-600 text-sm mt-2">
                Created: {new Date(course.created_at).toLocaleDateString()}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const StudentsTab = ({ students, programs }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Students ({students.length})</h2>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {students.map((student) => {
            const program = programs.find(p => p.id === student.program_id);
            return (
              <li key={student.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div>
                      <p className="text-lg font-medium text-gray-900">{student.name}</p>
                      <p className="text-sm text-gray-500">{student.email}</p>
                      {student.roll_number && (
                        <p className="text-sm text-gray-500">Roll: {student.roll_number}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-900">Semester: {student.semester || 'N/A'}</p>
                    <p className="text-sm text-gray-500">Program: {program?.name || 'N/A'}</p>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
};

const TeachersTab = ({ teachers }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Teachers ({teachers.length})</h2>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {teachers.map((teacher) => (
            <li key={teacher.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-lg font-medium text-gray-900">{teacher.name}</p>
                  <p className="text-sm text-gray-500">{teacher.email}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">
                    Courses: {teacher.assigned_courses?.length || 0}
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

const ProgramOutcomesTab = ({ programOutcomes, onCreatePO }) => {
  const [showForm, setShowForm] = useState(false);
  const [poData, setPoData] = useState({
    po_code: '',
    description: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreatePO(poData);
    setPoData({ po_code: '', description: '' });
    setShowForm(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Program Outcomes</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Add Program Outcome
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow">
          <div className="space-y-4">
            <input
              type="text"
              placeholder="PO Code (e.g., PO1, PO2)"
              value={poData.po_code}
              onChange={(e) => setPoData({...poData, po_code: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
            <textarea
              placeholder="Program Outcome Description"
              value={poData.description}
              onChange={(e) => setPoData({...poData, description: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows="3"
              required
            />
            <div className="flex space-x-4">
              <button
                type="submit"
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                Create PO
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {programOutcomes.map((po) => (
          <div key={po.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-semibold text-gray-800">{po.po_code}</h3>
            <p className="text-gray-600 mt-2">{po.description}</p>
            <p className="text-gray-500 text-sm mt-4">
              Created: {new Date(po.created_at).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

const TeacherDashboard = () => {
  const [activeTab, setActiveTab] = useState('courses');
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [courseOutcomes, setCourseOutcomes] = useState([]);
  const [exams, setExams] = useState([]);
  const [classAttainment, setClassAttainment] = useState({});

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    if (selectedCourse) {
      fetchCourseOutcomes(selectedCourse);
      fetchExams(selectedCourse);
      fetchClassAttainment(selectedCourse);
    }
  }, [selectedCourse]);

  const fetchCourses = async () => {
    try {
      const response = await axios.get(`${API}/courses`);
      setCourses(response.data);
      if (response.data.length > 0) {
        setSelectedCourse(response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch courses:', error);
    }
  };

  const fetchCourseOutcomes = async (courseId) => {
    try {
      const response = await axios.get(`${API}/course-outcomes/course/${courseId}`);
      setCourseOutcomes(response.data);
    } catch (error) {
      console.error('Failed to fetch course outcomes:', error);
    }
  };

  const fetchExams = async (courseId) => {
    try {
      const response = await axios.get(`${API}/exams/course/${courseId}`);
      setExams(response.data);
    } catch (error) {
      console.error('Failed to fetch exams:', error);
    }
  };

  const fetchClassAttainment = async (courseId) => {
    try {
      const response = await axios.get(`${API}/analytics/course/${courseId}/class-co-attainment`);
      setClassAttainment(response.data);
    } catch (error) {
      console.error('Failed to fetch class attainment:', error);
    }
  };

  const tabs = [
    { id: 'courses', label: 'My Courses', icon: '📚' },
    { id: 'outcomes', label: 'Course Outcomes', icon: '🎯' },
    { id: 'exams', label: 'Exams & Questions', icon: '📝' },
    { id: 'analytics', label: 'Class Performance', icon: '📊' }
  ];

  return (
    <div className="space-y-6">
      {courses.length > 0 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Course</label>
          <select
            value={selectedCourse || ''}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {courses.map(course => (
              <option key={course.id} value={course.id}>
                {course.name} (Semester {course.semester})
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'courses' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course) => (
            <div key={course.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
              <h3 className="text-xl font-semibold text-gray-800">{course.name}</h3>
              <p className="text-gray-600">Semester: {course.semester}</p>
              <button
                onClick={() => setSelectedCourse(course.id)}
                className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Manage Course
              </button>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'outcomes' && selectedCourse && (
        <CourseOutcomesManagement courseId={selectedCourse} courseOutcomes={courseOutcomes} onUpdate={() => fetchCourseOutcomes(selectedCourse)} />
      )}

      {activeTab === 'exams' && selectedCourse && (
        <ExamsManagement courseId={selectedCourse} exams={exams} courseOutcomes={courseOutcomes} onUpdate={() => {fetchExams(selectedCourse); fetchClassAttainment(selectedCourse);}} />
      )}

      {activeTab === 'analytics' && selectedCourse && (
        <ClassPerformanceAnalytics classAttainment={classAttainment} />
      )}
    </div>
  );
};

const CourseOutcomesManagement = ({ courseId, courseOutcomes, onUpdate }) => {
  const [showForm, setShowForm] = useState(false);
  const [coData, setCoData] = useState({
    co_code: '',
    description: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/course-outcomes`, {
        ...coData,
        course_id: courseId
      });
      setCoData({ co_code: '', description: '' });
      setShowForm(false);
      onUpdate();
    } catch (error) {
      console.error('Failed to create course outcome:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Course Outcomes</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Add Course Outcome
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow">
          <div className="space-y-4">
            <input
              type="text"
              placeholder="CO Code (e.g., CO1, CO2)"
              value={coData.co_code}
              onChange={(e) => setCoData({...coData, co_code: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
            <textarea
              placeholder="Course Outcome Description"
              value={coData.description}
              onChange={(e) => setCoData({...coData, description: e.target.value})}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows="3"
              required
            />
            <div className="flex space-x-4">
              <button
                type="submit"
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                Create CO
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {courseOutcomes.map((co) => (
          <div key={co.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-semibold text-gray-800">{co.co_code}</h3>
            <p className="text-gray-600 mt-2">{co.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const ExamsManagement = ({ courseId, exams, courseOutcomes, onUpdate }) => {
  const [showExamForm, setShowExamForm] = useState(false);
  const [selectedExam, setSelectedExam] = useState(null);
  const [examData, setExamData] = useState({
    exam_type: 'Internal',
    exam_date: new Date().toISOString().split('T')[0]
  });

  const createExam = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/exams`, {
        ...examData,
        course_id: courseId,
        exam_date: new Date(examData.exam_date)
      });
      setExamData({ exam_type: 'Internal', exam_date: new Date().toISOString().split('T')[0] });
      setShowExamForm(false);
      onUpdate();
    } catch (error) {
      console.error('Failed to create exam:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Exams & Questions</h2>
        <button
          onClick={() => setShowExamForm(!showExamForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Create Exam
        </button>
      </div>

      {showExamForm && (
        <form onSubmit={createExam} className="bg-white p-6 rounded-lg shadow">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select
              value={examData.exam_type}
              onChange={(e) => setExamData({...examData, exam_type: e.target.value})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="Internal">Internal Exam</option>
              <option value="Final">Final Exam</option>
            </select>
            <input
              type="date"
              value={examData.exam_date}
              onChange={(e) => setExamData({...examData, exam_date: e.target.value})}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="flex space-x-4 mt-4">
            <button
              type="submit"
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              Create Exam
            </button>
            <button
              type="button"
              onClick={() => setShowExamForm(false)}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {exams.map((exam) => (
          <div key={exam.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="text-xl font-semibold text-gray-800">{exam.exam_type} Exam</h3>
            <p className="text-gray-600">Date: {new Date(exam.exam_date).toLocaleDateString()}</p>
            <button
              onClick={() => setSelectedExam(selectedExam === exam.id ? null : exam.id)}
              className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              {selectedExam === exam.id ? 'Hide Questions' : 'Manage Questions'}
            </button>
            {selectedExam === exam.id && (
              <QuestionsManagement examId={exam.id} courseOutcomes={courseOutcomes} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const QuestionsManagement = ({ examId, courseOutcomes }) => {
  const [questions, setQuestions] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [questionData, setQuestionData] = useState({
    text: '',
    max_marks: 10,
    co_id: ''
  });

  useEffect(() => {
    fetchQuestions();
  }, [examId]);

  const fetchQuestions = async () => {
    try {
      const response = await axios.get(`${API}/questions/exam/${examId}`);
      setQuestions(response.data);
    } catch (error) {
      console.error('Failed to fetch questions:', error);
    }
  };

  const createQuestion = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/questions`, {
        ...questionData,
        exam_id: examId
      });
      setQuestionData({ text: '', max_marks: 10, co_id: '' });
      setShowForm(false);
      fetchQuestions();
    } catch (error) {
      console.error('Failed to create question:', error);
    }
  };

  return (
    <div className="mt-6 space-y-4 border-t pt-4">
      <div className="flex justify-between items-center">
        <h4 className="text-lg font-semibold">Questions</h4>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-green-600 text-white px-3 py-1 text-sm rounded hover:bg-green-700"
        >
          Add Question
        </button>
      </div>

      {showForm && (
        <form onSubmit={createQuestion} className="space-y-3 bg-gray-50 p-4 rounded">
          <textarea
            placeholder="Question text"
            value={questionData.text}
            onChange={(e) => setQuestionData({...questionData, text: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            rows="2"
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              type="number"
              placeholder="Max marks"
              value={questionData.max_marks}
              onChange={(e) => setQuestionData({...questionData, max_marks: parseFloat(e.target.value)})}
              className="px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              required
            />
            <select
              value={questionData.co_id}
              onChange={(e) => setQuestionData({...questionData, co_id: e.target.value})}
              className="px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select CO</option>
              {courseOutcomes.map(co => (
                <option key={co.id} value={co.id}>{co.co_code}</option>
              ))}
            </select>
          </div>
          <div className="flex space-x-2">
            <button
              type="submit"
              className="bg-green-600 text-white px-3 py-1 text-sm rounded hover:bg-green-700"
            >
              Add
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="bg-gray-600 text-white px-3 py-1 text-sm rounded hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="space-y-2">
        {questions.map((question) => {
          const co = courseOutcomes.find(c => c.id === question.co_id);
          return (
            <div key={question.id} className="bg-gray-50 p-3 rounded">
              <p className="text-sm">{question.text}</p>
              <div className="flex justify-between items-center mt-2 text-xs text-gray-600">
                <span>Max Marks: {question.max_marks}</span>
                <span>CO: {co?.co_code || 'Unknown'}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const ClassPerformanceAnalytics = ({ classAttainment }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Class Performance Analytics</h2>
      
      {Object.keys(classAttainment).length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <p className="text-gray-500">No performance data available yet. Add exams, questions, and student marks to see analytics.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(classAttainment).map(([coId, data]) => (
            <div key={coId} className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-800">{data.co_code}</h3>
              <p className="text-gray-600 text-sm mb-4">{data.description}</p>
              
              <div className="bg-gray-50 p-4 rounded">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">Class Average</span>
                  <span className="text-lg font-bold text-blue-600">{data.class_average}%</span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${Math.min(data.class_average, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Individual Student Performance</h4>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {data.student_attainments.map((student, index) => (
                    <div key={index} className="flex justify-between items-center text-sm">
                      <span className="text-gray-600">{student.student_name}</span>
                      <span className={`font-medium ${
                        student.attainment_percentage >= 60 ? 'text-green-600' : 
                        student.attainment_percentage >= 40 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {student.attainment_percentage}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const StudentDashboard = () => {
  const { user } = useAuth();
  const [coAttainment, setCoAttainment] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user && user.id) {
      fetchStudentAttainment();
    }
  }, [user]);

  const fetchStudentAttainment = async () => {
    try {
      const response = await axios.get(`${API}/analytics/student/${user.id}/co-attainment`);
      setCoAttainment(response.data);
    } catch (error) {
      console.error('Failed to fetch student attainment:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async () => {
    try {
      const response = await axios.get(`${API}/reports/student/${user.id}/performance`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `performance_report_${user.name}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to download report:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">My Performance Dashboard</h2>
          <p className="text-gray-600">Track your CO attainment and academic progress</p>
        </div>
        <button
          onClick={downloadReport}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
        >
          Download Report (CSV)
        </button>
      </div>

      {Object.keys(coAttainment).length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <p className="text-gray-500">No performance data available yet. Your teachers will add exam results soon.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(coAttainment).map(([coId, data]) => (
              <div key={coId} className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">{data.co_code}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    data.attainment_percentage >= 60 ? 'bg-green-100 text-green-800' :
                    data.attainment_percentage >= 40 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {data.attainment_percentage}%
                  </span>
                </div>
                
                <p className="text-gray-600 text-sm mb-4">{data.description}</p>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Marks Obtained:</span>
                    <span className="font-medium">{data.obtained_marks}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Total Marks:</span>
                    <span className="font-medium">{data.total_marks}</span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div
                      className={`h-2 rounded-full ${
                        data.attainment_percentage >= 60 ? 'bg-green-600' :
                        data.attainment_percentage >= 40 ? 'bg-yellow-600' :
                        'bg-red-600'
                      }`}
                      style={{ width: `${Math.min(data.attainment_percentage, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Overall Performance Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Object.values(coAttainment).filter(data => data.attainment_percentage >= 60).length}
                </div>
                <p className="text-sm text-gray-600">Excellent (≥60%)</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {Object.values(coAttainment).filter(data => data.attainment_percentage >= 40 && data.attainment_percentage < 60).length}
                </div>
                <p className="text-sm text-gray-600">Good (40-59%)</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {Object.values(coAttainment).filter(data => data.attainment_percentage < 40).length}
                </div>
                <p className="text-sm text-gray-600">Needs Improvement (&lt;40%)</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <AuthenticatedApp />
      </div>
    </AuthProvider>
  );
}

const AuthenticatedApp = () => {
  const { user, token } = useAuth();

  if (!token) {
    return <Login />;
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return <Dashboard />;
};

export default App;