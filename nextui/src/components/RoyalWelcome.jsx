"use client";
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Crown, Star, Zap, Trophy, Gem } from "lucide-react";

const RoyalWelcome = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [showContent, setShowContent] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const timer = setTimeout(() => {
      setShowContent(true);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (showContent) {
      const stepTimer = setTimeout(() => {
        if (currentStep < 3) {
          setCurrentStep(currentStep + 1);
        } else {
          setTimeout(() => {
            onComplete();
          }, 2000); // Keep it at 2000ms for good balance
        }
      }, 2500); // Increased from 1500 to 2500ms for slower transitions

      return () => clearTimeout(stepTimer);
    }
  }, [currentStep, showContent, onComplete]);

  const steps = [
    {
      icon: Crown,
      title: "Welcome to the Future",
      subtitle: "AI-Powered Report Generation",
      color: "from-yellow-400 to-orange-500",
    },
    {
      icon: Zap,
      title: "Lightning Fast",
      subtitle: "Generate Professional Reports in Seconds",
      color: "from-blue-400 to-purple-500",
    },
    {
      icon: Gem,
      title: "Enterprise Grade",
      subtitle: "Built for Professional Excellence",
      color: "from-pink-400 to-red-500",
    },
    {
      icon: Trophy,
      title: "Ready to Impress",
      subtitle: "Your Reports Will Stand Out",
      color: "from-green-400 to-teal-500",
    },
  ];

  if (!mounted) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center overflow-hidden"
    >
      {/* Animated Background */}
      <div className="absolute inset-0">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            initial={{
              x:
                typeof window !== "undefined"
                  ? Math.random() * window.innerWidth
                  : Math.random() * 1000,
              y:
                typeof window !== "undefined"
                  ? Math.random() * window.innerHeight
                  : Math.random() * 1000,
              scale: 0,
            }}
            animate={{
              y: [null, -200],
              scale: [0, 1, 0],
              rotate: 360,
            }}
            transition={{
              duration: 4 + Math.random() * 2,
              delay: Math.random() * 2,
              repeat: Infinity,
              repeatDelay: Math.random() * 3,
            }}
            className="absolute w-1 h-1 bg-white rounded-full opacity-60"
          />
        ))}
      </div>

      {/* Main Content */}
      <div className="text-center relative z-10">
        <AnimatePresence mode="wait">
          {showContent && (
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, y: 50, scale: 0.8 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -50, scale: 0.8 }}
              transition={{ duration: 0.8, type: "spring", stiffness: 100 }}
              className="space-y-8"
            >
              {/* Icon */}
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ duration: 1, type: "spring", stiffness: 100 }}
                className="mx-auto"
              >
                <div
                  className={`w-32 h-32 mx-auto bg-gradient-to-r ${steps[currentStep].color} rounded-full flex items-center justify-center shadow-2xl`}
                >
                  {React.createElement(steps[currentStep].icon, {
                    className: "h-16 w-16 text-white",
                  })}
                </div>
              </motion.div>

              {/* Text Content */}
              <div className="space-y-4">
                <motion.h1
                  initial={{ y: 30, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  className="text-5xl font-bold bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 bg-clip-text text-transparent"
                >
                  {steps[currentStep].title}
                </motion.h1>

                <motion.p
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.5 }}
                  className="text-2xl text-white/80 max-w-2xl mx-auto"
                >
                  {steps[currentStep].subtitle}
                </motion.p>
              </div>

              {/* Progress Dots */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="flex justify-center space-x-3"
              >
                {steps.map((_, index) => (
                  <motion.div
                    key={index}
                    className={`w-3 h-3 rounded-full ${
                      index <= currentStep
                        ? "bg-gradient-to-r from-yellow-400 to-purple-600"
                        : "bg-white/30"
                    }`}
                    animate={{
                      scale: index === currentStep ? 1.5 : 1,
                    }}
                    transition={{ duration: 0.3 }}
                  />
                ))}
              </motion.div>

              {/* Sparkle Effects */}
              <div className="absolute inset-0 pointer-events-none">
                {[...Array(10)].map((_, i) => (
                  <motion.div
                    key={i}
                    initial={{
                      x: Math.random() * 400 - 200,
                      y: Math.random() * 400 - 200,
                      scale: 0,
                    }}
                    animate={{
                      scale: [0, 1, 0],
                      rotate: 360,
                    }}
                    transition={{
                      duration: 2,
                      delay: i * 0.2,
                      repeat: Infinity,
                      repeatDelay: 1,
                    }}
                    className="absolute"
                  >
                    <Star className="h-6 w-6 text-yellow-400" />
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Progress Bar */}
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: "100%" }}
        transition={{ duration: 6, ease: "linear" }}
        className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600"
      />
    </motion.div>
  );
};

export default RoyalWelcome;
