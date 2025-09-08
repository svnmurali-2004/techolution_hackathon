/**
 * Utility functions for cleaning and formatting text
 */

export const cleanMarkdown = (text) => {
  if (!text) return "";

  return (
    text
      // Remove markdown bold formatting
      .replace(/\*\*(.*?)\*\*/g, "$1")
      // Remove markdown italic formatting
      .replace(/\*(.*?)\*/g, "$1")
      // Remove markdown headers
      .replace(/^#{1,6}\s+/gm, "")
      // Remove markdown links but keep the text
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      // Remove markdown code blocks
      .replace(/```[\s\S]*?```/g, "")
      // Remove inline code
      .replace(/`([^`]+)`/g, "$1")
      // Remove markdown lists
      .replace(/^[\s]*[-*+]\s+/gm, "• ")
      // Remove markdown numbered lists
      .replace(/^[\s]*\d+\.\s+/gm, "")
      // Clean up extra whitespace
      .replace(/\n\s*\n/g, "\n\n")
      .trim()
  );
};

export const formatTextForDisplay = (text) => {
  if (!text) return "";

  // Clean markdown first
  let cleaned = cleanMarkdown(text);

  // Add some basic formatting for better readability
  cleaned = cleaned
    // Make bullet points more readable
    .replace(/•/g, "•")
    // Ensure proper spacing around sections
    .replace(/([.!?])\s*([A-Z])/g, "$1\n\n$2")
    // Clean up multiple newlines
    .replace(/\n{3,}/g, "\n\n");

  return cleaned;
};

export const extractSections = (text) => {
  if (!text) return [];

  const sections = [];
  const lines = text.split("\n");
  let currentSection = { title: "", content: "" };

  for (const line of lines) {
    const trimmedLine = line.trim();

    // Check if this is a section header (starts with number or bullet)
    if (trimmedLine.match(/^\d+\.\s+/) || trimmedLine.match(/^•\s+/)) {
      // Save previous section if it has content
      if (currentSection.title || currentSection.content) {
        sections.push({ ...currentSection });
      }

      // Start new section
      currentSection = {
        title: trimmedLine.replace(/^\d+\.\s+/, "").replace(/^•\s+/, ""),
        content: "",
      };
    } else if (trimmedLine) {
      // Add to current section content
      currentSection.content +=
        (currentSection.content ? "\n" : "") + trimmedLine;
    }
  }

  // Add the last section
  if (currentSection.title || currentSection.content) {
    sections.push(currentSection);
  }

  return sections;
};

