import { useState, useEffect } from "react";
import { Container, Row, Col } from "react-bootstrap";
import headerImg from "../assets/img/header-img.svg";
import Finance from "../assets/img/DDS2.gif"
import { ArrowRightCircle } from 'react-bootstrap-icons';
import 'animate.css';
import TrackVisibility from 'react-on-screen';
import { Chatbot } from "./Chatbot";
import {SimpleLineChart} from "./SimpleLineChart";
import {BarChartFinal} from "./BarChart";
import {PieChartFinal} from "./PieChartFinal";

export const BannerPart3 = () => {
  const [loopNum, setLoopNum] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [text, setText] = useState('');
  const [delta, setDelta] = useState(300 - Math.random() * 100);
  const [index, setIndex] = useState(1);
  const toRotate = [ "AI Agent", "Banking Buddy", "Wealth Wizard" ];
  const period = 2000;

  useEffect(() => {
    let ticker = setInterval(() => {
      tick();
    }, delta);

    return () => { clearInterval(ticker) };
  }, [text])

  const tick = () => {
    let i = loopNum % toRotate.length;
    let fullText = toRotate[i];
    let updatedText = isDeleting ? fullText.substring(0, text.length - 1) : fullText.substring(0, text.length + 1);

    setText(updatedText);

    if (isDeleting) {
      setDelta(prevDelta => prevDelta / 2);
    }

    if (!isDeleting && updatedText === fullText) {
      setIsDeleting(true);
      setIndex(prevIndex => prevIndex - 1);
      setDelta(period);
    } else if (isDeleting && updatedText === '') {
      setIsDeleting(false);
      setLoopNum(loopNum + 1);
      setIndex(1);
      setDelta(500);
    } else {
      setIndex(prevIndex => prevIndex + 1);
    }
  }

  return (
    <section className="banner2" id="home">
  <Container>
    <div className="home-section">
      {/* Left Content - Text Animation */}
      <div className="home-content">
        <TrackVisibility>
          {({ isVisible }) => (
            <div
              className={isVisible ? "animate__animated animate__fadeIn" : ""}
              style={{ animationDuration: "0.5s" }}
            >
              <h1>{`Hi! I'm FinBuzz,          your          `} <span className="txt-rotate" dataPeriod="1000" data-rotate='[ "AI Agent", "Banking Buddy", "Wealth Wizard" ]'><span className="wrap">{text}</span></span></h1>
            </div>
          )}
        </TrackVisibility>
      </div>

      {/* Right Content - Image */}
      <div className="home-image">
        <TrackVisibility>
          {({ isVisible }) => (
            <div className={isVisible ? "animate__animated animate__zoomIn" : ""}>
              <img src={Finance} alt="Finance Header Img" />
            </div>
          )}
        </TrackVisibility>
      </div>
    </div>

    {/* Charts Section */}
    {/* <div className="charts-container">
      <SimpleLineChart />
      <BarChartFinal />
      <PieChartFinal />
    </div> */}
    {/* <div>
    <Chatbot />
    </div> */}
  </Container>
</section>

  )
}
