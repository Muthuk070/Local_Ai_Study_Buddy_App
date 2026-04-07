import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function StudentDashboard() {

  const [data, setData] = useState({});
  const [selectedClass, setSelectedClass] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");

      const res = await axios.get(
        "http://localhost:8000/student/get_student_study_details",
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setData(res.data.available_notes);

    } catch (err) {
      console.log(err);
    }
  };

  return (
    <div style={{ textAlign: "center", padding: "30px", background:"#f5f5f5", minHeight:"100vh" }}>

      <h2 style={{ color:"#333" }}>🎓 Student Dashboard</h2>

      {/* ================= CLASS VIEW ================= */}
      {!selectedClass && Object.keys(data).map((cls) => (
        <div
          key={cls}
          onClick={() => setSelectedClass(cls)}
          style={{
            margin: "20px",
            padding: "40px",
            width: "200px",
            display: "inline-block",
            borderRadius: "20px",
            cursor: "pointer",
            background: "linear-gradient(145deg, #ff9a9e, #fad0c4)",
            color: "#333",
            fontWeight: "bold",
            fontSize: "18px",
            boxShadow: "8px 8px 20px rgba(0,0,0,0.2)",
            position: "relative",
            transition: "0.3s"
          }}
        >
          📘 {cls}

          {/* 🤖 emoji in corner */}
          <span style={{
            position:"absolute",
            top:"10px",
            right:"10px",
            fontSize:"20px"
          }}>
            🤖
          </span>
        </div>
      ))}

      {/* ================= SUBJECT VIEW ================= */}
      {selectedClass && (
        <>
          <h3 style={{ marginTop:"20px" }}>{selectedClass}</h3>

          {data[selectedClass].map((sub) => (
            <div
              key={sub}
              style={{
                margin: "15px auto",
                padding: "20px",
                width: "60%",
                borderRadius: "15px",
                background: "linear-gradient(145deg, #ffffff, #e6e6e6)",
                border: "2px solid darkred",
                boxShadow: "5px 5px 15px rgba(0,0,0,0.2)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
              }}
            >
              <span style={{ fontWeight: "bold" }}>📂 {sub}</span>

              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>

                {/* 🤖 CHAT */}
                <span
                  style={{ cursor:"pointer", fontSize:"22px" }}
                  onClick={() => {
                    navigate("/chatbot", {
                      state: {
                        class_standard: selectedClass,
                        subject: sub
                      }
                    });
                  }}
                >
                  🤖
                </span>

                <button style={{
                  padding: "6px 14px",
                  borderRadius: "8px",
                  border: "none",
                  background: "#ff6b6b",
                  color: "#fff",
                  cursor: "pointer"
                }}>
                  Quiz
                </button>

              </div>
            </div>
          ))}

          <br />
          <button onClick={() => setSelectedClass(null)}>
            🔙 Back
          </button>
        </>
      )}

    </div>
  );
}