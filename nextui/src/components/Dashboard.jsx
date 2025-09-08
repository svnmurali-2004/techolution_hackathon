"use client";
import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Toaster, toast } from "react-hot-toast";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  FileText,
  MessageSquare,
  LayoutTemplate,
  Eye,
  Settings,
  Trash2,
  RotateCcw,
  Upload,
  Sparkles,
  BookOpen,
  Download,
  Zap,
  TrendingUp,
  Users,
} from "lucide-react";
import FileUpload from "./FileUpload";
import UnifiedChat from "./UnifiedChat";
import EnhancedUnifiedChat from "./EnhancedUnifiedChat";
import TemplateSelector from "./TemplateSelector";
import EnhancedTemplateSelector from "./EnhancedTemplateSelector";
import OutputPreview from "./OutputPreview";
import ApiDebugPanel from "./ApiDebugPanel";
import ParallaxSection from "./ParallaxSection";
import HoverCard from "./HoverCard";
import RoyalWelcome from "./RoyalWelcome";
import ParticleField from "./ParticleField";
import GoogleAuthModal from "./GoogleAuthModal";
import { auth } from "@/lib/firebase";
import { onAuthStateChanged, signOut } from "firebase/auth";

export default function Dashboard() {
  const [reportId, setReportId] = useState("");
  const [generateData, setGenerateData] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [activeTab, setActiveTab] = useState("upload");
  const [showWelcome, setShowWelcome] = useState(true);
  const [user, setUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatTrigger, setChatTrigger] = useState(0);
  const welcomeShownRef = useRef(false);
  const [showProfile, setShowProfile] = useState(false);

  // Chat state to persist across tab switches
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatSelectedCitation, setChatSelectedCitation] = useState(null);
  const [chatAiThinking, setChatAiThinking] = useState(false);
  const [chatShowDocumentPreview, setChatShowDocumentPreview] = useState(false);
  const [chatPreviewReportId, setChatPreviewReportId] = useState(null);
  const [chatDocumentContext, setChatDocumentContext] = useState(null);
  const [chatShowSuccess, setChatShowSuccess] = useState(false);
  const [chatLayoutMode, setChatLayoutMode] = useState("normal");

  // Dynamic stats
  const [documentCount, setDocumentCount] = useState(0);
  const [templateCount, setTemplateCount] = useState(0);

  // Function to fetch current counts
  const fetchStats = async () => {
    try {
      // Fetch document count
      const docResponse = await fetch("http://localhost:8000/documents/status");
      if (docResponse.ok) {
        const docData = await docResponse.json();
        setDocumentCount(docData.document_count || 0);
      }

      // Fetch template count
      const templateResponse = await fetch(
        "http://localhost:8000/templates/list"
      );
      if (templateResponse.ok) {
        const templateData = await templateResponse.json();
        setTemplateCount(Array.isArray(templateData) ? templateData.length : 0);
      }
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  // Initialize welcome message when user is available
  useEffect(() => {
    if (user && chatMessages.length === 0) {
      setChatMessages([
        {
          role: "assistant",
          content: `Welcome back, ${
            user.displayName || user.email?.split("@")[0]
          }! I'm ready to help you create a professional report using your uploaded content. You can:

• Ask me to analyze your documents
• Generate a report using a template
• Ask specific questions about the content
• Request modifications to any template

What would you like me to help you with first?`,
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  }, [user, chatMessages.length]);

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setActiveTab("chat");
  };

  // Firebase Auth State Management
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
    });
    return () => unsubscribe();
  }, []);

  // Fetch stats when component mounts and when user changes
  useEffect(() => {
    if (user) {
      fetchStats();
    }
  }, [user]);

  // Periodically refresh stats to keep them up to date
  useEffect(() => {
    if (user) {
      const interval = setInterval(() => {
        fetchStats();
      }, 30000); // Refresh every 30 seconds

      return () => clearInterval(interval);
    }
  }, [user]);

  const handleAuthSuccess = (user) => {
    setUser(user);
    setShowAuth(false);

    // Only show welcome toast once per session
    if (user && !welcomeShownRef.current) {
      welcomeShownRef.current = true;
      toast.success(
        `Welcome, ${user.displayName || user.email?.split("@")[0]}! 🎉`
      );
    }
  };

  const handleNewChat = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/documents/session/start",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        setSelectedTemplate(null);
        setReportId("");
        setGenerateData(null);

        // Clear all chat-related state
        setChatMessages([]);
        setChatInput("");
        setChatLoading(false);
        setChatSelectedCitation(null);
        setChatAiThinking(false);
        setChatShowDocumentPreview(false);
        setChatPreviewReportId(null);
        setChatDocumentContext(null);
        setChatShowSuccess(false);
        setChatLayoutMode("normal");

        // Reset welcome message flag so it shows again for new session
        welcomeShownRef.current = false;

        setActiveTab("chat"); // Stay on chat tab for new conversation
        toast.success(
          "New chat started! Documents preserved for report generation. 🚀"
        );
      }
    } catch (error) {
      console.error("Error starting new session:", error);
      toast.error("Failed to start new session");
    }
  };

  const handleDeleteAllDocuments = async () => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      "⚠️ Are you sure you want to delete ALL uploaded documents?\n\n" +
        "This action cannot be undone and will:\n" +
        "• Remove all documents from the system\n" +
        "• Clear the chat history\n" +
        "• Templates will be preserved\n\n" +
        "Type 'DELETE ALL' to confirm:"
    );

    if (!confirmed) return;

    // Double confirmation with text input
    const userInput = window.prompt(
      "This will permanently delete ALL documents. Type 'DELETE ALL' to confirm:"
    );

    if (userInput !== "DELETE ALL") {
      toast.error("Operation cancelled. Documents preserved.");
      return;
    }

    try {
      const response = await fetch(
        "http://localhost:8000/documents/session/reset-all",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);

        // Clear document-related state but preserve templates
        setReportId("");
        setGenerateData(null);
        setChatMessages([]);
        setChatInput("");
        setChatLoading(false);
        setChatSelectedCitation(null);
        setChatAiThinking(false);
        setChatShowDocumentPreview(false);
        setChatPreviewReportId(null);
        setChatDocumentContext(null);
        setChatShowSuccess(false);
        setChatLayoutMode("normal");
        welcomeShownRef.current = false;

        // Note: selectedTemplate is preserved - templates remain available

        // Refresh stats to show 0 documents
        fetchStats();

        setActiveTab("upload");
        toast.success("All documents deleted! Templates preserved. 🗑️");
      } else {
        toast.error("Failed to delete documents");
      }
    } catch (error) {
      console.error("Error deleting documents:", error);
      toast.error("Failed to delete documents");
    }
  };

  const handleRecoverCollection = async () => {
    try {
      const response = await fetch(
        "http://localhost:8000/documents/collection/recover",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (response.ok) {
        const data = await response.json();
        toast.success("Collection recovered successfully! 🔧");

        // Refresh stats to show current document count
        fetchStats();
      } else {
        toast.error("Failed to recover collection");
      }
    } catch (error) {
      console.error("Error recovering collection:", error);
      toast.error("Failed to recover collection");
    }
  };

  const handleResetCollection = async () => {
    const confirmed = window.confirm(
      "⚠️ Are you sure you want to reset the collection?\n\n" +
        "This will:\n" +
        "• Delete all documents from the system\n" +
        "• Clear the ChromaDB collection\n" +
        "• Templates will be preserved\n\n" +
        "This action cannot be undone!"
    );

    if (!confirmed) return;

    try {
      const response = await fetch(
        "http://localhost:8000/documents/session/reset-all",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);

        // Clear document-related state but preserve templates
        setReportId("");
        setGenerateData(null);
        setChatMessages([]);
        setChatInput("");
        setChatLoading(false);
        setChatSelectedCitation(null);
        setChatAiThinking(false);
        setChatShowDocumentPreview(false);
        setChatPreviewReportId(null);
        setChatDocumentContext(null);
        setChatShowSuccess(false);
        setChatLayoutMode("normal");
        welcomeShownRef.current = false;

        // Refresh stats to show 0 documents
        fetchStats();

        setActiveTab("upload");
        toast.success("Collection reset successfully! 🔄");
      } else {
        toast.error("Failed to reset collection");
      }
    } catch (error) {
      console.error("Error resetting collection:", error);
      toast.error("Failed to reset collection");
    }
  };

  const handleUploadSuccess = (uploadData) => {
    // Switch to chat tab
    setActiveTab("chat");

    // Trigger document check in chat component
    setChatTrigger((prev) => prev + 1);

    // Refresh stats to update document count
    fetchStats();

    // The EnhancedUnifiedChat component will automatically generate a welcome message
    // when it detects documents are available, so we don't need a separate toast here
  };

  const handleProfileClick = () => {
    setShowProfile(true);
  };

  const handleLogout = async () => {
    try {
      // Sign out from Firebase
      await signOut(auth);

      // Clear backend session (optional - for cleanup)
      try {
        await fetch("http://localhost:8000/documents/session/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
      } catch (backendError) {
        console.log(
          "Backend session cleanup failed (non-critical):",
          backendError
        );
      }

      // Clear local state
      setUser(null);
      setShowProfile(false);
      setShowAuth(true);

      // Clear all chat-related state
      setChatMessages([]);
      setChatInput("");
      setChatLoading(false);
      setChatSelectedCitation(null);
      setChatAiThinking(false);
      setChatShowDocumentPreview(false);
      setChatPreviewReportId(null);
      setChatDocumentContext(null);
      setChatShowSuccess(false);
      setChatLayoutMode("normal");

      // Reset other state
      setReportId("");
      setGenerateData(null);
      setSelectedTemplate(null);
      setActiveTab("upload");

      // Reset welcome message flag
      welcomeShownRef.current = false;

      toast.success("Logged out successfully! 👋");
    } catch (error) {
      console.error("Error signing out:", error);
      toast.error("Failed to sign out. Please try again.");
    }
  };

  // Function to refresh template count (can be called from child components)
  const refreshTemplateCount = () => {
    fetchStats();
  };

  const stats = [
    {
      label: "Documents Uploaded",
      value: documentCount.toString(),
      icon: Upload,
      color: "from-blue-500 to-blue-600",
      hoverColor: "from-blue-600 to-blue-700",
    },
    {
      label: "Templates Available",
      value: templateCount.toString(),
      icon: LayoutTemplate,
      color: "from-purple-500 to-purple-600",
      hoverColor: "from-purple-600 to-purple-700",
    },
    {
      label: "Reports Generated",
      value: reportId ? "1" : "0",
      icon: FileText,
      color: "from-green-500 to-green-600",
      hoverColor: "from-green-600 to-green-700",
    },
    {
      label: "Active Template",
      value: selectedTemplate ? "1" : "0",
      icon: BookOpen,
      color: "from-orange-500 to-orange-600",
      hoverColor: "from-orange-600 to-orange-700",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative overflow-hidden">
      {/* Particle Field */}
      <ParticleField isVisible={!showWelcome} />

      {/* Royal Welcome Screen */}
      <AnimatePresence>
        {showWelcome && (
          <RoyalWelcome onComplete={() => setShowWelcome(false)} />
        )}
      </AnimatePresence>
      {/* Animated Background Elements */}
      <motion.div
        initial={{ opacity: 0, scale: 0 }}
        animate={{
          opacity: showWelcome ? 0 : 1,
          scale: showWelcome ? 0 : 1,
          x: [0, 100, 0],
          y: [0, -50, 0],
        }}
        transition={{
          opacity: { duration: 1, delay: 0.5 },
          scale: { duration: 1, delay: 0.5 },
          x: { duration: 20, repeat: Infinity, ease: "linear" },
          y: { duration: 20, repeat: Infinity, ease: "linear" },
        }}
        className="absolute top-20 left-10 w-32 h-32 bg-blue-200/20 rounded-full blur-xl"
      />
      <motion.div
        initial={{ opacity: 0, scale: 0 }}
        animate={{
          opacity: showWelcome ? 0 : 1,
          scale: showWelcome ? 0 : 1,
          x: [0, -80, 0],
          y: [0, 60, 0],
        }}
        transition={{
          opacity: { duration: 1, delay: 0.7 },
          scale: { duration: 1, delay: 0.7 },
          x: { duration: 25, repeat: Infinity, ease: "linear" },
          y: { duration: 25, repeat: Infinity, ease: "linear" },
        }}
        className="absolute top-40 right-20 w-40 h-40 bg-purple-200/20 rounded-full blur-xl"
      />
      <motion.div
        initial={{ opacity: 0, scale: 0 }}
        animate={{
          opacity: showWelcome ? 0 : 1,
          scale: showWelcome ? 0 : 1,
          x: [0, 60, 0],
          y: [0, -30, 0],
        }}
        transition={{
          opacity: { duration: 1, delay: 0.9 },
          scale: { duration: 1, delay: 0.9 },
          x: { duration: 30, repeat: Infinity, ease: "linear" },
          y: { duration: 30, repeat: Infinity, ease: "linear" },
        }}
        className="absolute bottom-20 left-1/4 w-24 h-24 bg-pink-200/20 rounded-full blur-xl"
      />

      {/* Header */}
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{
          y: showWelcome ? -100 : 0,
          opacity: showWelcome ? 0 : 1,
        }}
        transition={{
          duration: 0.8,
          delay: showWelcome ? 0 : 0.3,
          type: "spring",
          stiffness: 100,
        }}
        className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50"
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ x: -50, opacity: 0 }}
              animate={{
                x: showWelcome ? -50 : 0,
                opacity: showWelcome ? 0 : 1,
              }}
              transition={{
                duration: 0.6,
                delay: showWelcome ? 0 : 0.5,
              }}
              className="flex items-center space-x-3"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg"
              >
                <Sparkles className="h-6 w-6 text-white" />
              </motion.div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  AI Report Generator
                </h1>
                <p className="text-sm text-muted-foreground">
                  Intelligent document analysis & report creation
                </p>
              </div>
            </motion.div>
            <motion.div
              initial={{ x: 50, opacity: 0 }}
              animate={{
                x: showWelcome ? 50 : 0,
                opacity: showWelcome ? 0 : 1,
              }}
              transition={{
                duration: 0.6,
                delay: showWelcome ? 0 : 0.7,
              }}
              className="flex items-center space-x-2"
            >
              {selectedTemplate && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200 }}
                >
                  <HoverCard
                    hoverContent={
                      <div className="text-sm">
                        <p className="font-medium">Active Template</p>
                        <p className="text-gray-600">
                          {selectedTemplate.description}
                        </p>
                      </div>
                    }
                  >
                    <Badge
                      variant="secondary"
                      className="flex items-center space-x-1 cursor-pointer"
                    >
                      <LayoutTemplate className="h-3 w-3" />
                      <span>{selectedTemplate.name}</span>
                    </Badge>
                  </HoverCard>
                </motion.div>
              )}
              {user ? (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200 }}
                  className="flex items-center space-x-2"
                >
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleNewChat}
                    className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white border-0"
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    New Chat
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDeleteAllDocuments}
                    className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white border-0"
                    title="Delete all uploaded documents (templates preserved)"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete All
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRecoverCollection}
                    className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white border-0"
                    title="Recover corrupted collection"
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Recover
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleResetCollection}
                    className="bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white border-0"
                    title="Reset entire collection (preserves templates)"
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Reset
                  </Button>
                  <div className="flex items-center space-x-2">
                    {user.photoURL && (
                      <img
                        src={user.photoURL}
                        alt="Profile"
                        className="w-6 h-6 rounded-full border border-white shadow-sm"
                      />
                    )}
                    <Badge
                      variant="secondary"
                      className="flex items-center space-x-1"
                    >
                      <Users className="h-3 w-3" />
                      <span>
                        {user.displayName || user.email?.split("@")[0]}
                      </span>
                    </Badge>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleProfileClick}
                  >
                    <Settings className="h-4 w-4 mr-2" />
                    Profile
                  </Button>
                </motion.div>
              ) : (
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setShowAuth(true)}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white"
                >
                  <Users className="h-4 w-4 mr-2" />
                  Sign In
                </Button>
              )}
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <ParallaxSection speed={0.3} direction="up">
        <div className="container mx-auto px-6 py-6 pt-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{
              opacity: showWelcome ? 0 : 1,
              y: showWelcome ? 20 : 0,
            }}
            transition={{
              duration: 0.6,
              delay: showWelcome ? 0 : 0.9,
            }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
          >
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20, scale: 0.9 }}
                animate={{
                  opacity: showWelcome ? 0 : 1,
                  y: showWelcome ? 20 : 0,
                  scale: showWelcome ? 0.9 : 1,
                }}
                transition={{
                  duration: 0.5,
                  delay: showWelcome ? 0 : 1.1 + index * 0.1,
                  type: "spring",
                  stiffness: 100,
                }}
                whileHover={{
                  scale: 1.05,
                  y: -5,
                  transition: { duration: 0.2 },
                }}
                whileTap={{ scale: 0.95 }}
              >
                <HoverCard
                  hoverContent={
                    <div className="text-sm">
                      <p className="font-medium">{stat.label}</p>
                      <p className="text-gray-600">Click to view details</p>
                    </div>
                  }
                >
                  <Card className="border-0 shadow-sm bg-white/60 backdrop-blur-sm hover:shadow-lg transition-all duration-300 cursor-pointer group">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">
                            {stat.label}
                          </p>
                          <motion.p
                            animate={{ scale: [1, 1.1, 1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
                          >
                            {stat.value}
                          </motion.p>
                        </div>
                        <motion.div
                          whileHover={{ rotate: 360 }}
                          transition={{ duration: 0.5 }}
                          className={`p-2 bg-gradient-to-r ${stat.color} rounded-lg group-hover:shadow-lg`}
                        >
                          <stat.icon className="h-5 w-5 text-white" />
                        </motion.div>
                      </div>
                    </CardContent>
                  </Card>
                </HoverCard>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </ParallaxSection>

      {/* Main Content Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 50, scale: 0.95 }}
        animate={{
          opacity: showWelcome ? 0 : 1,
          y: showWelcome ? 50 : 0,
          scale: showWelcome ? 0.95 : 1,
        }}
        transition={{
          duration: 1,
          delay: showWelcome ? 0 : 1.5,
          type: "spring",
          stiffness: 100,
        }}
        className="container mx-auto px-6"
      >
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          <TabsList className="grid w-full grid-cols-4 bg-white/60 backdrop-blur-sm">
            <TabsTrigger value="upload" className="flex items-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>Upload</span>
            </TabsTrigger>
            <TabsTrigger
              value="templates"
              className="flex items-center space-x-2"
            >
              <LayoutTemplate className="h-4 w-4" />
              <span>Templates</span>
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center space-x-2">
              <MessageSquare className="h-4 w-4" />
              <span>AI Chat</span>
            </TabsTrigger>
            <TabsTrigger
              value="output"
              className="flex items-center space-x-2"
              disabled={!reportId}
            >
              <Eye className="h-4 w-4" />
              <span>Output</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FileUpload
                sessionId={sessionId}
                onUploadSuccess={handleUploadSuccess}
              />
              <Card className="border-0 shadow-sm bg-white/60 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Sparkles className="h-5 w-5 text-primary" />
                    <span>Quick Start Guide</span>
                  </CardTitle>
                  <CardDescription>
                    Get started with AI-powered report generation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <div className="p-1 bg-primary/10 rounded-full">
                        <Upload className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">Upload Documents</p>
                        <p className="text-sm text-muted-foreground">
                          PDF, DOCX, PPTX, XLSX, Images
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="p-1 bg-primary/10 rounded-full">
                        <LayoutTemplate className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">Select Template</p>
                        <p className="text-sm text-muted-foreground">
                          Choose from 6 professional templates
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="p-1 bg-primary/10 rounded-full">
                        <MessageSquare className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">Generate Report</p>
                        <p className="text-sm text-muted-foreground">
                          AI creates evidence-backed reports
                        </p>
                      </div>
                    </div>
                  </div>
                  <Button
                    onClick={() => setActiveTab("templates")}
                    className="w-full"
                    size="lg"
                  >
                    <LayoutTemplate className="h-4 w-4 mr-2" />
                    Browse Templates
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="templates" className="space-y-6">
            <EnhancedTemplateSelector
              onTemplateSelect={handleTemplateSelect}
              currentTemplate={selectedTemplate}
            />
          </TabsContent>

          <TabsContent value="chat" className="space-y-6">
            <EnhancedUnifiedChat
              setReportId={setReportId}
              setGenerateData={setGenerateData}
              selectedTemplate={selectedTemplate}
              user={user}
              chatTrigger={chatTrigger}
              // Chat state props
              messages={chatMessages}
              setMessages={setChatMessages}
              input={chatInput}
              setInput={setChatInput}
              loading={chatLoading}
              setLoading={setChatLoading}
              selectedCitation={chatSelectedCitation}
              setSelectedCitation={setChatSelectedCitation}
              aiThinking={chatAiThinking}
              setAiThinking={setChatAiThinking}
              showDocumentPreview={chatShowDocumentPreview}
              setShowDocumentPreview={setChatShowDocumentPreview}
              previewReportId={chatPreviewReportId}
              setPreviewReportId={setChatPreviewReportId}
              documentContext={chatDocumentContext}
              setDocumentContext={setChatDocumentContext}
              showSuccess={chatShowSuccess}
              setShowSuccess={setChatShowSuccess}
              layoutMode={chatLayoutMode}
              setLayoutMode={setChatLayoutMode}
              // Function to refresh template count
              refreshTemplateCount={refreshTemplateCount}
            />
          </TabsContent>

          <TabsContent value="output" className="space-y-6">
            {reportId && (
              <>
                <OutputPreview reportId={reportId} />
                <ApiDebugPanel
                  reportId={reportId}
                  generateResponse={generateData}
                />
              </>
            )}
          </TabsContent>
        </Tabs>
      </motion.div>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "rgba(255, 255, 255, 0.95)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.2)",
            borderRadius: "12px",
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
          },
          success: {
            iconTheme: {
              primary: "#10b981",
              secondary: "#fff",
            },
          },
          error: {
            iconTheme: {
              primary: "#ef4444",
              secondary: "#fff",
            },
          },
        }}
      />

      {/* Google Authentication Modal */}
      <GoogleAuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* Profile Modal */}
      <AnimatePresence>
        {showProfile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowProfile(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg p-6 max-w-md w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center space-x-4 mb-6">
                {user?.photoURL && (
                  <img
                    src={user.photoURL}
                    alt="Profile"
                    className="w-16 h-16 rounded-full border-2 border-gray-200"
                  />
                )}
                <div>
                  <h3 className="text-lg font-semibold">
                    {user?.displayName || "User"}
                  </h3>
                  <p className="text-gray-600">{user?.email}</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium mb-2">Account Information</h4>
                  <p className="text-sm text-gray-600">Email: {user?.email}</p>
                  <p className="text-sm text-gray-600">
                    Name: {user?.displayName || "Not set"}
                  </p>
                </div>

                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    onClick={() => setShowProfile(false)}
                    className="flex-1"
                  >
                    Close
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleLogout}
                    className="flex-1"
                  >
                    Logout
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
