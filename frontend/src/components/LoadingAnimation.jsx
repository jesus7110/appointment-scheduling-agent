import React from 'react';
import './LoadingAnimation.css';

const LoadingAnimation = () => {
  return (
    <div className="loader-container">
      <svg className="loader-icon" fill="#ef6a36" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
        <g id="SVGRepo_bgCarrier" strokeWidth="0"></g>
        <g id="SVGRepo_tracerCarrier" strokeLinecap="round" strokeLinejoin="round"></g>
        <g id="SVGRepo_iconCarrier">
          <title>ionicons-v5-n</title>
          <polygon points="351.9 256 460 193.6 412 110.4 304 172.8 304 48 208 48 208 172.8 100 110.4 52 193.6 160.1 256 52 318.4 100 401.6 208 339.2 208 464 304 464 304 339.2 412 401.6 460 318.4 351.9 256"></polygon>
        </g>
      </svg>
      <span className="thinking-text">thinking<span className="dots"><span>.</span><span>.</span><span>.</span></span></span>
    </div>
  );
};

export default LoadingAnimation;

