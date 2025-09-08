"use client";
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
// ScrollArea not available, using div with overflow instead
import {
  X,
  Download,
  FileText,
  Eye,
  Share2,
  Copy,
  CheckCircle,
  Loader2,
  Sparkles,
  BookOpen,
  ExternalLink,
  Quote,
} from "lucide-react";
import toast from "react-hot-toast";
import CitationPopup from "./CitationPopup";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from "docx";
import { saveAs } from "file-saver";

export default function DocumentPreview({ reportId, isVisible, onClose }) {
  const [reportContent, setReportContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);

  // Debug logging
  useEffect(() => {
    console.log("🔍 DocumentPreview render state:", {
      reportId,
      isVisible,
      reportContent: !!reportContent,
      exporting,
      loading,
    });

    // Test if libraries are loaded
    console.log("📚 Library availability:", {
      jsPDF: typeof jsPDF !== "undefined",
      Document: typeof Document !== "undefined",
      Packer: typeof Packer !== "undefined",
      saveAs: typeof saveAs !== "undefined",
    });
  }, [reportId, isVisible, reportContent, exporting, loading]);

  // Helper function to parse and replace citation patterns in text
  const parseTextWithCitations = (text, citations) => {
    if (!text) return { cleanText: "", citationMap: {} };

    // Pattern to match citations like [uploaded_document_abc123:1]
    const citationPattern = /\[([^\]]+):(\d+)\]/g;
    const citationMap = {};
    let citationIndex = 1;

    // Replace citation patterns with numbered citations
    const cleanText = text.replace(citationPattern, (match, sourceId, page) => {
      const citationKey = `${sourceId}:${page}`;
      if (!citationMap[citationKey]) {
        citationMap[citationKey] = {
          number: citationIndex++,
          sourceId,
          page: parseInt(page),
          originalMatch: match,
        };
      }
      return `[${citationMap[citationKey].number}]`;
    });

    return { cleanText, citationMap };
  };

  // Component to render text with clickable citations
  const TextWithClickableCitations = ({
    text,
    citationMap,
    originalCitations,
  }) => {
    if (!text) return null;

    // Convert to string if it's not already
    const textStr = typeof text === "string" ? text : String(text);

    // Split text by citation patterns and render each part
    const parts = textStr.split(/(\[\d+\])/g);

    return (
      <span>
        {parts.map((part, index) => {
          // Check if this part is a citation
          const citationMatch = part.match(/\[(\d+)\]/);
          if (citationMatch) {
            const citationNumber = parseInt(citationMatch[1]);
            const citationInfo = Object.values(citationMap).find(
              (c) => c.number === citationNumber
            );

            if (citationInfo) {
              return (
                <button
                  key={index}
                  onClick={() => {
                    // Find the original citation data to get the snippet
                    const originalCitation = originalCitations?.find(
                      (c) =>
                        c.source_id === citationInfo.sourceId &&
                        c.page === citationInfo.page
                    );

                    setSelectedCitation({
                      source_id: citationInfo.sourceId,
                      page: citationInfo.page,
                      document: citationInfo.sourceId,
                      snippet:
                        originalCitation?.snippet ||
                        originalCitation?.content ||
                        "Content not available",
                    });
                  }}
                  className="inline text-blue-600 hover:text-blue-800 hover:underline cursor-pointer font-medium mx-0.5"
                  title="Click to view citation details"
                >
                  {part}
                </button>
              );
            }
          }

          // Regular text
          return <span key={index}>{part}</span>;
        })}
      </span>
    );
  };

  useEffect(() => {
    if (reportId && isVisible) {
      if (reportId === "demo-report") {
        // Show demo content
        setReportContent({
          preview: {
            sections: [
              {
                title: "Demo Report",
                content: [
                  {
                    text: "This is a demo of the dual-pane layout. When you generate a real report, it will appear here with actual content from your documents.",
                    citations: [],
                  },
                ],
              },
            ],
          },
        });
        setLoading(false);
      } else {
        fetchReportContent();
      }
    }
  }, [reportId, isVisible]);

  const fetchReportContent = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/reports/preview/${reportId}`
      );
      if (response.ok) {
        const data = await response.json();
        setReportContent(data);
      } else {
        toast.error("Failed to load report content");
      }
    } catch (error) {
      console.error("Error fetching report:", error);
      toast.error("Error loading report content");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    console.log("🔄 Export button clicked:", format);
    console.log("📊 Report content available:", !!reportContent);
    console.log("📊 Exporting state:", exporting);

    if (!reportContent) {
      toast.error("No report content available to export");
      return;
    }

    setExporting(true);
    try {
      if (format === "pdf") {
        console.log("📄 Starting PDF export...");
        await exportToPDF();
      } else if (format === "docx") {
        console.log("📝 Starting DOCX export...");
        await exportToDOCX();
      } else {
        toast.error("Unsupported export format");
      }
    } catch (error) {
      console.error("Export error:", error);
      toast.error("Export failed. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  const exportToPDF = async () => {
    try {
      // Create a new PDF document
      const pdf = new jsPDF("p", "mm", "a4");
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      let yPosition = 20;
      const margin = 20;
      const lineHeight = 7;

      // Add title
      pdf.setFontSize(20);
      pdf.setFont(undefined, "bold");
      pdf.text("AI Generated Report", margin, yPosition);
      yPosition += 15;

      // Add report ID
      pdf.setFontSize(12);
      pdf.setFont(undefined, "normal");
      pdf.text(`Report ID: ${reportId}`, margin, yPosition);
      yPosition += 10;

      // Add generation date
      pdf.text(
        `Generated on: ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}`,
        margin,
        yPosition
      );
      yPosition += 15;

      // Process each section
      reportContent.preview?.sections?.forEach((section, sectionIndex) => {
        // Check if we need a new page
        if (yPosition > pageHeight - 40) {
          pdf.addPage();
          yPosition = 20;
        }

        // Add section title
        pdf.setFontSize(16);
        pdf.setFont(undefined, "bold");
        const sectionTitle = section.title;
        pdf.text(sectionTitle, margin, yPosition);
        yPosition += 12;

        // Add section content
        pdf.setFontSize(11);
        pdf.setFont(undefined, "normal");

        section.content?.forEach((contentItem) => {
          // Clean text and remove citations for PDF
          const cleanText = contentItem.text.replace(
            /\[([^\]]+):(\d+)\]/g,
            "[$1]"
          );
          const lines = pdf.splitTextToSize(cleanText, pageWidth - 2 * margin);

          lines.forEach((line) => {
            if (yPosition > pageHeight - 20) {
              pdf.addPage();
              yPosition = 20;
            }
            pdf.text(line, margin, yPosition);
            yPosition += lineHeight;
          });

          // Add citations if any
          if (contentItem.citations && contentItem.citations.length > 0) {
            yPosition += 5;
            pdf.setFont(undefined, "italic");
            pdf.text("Citations:", margin, yPosition);
            yPosition += lineHeight;

            contentItem.citations.forEach((citation) => {
              if (yPosition > pageHeight - 20) {
                pdf.addPage();
                yPosition = 20;
              }
              const citationText = `• ${citation.source_id}, Page ${
                citation.page
              }: ${citation.snippet?.substring(0, 80)}...`;
              const citationLines = pdf.splitTextToSize(
                citationText,
                pageWidth - 2 * margin - 10
              );
              citationLines.forEach((line) => {
                if (yPosition > pageHeight - 20) {
                  pdf.addPage();
                  yPosition = 20;
                }
                pdf.text(line, margin + 10, yPosition);
                yPosition += lineHeight;
              });
            });
            pdf.setFont(undefined, "normal");
          }

          yPosition += 5; // Space between content items
        });

        yPosition += 10; // Space between sections
      });

      // Save the PDF
      pdf.save(`report_${reportId}.pdf`);
      toast.success("PDF exported successfully! 🎉");
    } catch (error) {
      console.error("PDF export error:", error);
      throw error;
    }
  };

  const exportToDOCX = async () => {
    try {
      const children = [];

      // Add title
      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text: "AI Generated Report",
              bold: true,
              size: 32,
            }),
          ],
          heading: HeadingLevel.TITLE,
        })
      );

      // Add report metadata
      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text: `Report ID: ${reportId}`,
              size: 20,
            }),
          ],
        })
      );

      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text: `Generated on: ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}`,
              size: 20,
            }),
          ],
        })
      );

      children.push(new Paragraph({ text: "" })); // Empty line

      // Process each section
      reportContent.preview?.sections?.forEach((section) => {
        // Add section title
        children.push(
          new Paragraph({
            children: [
              new TextRun({
                text: section.title,
                bold: true,
                size: 24,
              }),
            ],
            heading: HeadingLevel.HEADING_1,
          })
        );

        // Add section content
        section.content?.forEach((contentItem) => {
          // Clean text and replace citations with numbered references
          const cleanText = contentItem.text.replace(
            /\[([^\]]+):(\d+)\]/g,
            (match, sourceId, page) => {
              return `[${sourceId}]`;
            }
          );

          children.push(
            new Paragraph({
              children: [
                new TextRun({
                  text: cleanText,
                  size: 22,
                }),
              ],
            })
          );

          // Add citations if any
          if (contentItem.citations && contentItem.citations.length > 0) {
            children.push(
              new Paragraph({
                children: [
                  new TextRun({
                    text: "Citations:",
                    bold: true,
                    size: 20,
                  }),
                ],
              })
            );

            contentItem.citations.forEach((citation) => {
              children.push(
                new Paragraph({
                  children: [
                    new TextRun({
                      text: `• ${citation.source_id}, Page ${
                        citation.page
                      }: ${citation.snippet?.substring(0, 100)}...`,
                      size: 20,
                    }),
                  ],
                })
              );
            });
          }

          children.push(new Paragraph({ text: "" })); // Empty line
        });
      });

      // Create document
      const doc = new Document({
        sections: [
          {
            properties: {},
            children: children,
          },
        ],
      });

      // Generate and save the document
      const buffer = await Packer.toBuffer(doc);
      const blob = new Blob([buffer], {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      });

      saveAs(blob, `report_${reportId}.docx`);
      toast.success("DOCX exported successfully! 🎉");
    } catch (error) {
      console.error("DOCX export error:", error);
      throw error;
    }
  };

  const handleCopyContent = async () => {
    if (reportContent?.preview) {
      try {
        const textContent = JSON.stringify(reportContent.preview, null, 2);
        await navigator.clipboard.writeText(textContent);
        setCopied(true);
        toast.success("Report content copied to clipboard! 📋");
        setTimeout(() => setCopied(false), 2000);
      } catch (error) {
        toast.error("Failed to copy content");
      }
    }
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: "AI Generated Report",
        text: "Check out this AI-generated report!",
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied to clipboard! 🔗");
    }
  };

  return (
    <>
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ x: "100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="w-full h-full bg-white shadow-2xl border-l border-gray-200 relative z-50"
            style={{ zIndex: 50 }}
          >
            <div className="h-full flex flex-col">
              {/* Header */}
              <div className="flex-shrink-0 flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50">
                <div className="flex items-center space-x-4">
                  <motion.div
                    animate={{ rotate: [0, 10, -10, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center"
                  >
                    <BookOpen className="h-6 w-6 text-white" />
                  </motion.div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">
                      Document Preview
                    </h2>
                    <p className="text-sm text-gray-600">
                      AI-Generated Report with Citations
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <Badge
                    variant="secondary"
                    className="bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 border-green-200"
                  >
                    <Sparkles className="h-3 w-3 mr-1" />
                    AI Generated
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    className="hover:bg-gray-100 rounded-full w-8 h-8 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Action Bar */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100 relative z-10">
                <div className="flex items-center space-x-3">
                  {/* Test button to check if buttons work at all */}
                  <button
                    onClick={() => {
                      console.log("🧪 Test button clicked!");
                      toast.success("Test button works!");
                    }}
                    className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600 relative z-[60]"
                    style={{ zIndex: 60 }}
                  >
                    Test
                  </button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      console.log("🔵 PDF button clicked");
                      handleExport("pdf");
                    }}
                    disabled={exporting || !reportContent}
                    className="hover:bg-blue-50 hover:border-blue-300 transition-all duration-200 cursor-pointer relative z-[60]"
                    style={{ pointerEvents: "auto", zIndex: 60 }}
                  >
                    {exporting ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Download className="h-4 w-4 mr-2" />
                    )}
                    Export PDF
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      console.log("🟢 DOCX button clicked");
                      handleExport("docx");
                    }}
                    disabled={exporting || !reportContent}
                    className="hover:bg-green-50 hover:border-green-300 transition-all duration-200 cursor-pointer relative z-[60]"
                    style={{ pointerEvents: "auto", zIndex: 60 }}
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    Export Word
                  </Button>
                </div>
                <div className="flex items-center space-x-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopyContent}
                    className="hover:bg-gray-100 transition-all duration-200"
                  >
                    {copied ? (
                      <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4 mr-2" />
                    )}
                    Copy
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleShare}
                    className="hover:bg-gray-100 transition-all duration-200"
                  >
                    <Share2 className="h-4 w-4 mr-2" />
                    Share
                  </Button>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-hidden">
                <div className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                  <div className="p-6">
                    {loading ? (
                      <div className="flex items-center justify-center h-64">
                        <div className="text-center">
                          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
                          <p className="text-gray-500">
                            Loading report content...
                          </p>
                        </div>
                      </div>
                    ) : reportContent ? (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="space-y-6"
                      >
                        {/* Report Header */}
                        <div className="text-center border-b border-gray-200 pb-8 mb-8">
                          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-8">
                            <h1 className="text-3xl font-bold text-gray-900 mb-3">
                              AI-Generated Report
                            </h1>
                            <p className="text-gray-600 mb-4">
                              Generated on {new Date().toLocaleDateString()} at{" "}
                              {new Date().toLocaleTimeString()}
                            </p>
                            <div className="flex items-center justify-center space-x-4">
                              <Badge
                                variant="outline"
                                className="bg-white border-blue-200 text-blue-800"
                              >
                                Report ID: {reportId}
                              </Badge>
                              <Badge
                                variant="secondary"
                                className="bg-green-100 text-green-800"
                              >
                                <Sparkles className="h-3 w-3 mr-1" />
                                AI Powered
                              </Badge>
                            </div>
                          </div>
                        </div>

                        {/* Report Sections */}
                        {reportContent.preview?.sections?.map(
                          (section, index) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ duration: 0.5, delay: index * 0.1 }}
                              className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm hover:shadow-lg transition-all duration-300"
                            >
                              <div className="flex items-center mb-6">
                                <div className="w-3 h-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mr-4"></div>
                                <h2 className="text-2xl font-bold text-gray-900">
                                  {section.title}
                                </h2>
                              </div>

                              <div className="space-y-6">
                                {section.content?.map(
                                  (content, contentIndex) => (
                                    <div
                                      key={contentIndex}
                                      className="relative"
                                    >
                                      <div className="bg-gray-50 rounded-lg p-6 border-l-4 border-blue-500">
                                        <div className="text-gray-800 leading-relaxed text-base mb-4 prose prose-gray max-w-none">
                                          {(() => {
                                            const { cleanText, citationMap } =
                                              parseTextWithCitations(
                                                content.text,
                                                content.citations
                                              );

                                            return (
                                              <div>
                                                <ReactMarkdown
                                                  remarkPlugins={[remarkGfm]}
                                                  components={{
                                                    h1: ({ children }) => (
                                                      <h1 className="text-2xl font-bold text-gray-900 mb-4">
                                                        {children}
                                                      </h1>
                                                    ),
                                                    h2: ({ children }) => (
                                                      <h2 className="text-xl font-semibold text-gray-900 mb-3">
                                                        {children}
                                                      </h2>
                                                    ),
                                                    h3: ({ children }) => (
                                                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                                                        {children}
                                                      </h3>
                                                    ),
                                                    p: ({ children }) => (
                                                      <p className="mb-4 text-gray-800">
                                                        <TextWithClickableCitations
                                                          text={children}
                                                          citationMap={
                                                            citationMap
                                                          }
                                                          originalCitations={
                                                            content.citations
                                                          }
                                                        />
                                                      </p>
                                                    ),
                                                    ul: ({ children }) => (
                                                      <ul className="list-disc list-inside mb-4 space-y-1">
                                                        {children}
                                                      </ul>
                                                    ),
                                                    ol: ({ children }) => (
                                                      <ol className="list-decimal list-inside mb-4 space-y-1">
                                                        {children}
                                                      </ol>
                                                    ),
                                                    li: ({ children }) => (
                                                      <li className="text-gray-800">
                                                        <TextWithClickableCitations
                                                          text={children}
                                                          citationMap={
                                                            citationMap
                                                          }
                                                          originalCitations={
                                                            content.citations
                                                          }
                                                        />
                                                      </li>
                                                    ),
                                                    strong: ({ children }) => (
                                                      <strong className="font-semibold text-gray-900">
                                                        {children}
                                                      </strong>
                                                    ),
                                                    em: ({ children }) => (
                                                      <em className="italic text-gray-700">
                                                        {children}
                                                      </em>
                                                    ),
                                                    code: ({ children }) => (
                                                      <code className="bg-gray-200 px-1 py-0.5 rounded text-sm font-mono">
                                                        {children}
                                                      </code>
                                                    ),
                                                    pre: ({ children }) => (
                                                      <pre className="bg-gray-200 p-3 rounded-lg overflow-x-auto mb-4">
                                                        {children}
                                                      </pre>
                                                    ),
                                                    blockquote: ({
                                                      children,
                                                    }) => (
                                                      <blockquote className="border-l-4 border-blue-300 pl-4 italic text-gray-700 mb-4">
                                                        <TextWithClickableCitations
                                                          text={children}
                                                          citationMap={
                                                            citationMap
                                                          }
                                                          originalCitations={
                                                            content.citations
                                                          }
                                                        />
                                                      </blockquote>
                                                    ),
                                                    table: ({ children }) => (
                                                      <table className="w-full border-collapse border border-gray-300 mb-4">
                                                        {children}
                                                      </table>
                                                    ),
                                                    th: ({ children }) => (
                                                      <th className="border border-gray-300 px-3 py-2 bg-gray-100 font-semibold text-left">
                                                        {children}
                                                      </th>
                                                    ),
                                                    td: ({ children }) => (
                                                      <td className="border border-gray-300 px-3 py-2">
                                                        {children}
                                                      </td>
                                                    ),
                                                  }}
                                                >
                                                  {cleanText}
                                                </ReactMarkdown>
                                              </div>
                                            );
                                          })()}
                                        </div>
                                      </div>
                                    </div>
                                  )
                                )}
                              </div>
                            </motion.div>
                          )
                        ) || (
                          <div className="text-center py-12">
                            <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                            <p className="text-gray-500">
                              No report content available
                            </p>
                          </div>
                        )}
                      </motion.div>
                    ) : (
                      <div className="text-center py-12">
                        <Eye className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                        <p className="text-gray-500">No report to preview</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Citation Popup */}
      {selectedCitation && (
        <CitationPopup
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </>
  );
}
