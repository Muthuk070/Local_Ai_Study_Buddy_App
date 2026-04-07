import { useNavigate } from "react-router-dom";
import studyImage from "../../assets/chatbot_image.jpg"; 

function Home() {
  const navigate = useNavigate();

  return (
    <div style={{ textAlign: "center" }}>
      <img
        src={studyImage}
        alt="Study"
        style={{ width: "50%", height: "300px", objectFit: "contain" }}
      />

      <div style={{ display: "flex", justifyContent: "center", gap: "20px", marginTop: "30px" }}>
        <button onClick={() => navigate("/admin-login")}>Admin</button>
        <button onClick={() => navigate("/signup")}>Student</button>
        <button onClick={() => navigate("/login")}>Users Login</button>
      </div>
    </div>
  );
}

export default Home;

