import { Container, Row, Col, Nav } from "react-bootstrap";
import { ProjectCard } from "./ProjectCard";

export const Projects = () => {

  const projects = [
    {
      title: "Expense Breakdown",
      description: "Track spending by category, identify trends, and see where your money goes.",
    },
    {
      title: "Smart Budgeting",
      description: "Compare income vs. expenses, find savings opportunities, and get insights.",
    },
    {
      title: "Detect Unusual Transactions",
      description: "Spot high-value or suspicious transactions instantly.",
    },
    {
      title: "Monthly Trends",
      description: "Compare spending patterns across months to adjust your budget.",
    },
    {
      title: "Visual Insights",
      description: "Interactive charts (line, pie, bar) make financial data easy to understand.",
    },
    {
      title: "Quick Answers",
      description: "Ask about your expenses and get instant, data-driven responses.",
    },
  ];

  return (
    <section className="project" id="projects">
      <Container>
        <Row>
          <Col size={12}>
            <div>
              <h2>What I can help with</h2>
              <p></p>
              <p></p>
              <Nav variant="pills" className="modern-nav" id="pills-tab">
                Ask away the following to gain insights into your financial statements
              </Nav>
              <p></p>
              <p></p>
              <Row>
                {projects.map((project, index) => (
                  <ProjectCard key={index} {...project} />
                ))}
              </Row>  
            </div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};
