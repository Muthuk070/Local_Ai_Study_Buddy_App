import { useNavigate } from "react-router-dom";

const classes = ["Class 9", "Class 10", "Class 11", "Class 12"];

export default function TeacherDashboard() {

  const navigate = useNavigate();

  return (
    <div style={{ textAlign: "center" }}>
      <h2>Teacher Dashboard</h2>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"20px" }}>
        {classes.map((cls) => (
          <div
            key={cls}
            style={{
              padding:"40px",
              background:"#2c2c2c",
              borderRadius:"15px",
              cursor:"pointer"
            }}
            onClick={() => navigate(`/upload/${cls}`)}
          >
            {cls}
          </div>
        ))}
      </div>

    </div>
  );
}