"use client";
import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  MessageSquare,
} from "lucide-react";
import toast from "react-hot-toast";
import CitationPopup from "./CitationPopup";
import AnimatedTyping from "./AnimatedTyping";
import HoverCard from "./HoverCard";

export default function UnifiedChat({
  setReportId,
  setGenerateData,
  selectedTemplate,
}) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm your AI assistant for creating professional reports. I can help you:\n\n1. **Design custom templates** - Just tell me what kind of report you need\n2. **Generate reports** - Upload documents and I'll create reports using your content\n3. **Refine templates** - Modify sections, tone, or structure as needed\n\nWhat would you like to do first?",
      type: "welcome",
      isTyping: true,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Update messages when a template is selected
  useEffect(() => {
    if (selectedTemplate) {
      setCurrentTemplate(selectedTemplate);
      // Add a message showing the selected template
      const templateMessage = {
        role: "assistant",
        content: `✅ **Template Selected: ${
          selectedTemplate.name
        }**\n\n**Description:** ${
          selectedTemplate.description
        }\n\n**Sections:**\n${selectedTemplate.template
          .map((section, index) => `${index + 1}. ${section}`)
          .join(
            "\n"
          )}\n\nYou can now:\n• Generate a report using this template\n• Modify the template structure\n• Ask questions about the template\n\nWhat would you like to do?`,
        type: "template_selected",
      };

      setMessages((prev) => {
        // Remove any existing template_selected messages
        const filtered = prev.filter((msg) => msg.type !== "template_selected");
        return [...filtered, templateMessage];
      });
    }
  }, [selectedTemplate]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // Determine if this is a template request or report generation request
      const isTemplateRequest =
        input.toLowerCase().includes("template") ||
        input.toLowerCase().includes("structure") ||
        input.toLowerCase().includes("sections") ||
        input.toLowerCase().includes("format") ||
        input.toLowerCase().includes("check") ||
        input.toLowerCase().includes("see") ||
        input.toLowerCase().includes("uploaded") ||
        input.toLowerCase().includes("content") ||
        input.toLowerCase().includes("suitable") ||
        input.toLowerCase().includes("create") ||
        input.toLowerCase().includes("design") ||
        input.toLowerCase().includes("suggest");

      let response;

      if (isTemplateRequest) {
        // Handle template generation/refinement
        response = await handleTemplateRequest(input.trim());
      } else {
        // Handle report generation
        response = await handleReportRequest(input.trim());
      }

      const assistantMessage = {
        role: "assistant",
        content: response.content,
        type: response.type,
        template: response.template,
        reportId: response.reportId,
        timestamp: new Date().toISOString(),
        isTyping: true,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Show success toast
      if (response.type === "report") {
        toast.success("Report generated successfully!", {
          duration: 3000,
          position: "top-right",
        });
      } else if (response.type === "template") {
        toast.success("Template updated!", {
          duration: 2000,
          position: "top-right",
        });
      }

      // Update report ID if a report was generated
      if (response.reportId) {
        setReportId(response.reportId);
      }

      // Update generate data for debug panel
      if (setGenerateData) {
        setGenerateData(response);
      }
    } catch (error) {
      console.error("Chat Error:", error);
      const errorMessage = {
        role: "assistant",
        content:
          "I apologize, but I encountered an error. Please try again or rephrase your request.",
        type: "error",
        timestamp: new Date().toISOString(),
        isTyping: true,
      };
      setMessages((prev) => [...prev, errorMessage]);

      // Show error toast
      toast.error("Something went wrong. Please try again.", {
        duration: 4000,
        position: "top-right",
      });
    }

    setLoading(false);
  };

  const handleTemplateRequest = async (query) => {
    // First, get available documents and samples to provide context
    let documentContext = null;
    try {
      const [sourcesResponse, samplesResponse] = await Promise.all([
        fetch("http://localhost:8000/documents/status"),
        fetch("http://localhost:8000/documents/samples"),
      ]);

      if (sourcesResponse.ok) {
        const sourcesData = await sourcesResponse.json();
        documentContext = sourcesData;
      }

      if (samplesResponse.ok) {
        const samplesData = await samplesResponse.json();
        if (documentContext) {
          documentContext.samples = samplesData.samples;
          documentContext.analysis_message = samplesData.message;
        }
      }
    } catch (error) {
      console.error("Error fetching document context:", error);
    }

    const response = await fetch("http://localhost:8000/templates/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: query,
        template_id: currentTemplate?.id || selectedTemplate?.id,
        chat_history: messages.slice(-10), // Last 10 messages for context
        context: documentContext, // Include document context
        selected_template: selectedTemplate, // Include selected template info
      }),
    });

    const data = await response.json();

    if (data.template) {
      setCurrentTemplate(data.template);
      return {
        content: data.response,
        type: "template",
        template: data.template,
      };
    }

    return {
      content:
        data.response ||
        "I can help you create a template. What kind of report do you need?",
      type: "template",
    };
  };

  const handleReportRequest = async (query) => {
    // First check if we have a template (from selector or current template)
    let sections = ["Executive Summary", "Key Findings", "Recommendations"];

    if (selectedTemplate && selectedTemplate.template) {
      sections = selectedTemplate.template;
    } else if (currentTemplate && currentTemplate.template) {
      sections = currentTemplate.template;
    }

    const response = await fetch("http://localhost:8000/reports/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sections: sections,
        query: query,
        top_k: 10,
      }),
    });

    const data = await response.json();

    if (data.report_id) {
      return {
        content: `✅ **Report Generated Successfully!**\n\nI've created a report using your uploaded documents with the following sections:\n${sections
          .map((s) => `• ${s}`)
          .join(
            "\n"
          )}\n\nClick on any citation in the preview below to see the source details.`,
        type: "report",
        reportId: data.report_id,
      };
    } else {
      return {
        content: `❌ **Report Generation Failed**\n\n${
          data.detail ||
          data.error ||
          "Please make sure you have uploaded documents and try again."
        }`,
        type: "error",
      };
    }
  };

  const handleCitationClick = (citation) => {
    setSelectedCitation(citation);
  };

  const closeCitationPopup = () => {
    setSelectedCitation(null);
  };

  const renderMessage = (message, index) => {
    const isUser = message.role === "user";

    return (
      <motion.div
        key={index}
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{
          duration: 0.4,
          delay: index * 0.1,
          type: "spring",
          stiffness: 100,
        }}
        className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
      >
        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`max-w-[80%] rounded-xl px-4 py-3 shadow-sm ${
            isUser
              ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white"
              : message.type === "error"
              ? "bg-red-50 text-red-800 border border-red-200"
              : "bg-white text-gray-800 border border-gray-200"
          }`}
        >
          <div className="flex items-start space-x-2">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring" }}
              className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                isUser
                  ? "bg-blue-400"
                  : "bg-gradient-to-r from-purple-400 to-pink-400"
              }`}
            >
              {isUser ? (
                <User className="h-4 w-4 text-white" />
              ) : (
                <Bot className="h-4 w-4 text-white" />
              )}
            </motion.div>

            <div className="flex-1">
              {message.isTyping && !isUser ? (
                <AnimatedTyping
                  text={message.content}
                  speed={20}
                  onComplete={() => {
                    setMessages((prev) =>
                      prev.map((msg, i) =>
                        i === index ? { ...msg, isTyping: false } : msg
                      )
                    );
                  }}
                  className="whitespace-pre-wrap"
                />
              ) : (
                <div className="whitespace-pre-wrap">{message.content}</div>
              )}

              {message.template && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  transition={{ delay: 0.5, duration: 0.3 }}
                  className="mt-3 p-3 bg-gray-50 rounded-lg border"
                >
                  <div className="flex items-center space-x-2 mb-2">
                    <Sparkles className="h-4 w-4 text-purple-500" />
                    <h4 className="font-semibold text-sm text-gray-700">
                      Current Template:
                    </h4>
                  </div>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {message.template.map((section, idx) => (
                      <motion.li
                        key={idx}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.6 + idx * 0.1 }}
                        className="flex items-center"
                      >
                        <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs mr-2 font-medium">
                          {idx + 1}
                        </span>
                        {section}
                      </motion.li>
                    ))}
                  </ul>
                </motion.div>
              )}

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="text-xs opacity-70 mt-2 flex items-center space-x-2"
              >
                <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                {message.type === "report" && (
                  <Badge variant="secondary" className="text-xs">
                    Report Generated
                  </Badge>
                )}
                {message.type === "template" && (
                  <Badge variant="outline" className="text-xs">
                    Template
                  </Badge>
                )}
              </motion.div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    );
  };

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="border-0 rounded-2xl bg-white/80 backdrop-blur-sm shadow-xl flex flex-col h-[600px] overflow-hidden"
      >
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="p-6 border-b bg-gradient-to-r from-blue-500 via-purple-500 to-blue-700 text-white relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20"></div>
          <div className="relative flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center"
              >
                <Bot className="h-6 w-6 text-white" />
              </motion.div>
              <div>
                <h2 className="font-bold text-xl flex items-center space-x-2">
                  <span>AI Report Assistant</span>
                  <motion.span
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="text-yellow-300"
                  >
                    ✨
                  </motion.span>
                </h2>
                <p className="text-sm opacity-90">
                  Unified template design & report generation
                </p>
              </div>
            </div>
            {(currentTemplate || selectedTemplate) && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 200 }}
                className="text-sm bg-white/20 backdrop-blur-sm text-white px-4 py-2 rounded-full border border-white/30"
              >
                <HoverCard
                  hoverContent={
                    <div className="text-sm">
                      <p className="font-medium">Template Details:</p>
                      <p className="text-gray-600">
                        {(currentTemplate || selectedTemplate).description}
                      </p>
                    </div>
                  }
                >
                  <div className="flex items-center space-x-2">
                    <MessageSquare className="h-4 w-4" />
                    <span>
                      {(currentTemplate || selectedTemplate).name ||
                        "Custom Template"}
                    </span>
                  </div>
                </HoverCard>
              </motion.div>
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-gray-50/50 to-white/50"
        >
          <AnimatePresence>
            {messages.map((message, index) => renderMessage(message, index))}
          </AnimatePresence>

          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <motion.div
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="bg-white rounded-xl px-4 py-3 shadow-sm border border-gray-200"
              >
                <div className="flex items-center space-x-3">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full flex items-center justify-center"
                  >
                    <Loader2 className="h-4 w-4 text-white" />
                  </motion.div>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-600 font-medium">
                      AI is thinking
                    </span>
                    <motion.div
                      animate={{ opacity: [0, 1, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                      className="flex space-x-1"
                    >
                      <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                      <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                      <div className="w-1 h-1 bg-blue-500 rounded-full"></div>
                    </motion.div>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
          className="p-6 border-t bg-white/80 backdrop-blur-sm"
        >
          <div className="flex space-x-3">
            <motion.div
              whileFocus={{ scale: 1.02 }}
              className="flex-1 relative"
            >
              <Input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask me to create a template, generate a report, or refine your content..."
                className="pr-12 h-12 text-base border-2 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 rounded-xl"
                disabled={loading}
              />
              <motion.div
                animate={{ scale: input.trim() ? 1.1 : 1 }}
                className="absolute right-3 top-1/2 transform -translate-y-1/2"
              >
                <MessageSquare className="h-5 w-5 text-gray-400" />
              </motion.div>
            </motion.div>

            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="h-12 px-8 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 1,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                  >
                    <Loader2 className="h-5 w-5" />
                  </motion.div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Send className="h-5 w-5" />
                    <span>Send</span>
                  </div>
                )}
              </Button>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="mt-3 flex items-center space-x-2 text-sm text-gray-500"
          >
            <Sparkles className="h-4 w-4 text-yellow-500" />
            <span>
              Try: "Create a template for a market analysis report" or "Generate
              a report about our Q3 performance"
            </span>
          </motion.div>
        </motion.div>

        {selectedCitation && (
          <CitationPopup
            citation={selectedCitation}
            onClose={closeCitationPopup}
          />
        )}
      </motion.div>
    </TooltipProvider>
  );
}
