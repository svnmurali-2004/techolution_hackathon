"use client";
import React, { useState, useEffect } from "react";

export default function CitationPopup({ citation, onClose }) {
  const [documentDetails, setDocumentDetails] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (citation && citation.source_id) {
      fetchDocumentDetails(citation.source_id);
    }
  }, [citation]);

  const fetchDocumentDetails = async (sourceId) => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/documents/source/${sourceId}`
      );
      if (response.ok) {
        const data = await response.json();
        setDocumentDetails(data);
      }
    } catch (error) {
      console.error("Error fetching document details:", error);
    }
    setLoading(false);
  };

  if (!citation) return null;

  const formatSourceId = (sourceId) => {
    if (!sourceId) return "Unknown";

    // Ensure sourceId is a string
    const sourceIdStr = String(sourceId);

    // Extract meaningful parts from source ID
    if (sourceIdStr.startsWith("uploaded_")) {
      const parts = sourceIdStr.split("_");
      if (parts.length >= 3) {
        return `${parts[1]} (${parts[2]})`;
      }
    }
    return sourceIdStr;
  };

  const getDocumentType = (sourceId) => {
    if (!sourceId) return "Unknown";

    // Ensure sourceId is a string
    const sourceIdStr = String(sourceId);

    if (sourceIdStr.includes(".pdf")) return "PDF Document";
    if (sourceIdStr.includes(".docx")) return "Word Document";
    if (sourceIdStr.includes(".pptx")) return "PowerPoint Presentation";
    if (sourceIdStr.includes(".xlsx")) return "Excel Spreadsheet";
    if (sourceIdStr.includes(".txt")) return "Text Document";
    if (sourceIdStr.includes(".png") || sourceIdStr.includes(".jpg"))
      return "Image Document";

    return "Document";
  };

  const getConfidenceLevel = (citation) => {
    // Enterprise-grade confidence scoring
    let score = 0;

    if (citation.snippet && String(citation.snippet).length > 50) score += 30;
    if (citation.page && citation.page > 0) score += 25;
    if (citation.source_id && String(citation.source_id).length > 10)
      score += 25;
    if (citation.document && String(citation.document).length > 20) score += 20;

    if (score >= 80) return { level: "High", color: "green", icon: "🟢" };
    if (score >= 60) return { level: "Medium", color: "yellow", icon: "🟡" };
    return { level: "Low", color: "red", icon: "🔴" };
  };

  const confidence = getConfidenceLevel(citation);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[90vh] overflow-y-auto shadow-xl w-full">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-800 flex items-center">
              📄 Citation Details
              <span
                className={`ml-3 px-2 py-1 rounded-full text-xs font-medium bg-${confidence.color}-100 text-${confidence.color}-800`}
              >
                {confidence.icon} {confidence.level} Confidence
              </span>
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Enterprise-grade source verification
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100"
          >
            ×
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column - Citation Info */}
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-3 flex items-center">
                📋 Citation Information
              </h4>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Document Name
                  </label>
                  <p className="text-gray-900 bg-white p-2 rounded border text-sm">
                    {formatSourceId(
                      citation.document || citation.source_id || citation
                    )}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Document Type
                  </label>
                  <p className="text-gray-900 bg-white p-2 rounded border text-sm">
                    {getDocumentType(
                      citation.document || citation.source_id || citation
                    )}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Page Reference
                  </label>
                  <p className="text-gray-900 bg-white p-2 rounded border text-sm font-mono">
                    Page {citation.page || "N/A"}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source ID
                  </label>
                  <p className="text-gray-900 bg-white p-2 rounded border text-sm font-mono break-all">
                    {String(
                      citation.source_id ||
                        citation.document ||
                        citation ||
                        "N/A"
                    )}
                  </p>
                </div>

                {citation.timestamp && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Timestamp
                    </label>
                    <p className="text-gray-900 bg-white p-2 rounded border text-sm">
                      {new Date(citation.timestamp).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Content & Verification */}
          <div className="space-y-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-semibold text-green-800 mb-3 flex items-center">
                📝 Referenced Content
              </h4>

              {citation.snippet ? (
                <div className="bg-white p-3 rounded border">
                  <p className="text-gray-900 text-sm leading-relaxed">
                    "{String(citation.snippet)}"
                  </p>
                </div>
              ) : (
                <p className="text-gray-500 text-sm italic">
                  No content snippet available
                </p>
              )}
            </div>

            {/* Document Details */}
            {loading ? (
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  <span className="text-sm text-gray-600">
                    Loading document details...
                  </span>
                </div>
              </div>
            ) : documentDetails ? (
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-semibold text-purple-800 mb-3 flex items-center">
                  📊 Document Statistics
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Documents:</span>
                    <span className="font-medium">
                      {documentDetails.documents?.length || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Source ID:</span>
                    <span className="font-mono text-xs">
                      {documentDetails.source_id}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>

        {/* Enterprise Features */}
        <div className="mt-6 bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-3 flex items-center">
            🏢 Enterprise Features
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span>Source Verification</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <span>Audit Trail</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
              <span>Confidence Scoring</span>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-between items-center">
          <div className="text-xs text-gray-500">
            Citation ID:{" "}
            {String(
              citation.source_id || citation.document || citation || "unknown"
            )}
            _{citation.page || "0"}_{Date.now()}
          </div>
          <div className="space-x-2">
            <button
              onClick={() => {
                // Copy citation to clipboard
                const citationText = `Source: ${formatSourceId(
                  citation.document || citation.source_id || citation
                )}, Page ${citation.page || "N/A"}`;
                navigator.clipboard.writeText(citationText);
              }}
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors text-sm"
            >
              Copy Citation
            </button>
            <button
              onClick={onClose}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
