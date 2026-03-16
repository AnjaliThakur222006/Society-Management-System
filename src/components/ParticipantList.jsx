import React, { useState, useEffect, useRef } from 'react';
import './ParticipantList.css';

const ParticipantList = ({ participants }) => {
  const [loadedImages, setLoadedImages] = useState(new Set());
  const imgRefs = useRef([]);

  useEffect(() => {
    // Reset loaded images when participants change
    setLoadedImages(new Set());
    imgRefs.current = imgRefs.current.slice(0, participants.length);
  }, [participants]);

  useEffect(() => {
    // Check for already loaded images after refs are set
    const checkLoadedImages = () => {
      imgRefs.current.forEach((img, index) => {
        if (img && img.complete && img.naturalHeight !== 0 && !loadedImages.has(index)) {
          setLoadedImages(prev => new Set([...prev, index]));
        }
      });
    };

    // Check after a short delay to ensure refs are set
    const timer = setTimeout(checkLoadedImages, 50);

    return () => clearTimeout(timer);
  }, [participants, loadedImages]);

  const handleImageLoad = (index) => {
    setLoadedImages(prev => new Set([...prev, index]));
  };

  const handleImageError = (index) => {
    setLoadedImages(prev => new Set([...prev, index]));
  };

  const allImagesLoaded = loadedImages.size === participants.length;

  return (
    <div className="participant-list">
      {!allImagesLoaded && (
        <div className="shimmer-container">
          {participants.map((participant, index) => (
            !loadedImages.has(index) && (
              <div key={index} className="shimmer-item">
                <div className="shimmer-avatar"></div>
                <div className="shimmer-text"></div>
              </div>
            )
          ))}
        </div>
      )}
      <div className="participant-grid">
        {participants.map((participant, index) => (
          <div key={index} className="participant-item">
            <img
              ref={el => imgRefs.current[index] = el}
              src={participant.image}
              alt={participant.name}
              className="participant-avatar"
              onLoad={() => handleImageLoad(index)}
              onError={() => handleImageError(index)}
            />
            <div className="participant-info">
              <h3>{participant.name}</h3>
              <p>{participant.role}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ParticipantList;
