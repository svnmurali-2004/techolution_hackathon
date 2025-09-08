"use client";
import React from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";

const HoverCard = ({
  children,
  hoverContent,
  className = "",
  delay = 0.2,
  side = "top",
}) => {
  const [isHovered, setIsHovered] = React.useState(false);

  const getSideClasses = () => {
    switch (side) {
      case "top":
        return "bottom-full left-1/2 transform -translate-x-1/2 mb-2";
      case "bottom":
        return "top-full left-1/2 transform -translate-x-1/2 mt-2";
      case "left":
        return "right-full top-1/2 transform -translate-y-1/2 mr-2";
      case "right":
        return "left-full top-1/2 transform -translate-y-1/2 ml-2";
      default:
        return "bottom-full left-1/2 transform -translate-x-1/2 mb-2";
    }
  };

  return (
    <div
      className={`relative ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children}

      <motion.div
        initial={{ opacity: 0, scale: 0.8, y: 10 }}
        animate={{
          opacity: isHovered ? 1 : 0,
          scale: isHovered ? 1 : 0.8,
          y: isHovered ? 0 : 10,
        }}
        transition={{
          duration: 0.2,
          delay: isHovered ? delay : 0,
        }}
        className={`absolute z-50 ${getSideClasses()}`}
        style={{ pointerEvents: isHovered ? "auto" : "none" }}
      >
        <Card className="shadow-lg border-0 bg-white/95 backdrop-blur-sm">
          <CardContent className="p-3">{hoverContent}</CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default HoverCard;
