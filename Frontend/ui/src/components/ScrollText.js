import React, { useEffect } from 'react';

const ScrollText = () => {
  useEffect(() => {
    const pos = document.documentElement;

    // Event listener to update CSS custom properties on mouse move
    const handleMouseMove = (e) => {
      pos.style.setProperty('--x', `${e.clientX}px`);
      pos.style.setProperty('--y', `${e.clientY}px`);
    };

    pos.addEventListener('mousemove', handleMouseMove);

    // Cleanup the event listener when the component unmounts
    return () => {
      pos.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <section>
      <h2>Now Coding</h2>
      <div className="light"></div>
    </section>
  );
};

export default ScrollText;
