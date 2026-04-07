import { useNavigate } from "react-router-dom";
import studyImage from "../../assets/exact_ai_study_buddy.jpg";

function LandingPage() {
  const navigate = useNavigate();

  return (
    <div style={{ textAlign: "center" }}>
      <img
        src={studyImage}
        alt="Study Buddy"
        style={{ width: "100%", height: "90vh", objectFit: "cover" }}
      />
      <button
        style={{
          padding: "15px 40px",
          fontSize: "18px",
          marginTop: "20px",
        }}
        onClick={() => navigate("/home")}
      >
        Go In
      </button>
    </div>
  );
}

export default LandingPage;
