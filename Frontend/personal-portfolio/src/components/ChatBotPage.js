import React, { useState, useEffect, useRef } from "react";
import { NavBar } from "./NavBar";
import { Chatbot } from "./Chatbot";
import { SimpleLineChart } from "./SimpleLineChart";
import { BarChartFinal } from "./BarChart";
import { PieChartFinal } from "./PieChartFinal";
import { Container, Row, Col } from "react-bootstrap";
import { motion } from "framer-motion";
import loadingGif from '../assets/img/ezgif-5b9077b0393745.gif';
import { LineChart2 } from "./LineChart2";

export const ChatBotPage = () => {
  useEffect(() => {
    window.scrollTo(0, 0); // Scroll to top when the page loads
  }, []);
    const [pdfId,setpdfId] = useState(null);
    const [messages, setMessages] = useState([{sender: "bot"}]);    
    const [result, setResult] = useState(null);
    const [loadingText, setText] = useState("See your insights here!");
    const[showLoading,setShowLoading] = useState(true);

    const handleInsights = async () => {
      const userMessage = { sender: "user" };

      setMessages((prev) => [...prev, userMessage]);
        try {
          // API call to /api/insights
          console.log("i have reached here");
          console.log("parent:",pdfId);
          let response = await fetch("http://127.0.0.1:8080/api/insights", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
           
            body: JSON.stringify({
              pdf_id: pdfId // Send the pdfId along with the question
            }),
          });
     
          let result = await response.json();
          console.log(result);
          console.log(pdfId);
          if (response.ok) {
            displayMessage(result.answer, "bot-message");
            setShowLoading(false);
            setResult(result);
          } else {
            displayMessage("Error: " + result.error, "bot-message");
          }
        } catch (error) {
          displayMessage("Error connecting to chat API.", "bot-message");
        } 
        // finally {
        //   sendBtn.disabled = false;
        // }
      };

      const displayMessage = (text, className) => {
        setMessages((prev) => [
          ...prev,
          { sender: className === "bot-message" ? "bot" : "user" },
        ]);
      };


    useEffect(() => {
      if (pdfId !== null) {
        console.log("📢 pdfId has changed, calling handleInsights...");
        setText("Gathering your insights...");
        handleInsights();
      }
    }, [pdfId]); // ✅ Runs whenever pdfId changes

    useEffect(() => {
      if (result !== null && result!==undefined) {
        console.log("📢 Charts will be rendered now, result is populated:", result);
      }
    }, [result]); // ✅ This triggers a re-render when `result` updates
    
    return (
   
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          
          style={{ overflow: 'hidden', height: '100vh', display: 'flex', flexDirection: 'column' }} // Ensure full viewport height and no scrolling
        >
          <NavBar />
          <section className="banner2" id="home" style={{ flex: 1 }}>
          <Container fluid style={{ height: '100%' }}>

              <Row className="align-items-start" style={{ height: '100%' }}>
              {showLoading && <div style={{ position: 'absolute', top: '200px', left: '90px', display: 'flex', alignItems: 'center', zIndex: 999 ,gap: '-5px', justifyContent : 'right'}}>
  <p style={{ 
    fontSize: '28px', 
    fontWeight: 'bold', 
    margin:0,
    marginLeft: '100px', // Space between text and GIF
    marginRight: '0', // Space between text and GIF
    color:'white'
  }}>
    {loadingText}
  </p>
  <img src={loadingGif} alt="Loading..." style={{ width: '300px', height: '300px' , marginRight: '800px' // Space between text and GIF
    }} />
</div>}


                {/* Left Section - Charts */}
                <Col md={9} style={{ marginTop: "-120px", height: '100%' }}>
                  <Row style={{ height: '100%' }}>
                    <Col md={6} className="charts-container-up" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
                      <div className="main-charts" style={{ height: '100%' }}>
                        {result && Object.keys(result).length > 0 && <SimpleLineChart barData={result} />}
                        {result && Object.keys(result).length > 0 && <LineChart2 barData={result} />}
                       
                      </div>
                    </Col>
                    {/* First Row: Two charts side by side */}
                    <Col md={6} className="charts-container-up" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
                      <div className="pie-chart" style={{ height: '100%', marginTop:'-120px', marginLeft:'-0px' }}>
                      {result && Object.keys(result).length > 0 && <PieChartFinal barData={result} />}
          
                        {result && Object.keys(result).length > 0 && <BarChartFinal barData={result} />}
                        </div>
                       
                     
                    </Col>
                  </Row>
                </Col>
      
                {/* Right Section - Chatbot */}
                <Col md={3} className="chatbot-wrapper" style={{ height: '100%', marginTop: "-120px", marginLeft : "-90px" }}>
                  <div className="chatbot-full-container" style={{ height: '100%', maxWidth: '150%' }}>
                    <Chatbot pdfId={pdfId} setPdfId={setpdfId} />
                  </div>
                </Col>
              </Row>
            </Container>
          </section>
        </motion.div>
      );
      
   
};
