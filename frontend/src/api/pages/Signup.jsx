import { useState } from "react";
import axios from "axios";

function Signup() {
  const [user_name, setUserName] = useState("");
  const [password, setPassword] = useState("");

  const handleSignup = async () => {
    try {
      const res = await axios.post("http://localhost:8000/auth/signup", {
        user_name,
        password,
      });

      alert(res.data.message + "\nUser ID: " + res.data.user_id);
    } catch (err) {
      alert("Signup Failed");
    }
  };

  return (
    <div style={{ textAlign: "center" }}>
      <h2>Student Signup</h2>
      <input placeholder="Username" onChange={(e) => setUserName(e.target.value)} /><br /><br />
      <input type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} /><br /><br />
      <button onClick={handleSignup}>Signup</button>
    </div>
  );
}

export default Signup;