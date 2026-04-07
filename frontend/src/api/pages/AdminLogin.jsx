import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function AdminLogin() {
  const [user_id, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleAdminLogin = async () => {
    try {
      const res = await axios.post("http://localhost:8000/auth/admin/login", {
        user_id,
        password,
      });

      localStorage.setItem("token", res.data.access_token);
      navigate("/admin-dashboard");
    } catch {
      alert("Admin Login Failed");
    }
  };

  return (
    <div style={{ textAlign: "center" }}>
      <h2>Admin Login</h2>
      <input placeholder="User ID" onChange={(e) => setUserId(e.target.value)} /><br /><br />
      <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} /><br /><br />
      <button onClick={handleAdminLogin}>Login</button>
    </div>
  );
}

export default AdminLogin;

