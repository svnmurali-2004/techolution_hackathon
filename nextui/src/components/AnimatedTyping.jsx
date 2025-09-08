"use client";
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const AnimatedTyping = ({
  text,
  speed = 100, // Faster default speed (was 30)
  delay = 0,
  onComplete = () => {},
  className = "",
  showCursor = true,
  cursorBlink = true,
  typeByWords = true, // New option to type by words
}) => {
  const [displayedText, setDisplayedText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (typeByWords) {
      // Type by words for faster, more natural feel
      const words = text.split(" ");
      if (currentIndex < words.length) {
        // Add some randomness to make typing feel more natural
        const randomDelay = speed + Math.random() * 20 - 10;
        const timeout = setTimeout(() => {
          setDisplayedText(
            (prev) => prev + (currentIndex > 0 ? " " : "") + words[currentIndex]
          );
          setCurrentIndex((prev) => prev + 1);
        }, Math.max(randomDelay, 20)); // Ensure minimum delay

        return () => clearTimeout(timeout);
      } else if (!isComplete) {
        setIsComplete(true);
        onComplete();
      }
    } else {
      // Original character-by-character typing
      if (currentIndex < text.length) {
        const timeout = setTimeout(() => {
          setDisplayedText((prev) => prev + text[currentIndex]);
          setCurrentIndex((prev) => prev + 1);
        }, speed);

        return () => clearTimeout(timeout);
      } else if (!isComplete) {
        setIsComplete(true);
        onComplete();
      }
    }
  }, [currentIndex, text, speed, isComplete, onComplete, typeByWords]);

  useEffect(() => {
    if (delay > 0) {
      const timeout = setTimeout(() => {
        setCurrentIndex(0);
      }, delay);
      return () => clearTimeout(timeout);
    }
  }, [delay]);

  return (
    <motion.span
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <motion.span
        animate={{
          textShadow: [
            "0 0 0px rgba(59, 130, 246, 0)",
            "0 0 2px rgba(59, 130, 246, 0.3)",
            "0 0 0px rgba(59, 130, 246, 0)",
          ],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        {displayedText}
      </motion.span>
      <AnimatePresence>
        {showCursor && (
          <motion.span
            className="inline-block relative ml-1"
            animate={{
              opacity: cursorBlink ? [1, 0, 1] : 1,
            }}
            transition={{
              duration: 0.8,
              repeat: cursorBlink ? Infinity : 0,
              ease: "easeInOut",
            }}
            exit={{ opacity: 0 }}
          >
            {/* Main cursor */}
            <span className="inline-block w-0.5 h-5 bg-blue-500"></span>
            {/* Glow effect */}
            <motion.span
              className="absolute inset-0 w-0.5 h-5 bg-blue-400 blur-sm"
              animate={{
                opacity: [0, 0.5, 0],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
            {/* Pulse effect */}
            <motion.span
              className="absolute inset-0 w-1 h-5 bg-blue-300 rounded-full opacity-30"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.1, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          </motion.span>
        )}
      </AnimatePresence>
    </motion.span>
  );
};

export default AnimatedTyping;
