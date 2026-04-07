import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();
  const [user_id, setUserId] = useState("");

  const handleLogin = async () => {
    try {
      const res = await axios.post("http://localhost:8000/auth/login", {
        user_id,
      });

      alert(res.data.message);

      localStorage.setItem("token", res.data.access_token);
      localStorage.setItem("role", res.data.role);
      localStorage.setItem("username", res.data.username);

      const role = res.data.role;

      if (role === "teacher") {
        navigate("/teacher-dashboard");
      } 
      else if (role === "student") {
        navigate("/student-dashboard");
      } 
      else if (role === "higher_teacher") {
        navigate("/higher-teacher-dashboard");
      } 
      else if (role === "admin") {
        navigate("/admin-dashboard");
      }

    } catch (error) {
      if (error.response) {
        alert(error.response.data.detail);
      } else if (error.request) {
        alert("Server not responding");
      } else {
        alert("Something went wrong");
      }
    }
  };

  return (
    <div style={{ textAlign: "center" }}>
      <h2>User Login</h2>

      <input
        placeholder="User ID"
        onChange={(e) => setUserId(e.target.value)}
      />

      <br /><br />

      <button onClick={handleLogin}>Login</button>
    </div>
  );
}

export default Login;