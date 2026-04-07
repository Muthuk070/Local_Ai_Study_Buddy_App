function AdminDashboard() {
  return (
    <div style={{ textAlign: "center" }}>
      <h2>Admin Dashboard</h2>

      <button style={{ display: "block", margin: "20px auto", padding: "15px 40px" }}>
        Admin User Creation
      </button>

      <button style={{ display: "block", margin: "20px auto", padding: "15px 40px" }}>
        Admin User View For Edits
      </button>

      <button style={{ display: "block", margin: "20px auto", padding: "15px 40px" }}>
        Admin Users Deletion
      </button>
    </div>
  );
}

export default AdminDashboard;

