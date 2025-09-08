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
  Brain,
  Zap,
  Star,
  Crown,
  FileText,
  Layout,
  PanelLeft,
  PanelRight,
} from "lucide-react";
import toast from "react-hot-toast";
import CitationPopup from "./CitationPopup";
import AnimatedTyping from "./AnimatedTyping";
import HoverCard from "./HoverCard";
import DocumentPreview from "./DocumentPreview";
import VoiceInput from "./VoiceInput";
import { cleanMarkdown, formatTextForDisplay } from "../utils/textFormatter";
import AIAnimation, {
  AILoadingState,
  AISuccessState,
  AITypingIndicator,
} from "./AIAnimation";

export default function EnhancedUnifiedChat({
  setReportId,
  setGenerateData,
  selectedTemplate,
  user,
  chatTrigger,
  // Chat state props
  messages: propMessages,
  setMessages: propSetMessages,
  input: propInput,
  setInput: propSetInput,
  loading: propLoading,
  setLoading: propSetLoading,
  selectedCitation: propSelectedCitation,
  setSelectedCitation: propSetSelectedCitation,
  aiThinking: propAiThinking,
  setAiThinking: propSetAiThinking,
  showDocumentPreview: propShowDocumentPreview,
  setShowDocumentPreview: propSetShowDocumentPreview,
  previewReportId: propPreviewReportId,
  setPreviewReportId: propSetPreviewReportId,
  documentContext: propDocumentContext,
  setDocumentContext: propSetDocumentContext,
  showSuccess: propShowSuccess,
  setShowSuccess: propSetShowSuccess,
  layoutMode: propLayoutMode,
  setLayoutMode: propSetLayoutMode,
  // Function to refresh template count
  refreshTemplateCount,
}) {
  const [messages, setMessages] = propMessages
    ? [propMessages, propSetMessages]
    : useState([
        {
          role: "assistant",
          content: user
            ? `Welcome back, ${
                user.displayName || user.email?.split("@")[0]
              }! 🎉 I'm your AI assistant with **true agentic AI capabilities** for creating professional reports. I can help you:\n\n🤖 **Agentic AI Features:**\n• **Autonomous Decision Making** - I make intelligent decisions about how to process your requests\n• **Multi-step Reasoning** - I break down complex tasks and execute them step by step\n• **Tool Usage** - I use specialized tools to process documents, analyze content, and generate reports\n• **Memory & Context** - I remember our conversation and use context to provide better responses\n• **Goal-oriented Behavior** - I work towards your objectives with persistent focus\n\n📋 **Traditional Features:**\n• **Design custom templates** - Tell me what kind of report you need\n• **Generate reports** - Upload documents and I'll create reports using your content\n• **Refine templates** - Modify sections, tone, or structure as needed\n\n**Try agentic commands like:**\n• "Generate a report with executive summary and recommendations"\n• "Process my documents and create a business analysis report"\n• "Analyze my documents and suggest the best template"\n• "Autonomously process my documents and create a comprehensive report"\n\nWhat would you like me to help you with?`
            : 'Hello! I\'m your AI assistant with **true agentic AI capabilities** for creating professional reports. I can help you:\n\n🤖 **Agentic AI Features:**\n• **Autonomous Decision Making** - I make intelligent decisions about how to process your requests\n• **Multi-step Reasoning** - I break down complex tasks and execute them step by step\n• **Tool Usage** - I use specialized tools to process documents, analyze content, and generate reports\n• **Memory & Context** - I remember our conversation and use context to provide better responses\n• **Goal-oriented Behavior** - I work towards your objectives with persistent focus\n\n📋 **Traditional Features:**\n• **Design custom templates** - Tell me what kind of report you need\n• **Generate reports** - Upload documents and I\'ll create reports using your content\n• **Refine templates** - Modify sections, tone, or structure as needed\n\n**Try agentic commands like:**\n• "Generate a report with executive summary and recommendations"\n• "Process my documents and create a business analysis report"\n• "Analyze my documents and suggest the best template"\n• "Autonomously process my documents and create a comprehensive report"\n\nWhat would you like me to help you with?',
          type: "welcome",
          isTyping: true,
        },
      ]);
  const [input, setInput] = propInput
    ? [propInput, propSetInput]
    : useState("");
  const [loading, setLoading] = propLoading
    ? [propLoading, propSetLoading]
    : useState(false);
  const [currentTemplate, setCurrentTemplate] = useState(null);
  const [selectedCitation, setSelectedCitation] = propSelectedCitation
    ? [propSelectedCitation, propSetSelectedCitation]
    : useState(null);
  const [aiThinking, setAiThinking] = propAiThinking
    ? [propAiThinking, propSetAiThinking]
    : useState(false);
  const [showDocumentPreview, setShowDocumentPreview] = useState(false);
  const [previewReportId, setPreviewReportId] = useState(null);
  const [documentContext, setDocumentContext] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [layoutMode, setLayoutMode] = useState("normal"); // "normal" or "dual-pane"
  const messagesEndRef = useRef(null);
  const welcomeMessageShownRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleCloseDocumentPreview = () => {
    setShowDocumentPreview(false);
    setPreviewReportId(null);
    // Optionally switch back to normal mode when closing preview
    // setLayoutMode("normal");
  };

  const handleVoiceTranscript = (transcript) => {
    setInput(transcript);
    // Auto-send the voice input
    setTimeout(() => {
      handleSubmit(new Event("submit"));
    }, 500);
  };

  const toggleLayoutMode = () => {
    if (layoutMode === "normal") {
      // Switch to dual-pane mode
      setLayoutMode("dual-pane");
      // If we have a real report, show it; otherwise show a placeholder
      if (previewReportId && previewReportId !== "demo-report") {
        setShowDocumentPreview(true);
      } else {
        // Create a test report ID for demonstration
        setPreviewReportId("demo-report");
        setShowDocumentPreview(true);
      }
    } else {
      // Switch to normal mode
      setLayoutMode("normal");
      setShowDocumentPreview(false);
    }
  };

  const fetchDocumentContext = async () => {
    try {
      const response = await fetch("http://localhost:8000/documents/status");
      const data = await response.json();
      setDocumentContext(data);
      console.log("📄 Document context updated:", data);
    } catch (error) {
      console.error("Error fetching document context:", error);
      setDocumentContext({ document_count: 0, sources: [] });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch document context on mount and when chatTrigger changes
  useEffect(() => {
    fetchDocumentContext();
  }, [chatTrigger]);

  useEffect(() => {
    if (selectedTemplate) {
      const templateMessage = {
        role: "assistant",
        content: `Great choice! I've selected the **${
          selectedTemplate.name
        }** template for you.\n\n**Template Details:**\n- **Description:** ${
          selectedTemplate.description
        }\n- **Category:** ${
          selectedTemplate.category
        }\n- **Sections:** ${selectedTemplate.template.join(
          ", "
        )}\n\nYou can now start chatting with me to refine this template or generate a report using your uploaded documents!`,
        type: "template_selected",
        template: selectedTemplate,
        isTyping: true,
      };
      setMessages((prev) => [...prev, templateMessage]);
    }
  }, [selectedTemplate]);

  // Check for documents and generate automatic message
  useEffect(() => {
    const checkDocumentsAndGenerateMessage = async () => {
      try {
        const response = await fetch("http://localhost:8000/documents/status");
        if (response.ok) {
          const data = await response.json();
          const documentCount = data.document_count || 0;

          // Only generate message if there are documents and no previous document-related messages
          if (documentCount > 0 && !welcomeMessageShownRef.current) {
            const hasDocumentMessage = messages.some(
              (msg) =>
                msg.type === "document_analysis" ||
                msg.content.includes("I can see you've uploaded") ||
                msg.content.includes("documents to analyze")
            );

            if (!hasDocumentMessage) {
              welcomeMessageShownRef.current = true;
              // Get document samples for better analysis
              try {
                const samplesResponse = await fetch(
                  "http://localhost:8000/documents/samples"
                );
                let documentInfo = "";

                if (samplesResponse.ok) {
                  const samplesData = await samplesResponse.json();
                  if (samplesData.samples && samplesData.samples.length > 0) {
                    documentInfo = `\n\n**Document Preview:**\n${samplesData.samples
                      .slice(0, 2)
                      .map((sample) => {
                        const content = sample.content_preview || sample;
                        return `• ${content.substring(0, 100)}...`;
                      })
                      .join("\n")}`;
                  }
                }

                const documentMessage = {
                  role: "assistant",
                  content: `Great! I can see you've uploaded ${documentCount} document${
                    documentCount > 1 ? "s" : ""
                  } to analyze! 📄✨${documentInfo}\n\nI'm ready to help you create a professional report using your uploaded content. You can:\n\n1. **Ask me to analyze** your documents\n2. **Generate a report** using a template\n3. **Ask specific questions** about the content\n4. **Request modifications** to any template\n\nWhat would you like me to help you with first?`,
                  type: "document_analysis",
                  timestamp: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, documentMessage]);
              } catch (error) {
                console.error("Error getting document samples:", error);
              }
            }
          }
        }
      } catch (error) {
        console.error("Error checking documents:", error);
      }
    };

    // Only check documents when chatTrigger changes (not on every message change)
    if (chatTrigger > 0) {
      checkDocumentsAndGenerateMessage();
    }
  }, [chatTrigger]); // Only run when chatTrigger changes

  const sendMessage = async (query) => {
    if (!query.trim()) return;

    const userMessage = {
      role: "user",
      content: query,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setAiThinking(true);

    try {
      // Check if this is the first user message (start of new session)
      const isFirstUserMessage =
        messages.filter((msg) => msg.role === "user").length === 0;

      // Only start a new session if user explicitly requests it or if no documents exist
      // Don't automatically clear documents on first message
      if (isFirstUserMessage) {
        try {
          // Check if documents exist first
          const statusResponse = await fetch(
            "http://localhost:8000/documents/status"
          );
          const statusData = await statusResponse.json();

          // Only clear if there are existing documents and user wants a fresh start
          if (statusData.document_count > 0) {
            console.log("Documents exist, keeping them for this session");
          } else {
            console.log("No existing documents, session ready");
          }
        } catch (error) {
          console.error("Error checking document status:", error);
        }
      }

      // Fetch document context from current session only
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

      // Check if user wants to use agentic AI system
      const isSimpleGenerate =
        query.toLowerCase().trim() === "generate" ||
        query.toLowerCase().trim() === "generate report" ||
        (query.toLowerCase().includes("generate") &&
          query.split(" ").length <= 3);

      // Check for generate-related commands (more comprehensive)
      const hasGenerateIntent =
        query.toLowerCase().includes("generate") ||
        query.toLowerCase().includes("create report") ||
        query.toLowerCase().includes("make report") ||
        query.toLowerCase().includes("build report") ||
        query.toLowerCase().includes("take the template") ||
        query.toLowerCase().includes("use template") ||
        query.toLowerCase().includes("fix that and generate") ||
        query.toLowerCase().includes("ok fix that and generate");

      const wantsAgenticAI =
        isSimpleGenerate ||
        hasGenerateIntent ||
        query.toLowerCase().includes("process documents") ||
        query.toLowerCase().includes("report from") ||
        query.toLowerCase().includes("generate from") ||
        query.toLowerCase().includes("proceed") ||
        query.toLowerCase().includes("agent") ||
        query.toLowerCase().includes("automate") ||
        query.toLowerCase().includes("autonomous") ||
        query.toLowerCase().includes("intelligent") ||
        query.toLowerCase().includes("save-template") ||
        query.toLowerCase().includes("smart");

      const wantsAnalysis =
        (query.toLowerCase().includes("analyse") ||
          query.toLowerCase().includes("analyze") ||
          query.toLowerCase().includes("check documents") ||
          query.toLowerCase().includes("what's in") ||
          query.toLowerCase().includes("show me")) &&
        !query.toLowerCase().includes("report") &&
        !query.toLowerCase().includes("generate") &&
        !query.toLowerCase().includes("create");

      // Debug logging
      console.log("🔍 Command Analysis:", {
        query: query,
        isSimpleGenerate: isSimpleGenerate,
        hasGenerateIntent: hasGenerateIntent,
        wantsAgenticAI: wantsAgenticAI,
        wantsAnalysis: wantsAnalysis,
        documentCount: documentContext?.document_count || 0,
      });

      let response;
      if (wantsAgenticAI) {
        // Use the agentic AI system for autonomous processing
        // Agentic AI can work with or without documents
        console.log("🤖 Routing to Agentic AI:", query);
        console.log("🤖 Sending to Agentic AI:", {
          command: query,
          selectedTemplate: selectedTemplate,
          currentTemplate: currentTemplate,
          documentContext: documentContext,
        });

        response = await fetch("http://localhost:8000/agentic/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            command: query,
            context: documentContext || { document_count: 0, sources: [] },
            selected_template: selectedTemplate, // Include selected template info
            current_template: currentTemplate, // Include current template info
          }),
        });
      } else if (
        wantsAnalysis &&
        documentContext &&
        documentContext.document_count > 0
      ) {
        // Use the dedicated analyze endpoint for simple analysis
        response = await fetch("http://localhost:8000/documents/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
      } else {
        // Use the regular chat endpoint
        response = await fetch("http://localhost:8000/templates/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: query,
            template_id: currentTemplate?.id || selectedTemplate?.id,
            chat_history: messages.slice(-10),
            context: documentContext,
            selected_template: selectedTemplate,
          }),
        });
      }

      const data = await response.json();

      if (data.analysis) {
        // Handle document analysis response
        const assistantMessage = {
          role: "assistant",
          content: data.analysis,
          type: "document_analysis",
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else if (
        data.response &&
        data.response.includes("Report Generated Successfully") &&
        (data.response.includes("Report ID:") ||
          data.response.includes("**Report ID:**"))
      ) {
        // Handle agentic AI report generation
        const reportIdMatch = data.response.match(
          /(?:\*\*)?Report ID:(?:\*\*)?\s*([a-f0-9-]+)/i
        );
        if (reportIdMatch) {
          const reportId = reportIdMatch[1];
          setReportId(reportId);
          setGenerateData({ report_id: reportId, sections: [] });
          setShowSuccess(true);

          // Show dual-pane interface
          setPreviewReportId(reportId);
          setShowDocumentPreview(true);
          setLayoutMode("dual-pane");

          const assistantMessage = {
            role: "assistant",
            content: data.response,
            type: "report_generated",
            reportId: reportId,
            isTyping: true,
          };
          setMessages((prev) => [...prev, assistantMessage]);
          toast.success("Report generated successfully! 🎉");
        } else {
          // Fallback for agentic response without report ID
          const assistantMessage = {
            role: "assistant",
            content: data.response,
            type: "agentic_response",
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
      } else if (data.template) {
        setCurrentTemplate(data.template);
        const assistantMessage = {
          role: "assistant",
          content: data.response,
          type: "template",
          template: data.template,
          isTyping: true,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else if (data.report_id) {
        setReportId(data.report_id);
        setGenerateData(data);
        setShowSuccess(true);

        // Show dual-pane interface
        setPreviewReportId(data.report_id);
        setShowDocumentPreview(true);
        setLayoutMode("dual-pane");
        const assistantMessage = {
          role: "assistant",
          content: `✅ **Report Generated Successfully!**\n\nI've created a report using your uploaded documents with the following sections:\n${
            data.sections?.map((s) => `• ${s}`).join("\n") ||
            "• Executive Summary\n• Key Findings\n• Recommendations"
          }\n\nClick on any citation in the preview below to see the source details.`,
          type: "report_generated",
          reportId: data.report_id,
          isTyping: true,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        toast.success("Report generated successfully! 🎉");
      } else {
        // Handle regular responses (including agentic responses)
        const assistantMessage = {
          role: "assistant",
          content:
            data.response || "I'm here to help! What would you like to do?",
          type: data.agentic ? "agentic_response" : "text",
          isTyping: true,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // Check if a template was saved and refresh template count
        if (
          data.response &&
          data.response.includes("Template Saved Successfully")
        ) {
          console.log("🔄 Template saved, refreshing template count...");
          if (refreshTemplateCount) {
            refreshTemplateCount();
          }
        }
      }
    } catch (error) {
      console.error("Error:", error);
      const errorMessage = {
        role: "assistant",
        content: "I apologize, but I encountered an error. Please try again.",
        type: "error",
        isTyping: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast.error("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
      setAiThinking(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const renderMessage = (message, index) => {
    const isUser = message.role === "user";
    const isTyping = message.isTyping;

    return (
      <motion.div
        key={index}
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, delay: index * 0.1 }}
        className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
      >
        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`flex items-start space-x-3 max-w-[80%] ${
            isUser ? "flex-row-reverse space-x-reverse" : ""
          }`}
        >
          {/* Avatar */}
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg ${
              isUser
                ? "bg-gradient-to-r from-blue-500 to-purple-500"
                : "bg-gradient-to-r from-purple-500 to-pink-500"
            }`}
          >
            {isUser ? (
              <User className="h-5 w-5 text-white" />
            ) : (
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Brain className="h-5 w-5 text-white" />
              </motion.div>
            )}
          </motion.div>

          {/* Message Content */}
          <motion.div
            initial={{ opacity: 0, x: isUser ? 20 : -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className={`rounded-2xl px-4 py-3 shadow-lg ${
              isUser
                ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white"
                : "bg-white border border-gray-200"
            }`}
          >
            {isTyping && !isUser ? (
              <div className="space-y-2">
                <AnimatedTyping
                  text={formatTextForDisplay(message.content)}
                  speed={50}
                  typeByWords={true}
                  onComplete={() => {
                    setMessages((prev) =>
                      prev.map((msg, i) =>
                        i === index ? { ...msg, isTyping: false } : msg
                      )
                    );
                  }}
                  className="text-gray-800 leading-relaxed"
                />
              </div>
            ) : (
              <div className="text-sm whitespace-pre-wrap">
                {formatTextForDisplay(message.content)}
              </div>
            )}

            {/* Template Display */}
            {message.template && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mt-3 p-3 bg-gray-50 rounded-lg border"
              >
                <div className="flex items-center space-x-2 mb-2">
                  <Crown className="h-4 w-4 text-yellow-500" />
                  <span className="font-semibold text-sm">
                    Template: {message.template.name}
                  </span>
                </div>
                <div className="text-xs text-gray-600">
                  <p className="mb-1">{message.template.description}</p>
                  <div className="flex flex-wrap gap-1">
                    {message.template.template.map((section, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {section}
                      </Badge>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Timestamp */}
            <div
              className={`text-xs mt-2 ${
                isUser ? "text-blue-100" : "text-gray-500"
              }`}
            >
              {new Date(message.timestamp || Date.now()).toLocaleTimeString()}
            </div>
          </motion.div>
        </motion.div>
      </motion.div>
    );
  };

  return (
    <TooltipProvider>
      <div
        className="flex bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 relative"
        style={{ height: "calc(100vh - 80px)" }}
      >
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(59,130,246,0.1)_1px,transparent_0)] bg-[length:20px_20px] opacity-30"></div>
        {/* Main Chat Area */}
        <div
          className={`h-full flex flex-col transition-all duration-500 ease-in-out ${
            layoutMode === "dual-pane" && showDocumentPreview
              ? "w-1/2 border-r border-gray-200 shadow-lg"
              : "w-full"
          }`}
        >
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex-shrink-0 sticky top-0 z-10 p-4 border-b bg-white/80 backdrop-blur-sm"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{
                    duration: 20,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                  className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center"
                >
                  <Brain className="h-6 w-6 text-white" />
                </motion.div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-semibold text-gray-900">
                      AI Report Assistant
                    </h3>
                    <Badge
                      variant={
                        layoutMode === "dual-pane" ? "default" : "secondary"
                      }
                      className="text-xs"
                    >
                      {layoutMode === "dual-pane" ? "Dual Pane" : "Normal"}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600">
                    {user
                      ? `Welcome, ${
                          user.displayName || user.email?.split("@")[0]
                        }!`
                      : "Your AI-powered report generator"}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                {/* Layout Toggle Button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={
                        layoutMode === "dual-pane" ? "default" : "outline"
                      }
                      size="sm"
                      onClick={toggleLayoutMode}
                      className="flex items-center space-x-2"
                    >
                      {layoutMode === "normal" ? (
                        <>
                          <PanelRight className="h-4 w-4" />
                          <span>Dual Pane</span>
                        </>
                      ) : (
                        <>
                          <PanelLeft className="h-4 w-4" />
                          <span>Normal</span>
                        </>
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>
                      Switch to{" "}
                      {layoutMode === "normal" ? "dual-pane" : "normal"} layout
                    </p>
                  </TooltipContent>
                </Tooltip>

                {selectedTemplate && (
                  <HoverCard
                    hoverContent={
                      <div className="p-2">
                        <p className="text-sm font-medium">
                          {selectedTemplate.name}
                        </p>
                        <p className="text-xs text-gray-600">
                          {selectedTemplate.description}
                        </p>
                      </div>
                    }
                  >
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <Badge variant="secondary" className="cursor-pointer">
                        <Star className="h-3 w-3 mr-1" />
                        {selectedTemplate.name}
                      </Badge>
                    </motion.div>
                  </HoverCard>
                )}
              </div>
            </div>
          </motion.div>

          {/* Messages */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
          >
            {messages.map((message, index) => renderMessage(message, index))}

            {/* AI Thinking State */}
            <AnimatePresence>
              {aiThinking && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="flex justify-start"
                >
                  <AILoadingState
                    message="AI is analyzing your request and documents..."
                    size={60}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Success State */}
            <AnimatePresence>
              {showSuccess && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="flex justify-center"
                >
                  <AISuccessState
                    message="Report generated successfully!"
                    size={80}
                    onComplete={() => setShowSuccess(false)}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </motion.div>

          {/* Input */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex-shrink-0 p-4 border-t bg-white/80 backdrop-blur-sm"
          >
            <form onSubmit={handleSubmit} className="flex space-x-3">
              <motion.div whileFocus={{ scale: 1.02 }} className="flex-1">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything about your report..."
                  disabled={loading}
                  className="w-full"
                />
              </motion.div>
              <VoiceInput
                onTranscript={handleVoiceTranscript}
                disabled={loading}
              />
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
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
                      <Loader2 className="h-4 w-4" />
                    </motion.div>
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </motion.div>
            </form>
          </motion.div>
        </div>

        {/* Visual Separator */}
        {layoutMode === "dual-pane" && showDocumentPreview && (
          <div className="w-px bg-gradient-to-b from-transparent via-gray-300 to-transparent h-full"></div>
        )}

        {/* Document Preview Side Panel */}
        <div
          className={`h-full transition-all duration-500 ease-in-out ${
            layoutMode === "dual-pane" && showDocumentPreview
              ? "w-1/2 border-l border-gray-200 shadow-lg bg-white"
              : "w-0 overflow-hidden"
          }`}
        >
          <DocumentPreview
            reportId={previewReportId}
            isVisible={showDocumentPreview}
            onClose={handleCloseDocumentPreview}
          />
        </div>

        {/* Citation Popup */}
        {selectedCitation && (
          <CitationPopup
            citation={selectedCitation}
            onClose={() => setSelectedCitation(null)}
          />
        )}
      </div>
    </TooltipProvider>
  );
}
