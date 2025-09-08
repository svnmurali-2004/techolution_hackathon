"use client";
import React, { useRef, useEffect, useState } from "react";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";

const ParallaxSection = ({
  children,
  speed = 0.5,
  direction = "up",
  className = "",
  offset = ["start end", "end start"],
}) => {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: offset,
  });

  const springConfig = { stiffness: 100, damping: 30, restDelta: 0.001 };

  const y = useSpring(
    useTransform(
      scrollYProgress,
      [0, 1],
      direction === "up" ? [100, -100] : [-100, 100]
    ),
    springConfig
  );

  const opacity = useSpring(
    useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]),
    springConfig
  );

  const scale = useSpring(
    useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0.8, 1, 1, 0.8]),
    springConfig
  );

  return (
    <motion.div
      ref={ref}
      className={className}
      style={{
        y: y,
        opacity: opacity,
        scale: scale,
      }}
    >
      {children}
    </motion.div>
  );
};

export default ParallaxSection;
