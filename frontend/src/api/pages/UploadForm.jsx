import { useParams } from "react-router-dom";
import { useState } from "react";
import axios from "axios";

export default function UploadNotes() {

  const { className } = useParams();

  const [subject, setSubject] = useState("");
  const [file, setFile] = useState(null);

  const handleUpload = async () => {

    const formData = new FormData();

    formData.append("class_standard", className);
    formData.append("subject", subject);
    formData.append("file", file);

    try {

      const token = localStorage.getItem("token");

      await axios.post(
        "http://localhost:8000/teacher/upload_notes",
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      alert("Notes uploaded successfully");

    } catch (error) {
      alert("Upload failed");
      console.log(error);
    }

  };

  return (

    <div style={{ textAlign:"center", marginTop:"40px" }}>

      <h2>Upload Notes for {className}</h2>

      <br/>

      <input
        placeholder="Enter Subject"
        onChange={(e) => setSubject(e.target.value)}
      />

      <br/><br/>

      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <br/><br/>

      <button onClick={handleUpload}>
        Upload File
      </button>

    </div>

  );

}