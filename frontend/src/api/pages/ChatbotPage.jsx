import { useState } from "react";
import axios from "axios";
import { useLocation } from "react-router-dom";

export default function ChatbotPage(){

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const location = useLocation();
  const { class_standard, subject } = location.state || {};

  // ✅ TYPING EFFECT FUNCTION
  const typeText = (text) => {
    let index = 0;
    let currentText = "";

    const interval = setInterval(() => {
      currentText += text[index];
      index++;

      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { type: "bot", text: currentText };
        return updated;
      });

      if(index === text.length){
        clearInterval(interval);
        setLoading(false);
      }
    }, 20); // speed (lower = faster)
  };

  const askAI = async () => {

    if(!question.trim()) return;

    const token = localStorage.getItem("token");

    // USER MESSAGE
    setMessages(prev => [...prev, { type: "user", text: question }]);

    // EMPTY BOT MESSAGE (for typing)
    setMessages(prev => [...prev, { type: "bot", text: "" }]);

    setLoading(true);

    const formData = new FormData();
    formData.append("question", question);
    formData.append("class_standard", class_standard);
    formData.append("subject", subject);

    try {
      const res = await axios.post(
        "http://localhost:8000/student/chatbot_ask_questions",
        formData,
        {
          headers:{ Authorization:`Bearer ${token}` }
        }
      );

      const botReply = res.data.message.answer || res.data.message;

      // START TYPING EFFECT
      typeText(botReply);

      setQuestion("");

    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  return (
    <div style={{
      height: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      background: darkMode ? "#121212" : "linear-gradient(120deg, #fff3e0, #ffe0b2)"
    }}>

      <div style={{
        width: "520px",
        height: "650px",
        background: darkMode ? "#1e1e1e" : "#fff",
        borderRadius: "20px",
        boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        color: darkMode ? "#fff" : "#000"
      }}>

        {/* HEADER */}
        <div style={{
          background: "#ff7a18",
          color: "#fff",
          padding: "15px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontWeight: "bold"
        }}>
          <div>
            🤖 AI Study Buddy <br/>
            <small>{class_standard} → {subject}</small>
          </div>

          {/* 🌙 DARK MODE TOGGLE */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            style={{
              background: "#fff",
              color: "#ff7a18",
              border: "none",
              padding: "6px 10px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "12px"
            }}
          >
            {darkMode ? "☀️ Light" : "🌙 Dark"}
          </button>
        </div>

        {/* CHAT AREA */}
        <div style={{
          flex: 1,
          padding: "15px",
          overflowY: "auto"
        }}>
          {messages.map((msg, i) => (
            <div key={i} style={{
              textAlign: msg.type === "user" ? "right" : "left",
              marginBottom: "10px"
            }}>
              <span style={{
                display:"inline-block",
                padding:"10px 15px",
                borderRadius:"15px",
                maxWidth:"70%",
                background: msg.type === "user"
                  ? "#ff7a18"
                  : (darkMode ? "#333" : "#eee"),
                color: msg.type === "user" ? "#fff" : (darkMode ? "#fff" : "#000")
              }}>
                {msg.text}
              </span>
            </div>
          ))}

          {/* 🔥 BOUNCING DOT LOADER */}
          {loading && (
            <div style={{ marginTop: "5px" }}>
              <div className="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        {/* INPUT AREA */}
        <div style={{
          display: "flex",
          alignItems:"center",
          borderTop: darkMode ? "1px solid #333" : "1px solid #ddd",
          padding:"10px"
        }}>
          <span style={{ fontSize:"20px", marginRight:"8px" }}>🤖</span>

          <input
            value={question}
            onChange={(e)=>setQuestion(e.target.value)}
            placeholder="Ask your question..."
            style={{
              flex: 1,
              padding: "10px",
              border: "none",
              outline: "none",
              background: "transparent",
              color: darkMode ? "#fff" : "#000"
            }}
          />

          <button
            onClick={askAI}
            style={{
              padding: "10px 18px",
              background: "#ff7a18",
              color: "#fff",
              border: "none",
              borderRadius:"8px",
              cursor: "pointer"
            }}
          >
            Send
          </button>
        </div>

      </div>

      {/* 🔥 PERFECT VISIBLE DOT ANIMATION */}
      <style>{`
        .typing-dots {
          display: flex;
          gap: 6px;
          margin-left: 5px;
        }

        .typing-dots span {
          width: 10px;
          height: 10px;
          background: #ff7a18;
          border-radius: 50%;
          display: inline-block;
          animation: bounce 1.4s infinite ease-in-out;
        }

        .typing-dots span:nth-child(1) {
          animation-delay: 0s;
        }
        .typing-dots span:nth-child(2) {
          animation-delay: 0.2s;
        }
        .typing-dots span:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes bounce {
          0%, 80%, 100% {
            transform: translateY(0);
            opacity: 0.5;
          }
          40% {
            transform: translateY(-12px);
            opacity: 1;
          }
        }
      `}</style>

    </div>
  );
}