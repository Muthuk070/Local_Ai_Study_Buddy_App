import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./api/pages/LandingPage";
import Home from "./api/pages/Home";
import Login from "./api/pages/Login";
import Signup from "./api/pages/Signup";
import AdminLogin from "./api/pages/AdminLogin";
import AdminDashboard from "./api/pages/AdminDashboard";
import TeacherDashboard from "./api/pages/TeacherDashboard";
import HigherTeacherDashboard from "./api/pages/HigherTeacherDashboard";
import StudentDashboard from "./api/pages/StudentDashboard";
import UploadNotes from "./api/pages/UploadNotes";
import ChatbotPage from "./api/pages/ChatbotPage"; // ✅ ADD THIS

function App() {
  return (
    <Router>
      <Routes>

        <Route path="/" element={<LandingPage />} />
        <Route path="/home" element={<Home />} />

        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />

        <Route path="/admin-login" element={<AdminLogin />} />
        <Route path="/admin-dashboard" element={<AdminDashboard />} />

        <Route path="/teacher-dashboard" element={<TeacherDashboard />} />
        <Route path="/upload/:className" element={<UploadNotes />} />
        <Route path="/higher-teacher-dashboard" element={<HigherTeacherDashboard />} />

        <Route path="/student-dashboard" element={<StudentDashboard />} />

        {/* ✅ IMPORTANT */}
        <Route path="/chatbot" element={<ChatbotPage />} />

      </Routes>
    </Router>
  );
}

export default App;