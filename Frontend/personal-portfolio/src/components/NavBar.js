import { useState, useEffect } from "react";
import { Navbar, Nav, Container } from "react-bootstrap";
import logo from "../assets/img/FinBuzz.png";
import navIcon1 from "../assets/img/nav-icon1.svg";
import navIcon2 from "../assets/img/nav-icon2.svg";
import navIcon3 from "../assets/img/nav-icon3.svg";
import { Link } from "react-router-dom";

export const NavBar = () => {
  const [activeLink, setActiveLink] = useState("home");
  const [scrolled, setScrolled] = useState(false);
  
  const [name, setName] = useState(false); // State to store the fetched name
  useEffect(() => {
    const onScroll = () => {
      if (window.scrollY > 50) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    const searchParams = new URLSearchParams(window.location.search);
    const nameParam = searchParams.get("name");
    if (nameParam) {
      setName(nameParam);
    }

    window.addEventListener("scroll", onScroll);

    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const onUpdateActiveLink = (value) => {
    setActiveLink(value);
  };

  const handleLoginClick = async () => {
    try {
      // Send the GET request to the login URL
      const response = await fetch("http://127.0.0.1:8080/login");
      console.log(response)
      // Check if the response is ok
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      // Parse the JSON response
      const data = await response.json();
      // Assuming 'name' is the field in the response you want to extract
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };
  return (
    <Navbar expand="md" className={scrolled ? "scrolled" : ""}>
      <Container>
        <Navbar.Brand as={Link} to="/">
        <img src={logo} alt="Logo" style={{ width: '150px', height: 'auto' }} />
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav">
          <span className="navbar-toggler-icon"></span>
        </Navbar.Toggle>
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link
              as={Link}
              to="/"
              className={activeLink === "home" ? "active navbar-link" : "navbar-link"}
              onClick={() => onUpdateActiveLink("home")}
            >
              Home
            </Nav.Link>
            <Nav.Link href="#projects" className={activeLink === 'projects' ? 'active navbar-link' : 'navbar-link'} onClick={() => onUpdateActiveLink('projects')}>About</Nav.Link>

            <Nav.Link
              as={Link}
              to="/chatbot"
              className={activeLink === "skills" ? "active navbar-link" : "navbar-link"}
              onClick={() => {
                onUpdateActiveLink("Product");
                window.scrollTo(0, 0); // Scroll to top when clicking the link
              }}
            >
              AI Agent
            </Nav.Link>
          </Nav>
          <span className="navbar-text">
            <a href="http://127.0.0.1:8080/login">
              <button className="vvd" onClick={handleLoginClick}>
                <span>{name? name : 'Login'}</span>
              </button>
            </a>
          </span>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};
