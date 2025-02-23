import React, { useState, useEffect, useRef } from "react";
import { Box, TextField, Button, Typography, IconButton, Paper, Container } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AttachFileIcon from "@mui/icons-material/AttachFile";
 
export const Chatbot = ({pdfId, setPdfId}) => {
  const [messages, setMessages] = useState([{ text: "Hello! Welcome to FinBuzz!\n Upload your statement and ask me anything!", sender: "bot" }]);
  const [input, setInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const chatEndRef = useRef(null);
  const [file, setFile] = useState(null);
  const [statusText, setStatusText] = useState("");
  // const [pdfId, setPdfId] = useState(null); // Store the PDF ID
 
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);
 
  const handleSend = async () => {
    if (input.trim() === "") return;
    setShowSuggestions(false);
 
    const userMessage = { text: input, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
 
    // Disable Send button while making the API call
    const sendBtn = document.getElementById("sendBtn");
    sendBtn.disabled = true;
 
    try {
      // API call to /api/chat
      console.log("i have reached here");
      console.log(pdfId);
      let response = await fetch("http://127.0.0.1:8080/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
       
        body: JSON.stringify({
          pdf_id: pdfId, // Send the pdfId along with the question
          question: input,
        }),
      });
 
      let result = await response.json();
      console.log(result);
      if (response.ok) {
        displayMessage(result.answer, "bot-message");
       
      } else {
        displayMessage("Error: " + result.error, "bot-message");
      }
    } catch (error) {
      displayMessage("Error connecting to chat API.", "bot-message");
    } finally {
      sendBtn.disabled = false;
    }
  };
 
  const displayMessage = (text, className) => {
    setMessages((prev) => [
      ...prev,
      { text: text, sender: className === "bot-message" ? "bot" : "user" },
    ]);
  };
 
 
  const handleSuggestionClick = (question) => {
    setInput(question);
    setShowSuggestions(false);
  };
 
  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      setStatusText("Uploading file...");
 
      // Create FormData to send the file
      const formData = new FormData();
      formData.append("file", uploadedFile);
 
      // Disable input and send button during upload
      setInput("");
      document.getElementById("sendBtn").disabled = true;
 
      try {
        const response = await fetch("http://127.0.0.1:8080/api/upload", {
          method: "POST",
          body: formData,
        });
 
        const result = await response.json();
        console.log(result);
        if (response.ok) {
          setStatusText("File uploaded! You can now chat.");
          setPdfId(result.pdf_id); // Store the PDF ID from the response
          setStatusText("File uploaded! You can now chat.");
          setMessages((prev) => [
            ...prev,
            { text: `You uploaded a file: ${uploadedFile.name}`, sender: "user" },
          ]);
        } else {
          setStatusText("Upload failed: " + result.error);
        }
      } catch (error) {
        setStatusText("Error uploading file.");
      }
 
      // Re-enable the input field and send button
      document.getElementById("sendBtn").disabled = false;
    }
  };
 
  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "1rem 0" }}>
      <Paper
        elevation={4}
        sx={{
          width: "100%",
          maxWidth: "400px",
          height: "550px",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#121212",
          borderRadius: "16px",
          overflow: "hidden",
          color: "white",
          border: "2px solid rgb(136, 132, 216)",
        }}
      >
        {/* Header */}
        <Box
          sx={{
            backgroundColor: "#1E1E1E",
            padding: "12px",
            textAlign: "center",
            fontSize: "1.2rem",
            fontWeight: "bold",
            borderBottom: "2px solid rgb(136, 132, 216)",
          }}
        >
          FinBuzz - AI Agent
        </Box>
 
        {/* Chat Messages */}
        <Box
          sx={{
            flex: 1,
            overflowY: "auto",
            padding: "12px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          {messages.map((msg, index) => (
            <Box
              key={index}
              sx={{
                padding: "10px",
                borderRadius: "12px",
                maxWidth: "75%",
                alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
                backgroundColor: msg.sender === "user" ? "rgb(136, 132, 216)" : "#333",
                color: "white",
                fontSize: "0.9rem",
              }}
            >
              {/* {msg.text} */}
              {msg.text.startsWith("<div>") ? (
                <div dangerouslySetInnerHTML={{ __html: msg.text }} />
              ) : (
                <Typography variant="body1">{msg.text}</Typography>
              )}
            </Box>
          ))}
          <div ref={chatEndRef}></div>
        </Box>
 
        {/* Suggested Questions (Above Input Box) */}
        {showSuggestions && (
          <Box
            sx={{
              textAlign: "center",
              color: "white",
              paddingBottom: "8px",
              fontSize: "0.9rem",
            }}
          >
            <Typography variant="body1" sx={{ fontSize: "0.9rem", color: "#999" }}>
              Try Clicking:
            </Typography>
            {["What was my biggest expenditure?", "Can you summarize my income?", "List all my grocery and shopping expenses."].map(
              (question, index) => (
                <Typography
                  key={index}
                  variant="body2"
                  sx={{
                    fontStyle: "italic",
                    color: "rgb(136, 132, 216)",
                    cursor: "pointer",
                    "&:hover": { textDecoration: "underline" },
                  }}
                  onClick={() => handleSuggestionClick(question)}
                >
                  {question}
                </Typography>
              )
            )}
          </Box>
        )}
 
        {/* Input Box & Send Button */}
        <Box
  sx={{
    display: "flex",
    alignItems: "center", // Align items vertically in the center
            justifyContent: "space-between",
    width: "100%",
    gap: "10px", // Increased the gap slightly for spacing between elements
    padding: "12px",
    backgroundColor: "#222",
    borderTop: "2px solid rgb(136, 132, 216)",
  }}
>
  <TextField
    variant="outlined"
    fullWidth
    placeholder="Type a message..."
    value={input}
    onChange={(e) => setInput(e.target.value)}
    onKeyDown={(e) => e.key === "Enter" && handleSend()}
    disabled={!pdfId} // Disable if pdfId is not set
    sx={{
      backgroundColor: pdfId ? "white" : "#d3d3d3", // Grey when disabled, white when enabled
      color: "black",
      borderRadius: "8px",
      flex: 1, // Make the text field take up remaining space
      "& .MuiOutlinedInput-root": {
        borderRadius: "8px",
      },
      "& .MuiInputBase-input.Mui-disabled": {
        color: "#a9a9a9", // Light grey text when disabled
      },
    }}
  />
 
  {/* Attach File Button */}
  <IconButton
    component="label"
    sx={{
      backgroundColor: "rgb(136, 132, 216)",
      height: "45px",
      width: "45px",
      minWidth: "unset",
      borderRadius: "8px",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      marginTop: "0px !important ",
      color: "white",
      "&:hover": { backgroundColor: "rgb(120, 125, 210)" },
    }}
  >
    <AttachFileIcon />
    <input
      type="file"
      hidden
      onChange={handleFileUpload}
      accept=".pdf"
    />
  </IconButton>
 
          <Button
          id="sendBtn"
            variant="contained"
            sx={{
              backgroundColor: "rgb(136, 132, 216)",
              height: "45px",
              width: "45px",
              minWidth: "unset",
              borderRadius: "8px",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              marginTop: "0px !important ",
              "&:hover": { backgroundColor: "rgb(120, 125, 210)" },
            }}
            onClick={handleSend}
          >
            <SendIcon sx={{ fontSize: "20px" }} />
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};