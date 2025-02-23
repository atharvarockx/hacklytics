import logo from './logo.svg';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";  

import 'bootstrap/dist/css/bootstrap.min.css';
import { NavBar } from "./components/NavBar";
import { Banner } from "./components/Banner";
import {BannerPart2, BannerPart3} from "./components/BannerPart3";
import { Chatbot, Skills } from "./components/Chatbot";
import { Projects } from "./components/Projects";
import { Contact } from "./components/Contact";
import { Footer } from "./components/Footer";
import { ChatBotPage } from "./components/ChatBotPage"
import ScrollText from './components/ScrollText';

function App() {
  return (
    <Router>
      <Routes>
        {/* Routes with Navbar & Footer */}
        <Route
          path="/"
          element={
            <>
              <NavBar />
              <BannerPart3 />
              <Projects />
              <Footer />
            </>
          }
        />
        <Route
          path="/projects"
          element={
            <>
              <NavBar />
              <BannerPart3 />
              <Projects />
              <Footer />
            </>
          }
        />
        <Route
          path="/contact"
          element={
            <>
              <NavBar />
              <Contact />
              <Footer />
            </>
          }
        />
        <Route path="/chatbot" element={
          <>
          <NavBar />
       <ChatBotPage/>
          </>
          } />
      </Routes>
    </Router>
  );
}

export default App;
