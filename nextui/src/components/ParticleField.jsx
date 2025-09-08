"use client";
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

const ParticleField = ({ isVisible = true }) => {
  const [particles, setParticles] = useState([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (isVisible) {
      const newParticles = Array.from({ length: 100 }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 4 + 1,
        delay: Math.random() * 5,
        duration: 3 + Math.random() * 4,
      }));
      setParticles(newParticles);
    }
  }, [isVisible]);

  if (!mounted || !isVisible) {
    return null;
  }

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          initial={{
            x: `${particle.x}vw`,
            y: `${particle.y}vh`,
            scale: 0,
            opacity: 0,
          }}
          animate={
            isVisible
              ? {
                  x: [
                    `${particle.x}vw`,
                    `${particle.x + (Math.random() - 0.5) * 20}vw`,
                    `${particle.x}vw`,
                  ],
                  y: [
                    `${particle.y}vh`,
                    `${particle.y + (Math.random() - 0.5) * 20}vh`,
                    `${particle.y}vh`,
                  ],
                  scale: [0, 1, 0],
                  opacity: [0, 0.6, 0],
                  rotate: 360,
                }
              : {
                  scale: 0,
                  opacity: 0,
                }
          }
          transition={{
            duration: particle.duration,
            delay: particle.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="absolute rounded-full bg-gradient-to-r from-blue-400 to-purple-500"
          style={{
            width: `${particle.size}px`,
            height: `${particle.size}px`,
          }}
        />
      ))}
    </div>
  );
};

export default ParticleField;
