"use client";
import React, { useState } from "react";
import CitationPopup from "./CitationPopup";

export default function OutputPreview({ reportId }) {
  const [preview, setPreview] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [message, setMessage] = useState("");
  const [selectedCitation, setSelectedCitation] = useState(null);

  const fetchPreview = async () => {
    if (!reportId) return;
    try {
      const res = await fetch(
        `http://localhost:8000/reports/preview/${reportId}`
      );
      const data = await res.json();
      if (data.preview) {
        console.log("Preview data:", data.preview); // Debug logging

        // Clean up the data to ensure all expected fields exist and are in the correct format
        const cleanedPreview = {
          ...data.preview,
          sections: (data.preview.sections || []).map((section) => ({
            ...section,
            title: section.title || "Untitled Section",
            content: (section.content || []).map((contentItem) => ({
              ...contentItem,
              text: contentItem.text || "",
              citations: (contentItem.citations || []).map((citation) => ({
                ...citation,
                source_id: citation.source_id || "",
                page: citation.page || 1,
                timestamp: citation.timestamp || "",
                snippet:
                  typeof citation.snippet === "string" ? citation.snippet : "",
                document:
                  typeof citation.document === "string"
                    ? citation.document
                    : "",
              })),
            })),
          })),
        };

        setPreview(cleanedPreview);
      } else {
        setPreview(null);
      }
    } catch (error) {
      console.error("Error fetching preview:", error);
      setPreview(null);
    }
  };

  const handleExport = async (format) => {
    setExporting(true);
    setMessage("");
    try {
      const res = await fetch(
        `http://localhost:8000/reports/export?report_id=${reportId}&format=${format}`
      );
      const data = await res.json();
      if (data.file) {
        setMessage(`Exported ${format.toUpperCase()}!`);
      } else {
        setMessage("Export failed.");
      }
    } catch (error) {
      console.error("Error exporting:", error);
      setMessage("Backend error.");
    }
    setExporting(false);
  };

  const handleCitationClick = (citation) => {
    setSelectedCitation(citation);
  };

  const closeCitationPopup = () => {
    setSelectedCitation(null);
  };

  React.useEffect(() => {
    fetchPreview();
  }, [reportId]);

  // Function to parse text and highlight citations with enterprise-grade formatting
  const renderTextWithCitations = (text, citations) => {
    // Check if text is a string, otherwise return a message
    if (!text) return null;
    if (typeof text !== "string") return "[Content could not be displayed]";

    // Enhanced citation patterns to match various formats
    const citationRegex = /\[([\w\-\_\.]+):(\d+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;
    let citationCounter = 0;

    try {
      while ((match = citationRegex.exec(text)) !== null) {
        // Add text before the citation
        if (match.index > lastIndex) {
          parts.push(
            <span key={`text-${lastIndex}`}>
              {text.substring(lastIndex, match.index)}
            </span>
          );
        }

        // Find the matching citation from our citations array
        const sourceId = match[1];
        const page = parseInt(match[2], 10);
        const citation = citations.find(
          (c) => c.source_id === sourceId && c.page === page
        );

        citationCounter++;

        // Add the citation as a clickable element with enterprise styling
        parts.push(
          <button
            key={`citation-${match.index}`}
            onClick={() => (citation ? handleCitationClick(citation) : null)}
            className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded mx-1 text-xs font-medium hover:bg-blue-200 transition-colors border border-blue-300 shadow-sm hover:shadow-md cursor-pointer"
            title={
              citation
                ? `Click to view source: ${citation.source_id}`
                : "Citation not found"
            }
          >
            [{sourceId}:{page}]
          </button>
        );

        lastIndex = match.index + match[0].length;
      }

      // Add the remaining text
      if (lastIndex < text.length) {
        parts.push(<span key={`text-end`}>{text.substring(lastIndex)}</span>);
      }

      return parts.length > 0 ? parts : text;
    } catch (error) {
      console.error("Error rendering citations:", error);
      return String(text); // Convert to string as a fallback
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-lg">
      <h2 className="font-bold text-xl mb-4 text-indigo-700">Output Preview</h2>
      <div className="bg-gray-100 p-4 rounded mb-4 text-sm text-gray-800 min-h-[120px]">
        {preview && preview.sections ? (
          <div>
            <div className="mb-3 p-2 bg-yellow-100 rounded border border-yellow-300">
              <span className="font-medium">Report ID:</span>{" "}
              {preview.report_id}
            </div>

            {preview.sections.map((section, idx) => (
              <div key={idx} className="mb-6 border-l-4 border-indigo-400 pl-3">
                <div className="font-semibold text-indigo-600 mb-1">
                  Section {idx + 1}: {section.title}
                </div>
                {section.content &&
                  section.content.map((item, cidx) => (
                    <div key={cidx} className="mb-2">
                      <div className="whitespace-pre-wrap">
                        {item.text ? (
                          renderTextWithCitations(
                            item.text,
                            item.citations || []
                          )
                        ) : (
                          <span className="text-gray-500 italic">
                            No content available
                          </span>
                        )}
                      </div>

                      <details className="mt-3 text-xs">
                        <summary className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium">
                          View All Citations ({(item.citations || []).length})
                        </summary>
                        {item.citations && item.citations.length > 0 && (
                          <div className="ml-2 mt-2 p-2 bg-gray-200 rounded">
                            <ul className="list-none ml-0 space-y-2">
                              {item.citations.map((c, eidx) => (
                                <li
                                  key={eidx}
                                  className="p-2 bg-white rounded shadow-sm"
                                >
                                  <div className="flex justify-between mb-1">
                                    <span className="font-semibold text-indigo-700">
                                      [{c.source_id}:{c.page}]
                                    </span>
                                    <button
                                      onClick={() => handleCitationClick(c)}
                                      className="text-blue-600 hover:text-blue-800 font-medium text-xs"
                                    >
                                      View Full Reference
                                    </button>
                                  </div>
                                  <div className="text-gray-800 border-l-2 border-gray-400 pl-2 mt-1">
                                    {typeof (c.document || c.snippet || "") ===
                                    "string"
                                      ? `${(
                                          c.document ||
                                          c.snippet ||
                                          ""
                                        ).substring(0, 150)}${
                                          (c.document || c.snippet || "")
                                            .length > 150
                                            ? "..."
                                            : ""
                                        }`
                                      : "No text content available"}
                                  </div>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </details>
                    </div>
                  ))}
              </div>
            ))}
            {selectedCitation && (
              <CitationPopup
                citation={selectedCitation}
                onClose={closeCitationPopup}
              />
            )}
          </div>
        ) : reportId ? (
          <div className="text-center py-4">
            <div className="text-orange-500 font-medium">
              Loading preview data...
            </div>
            <div className="text-gray-500 text-xs mt-2">
              Report ID: {reportId}
            </div>
          </div>
        ) : (
          <span>Live preview will appear here.</span>
        )}
      </div>
      <div className="flex gap-2">
        <button
          className="bg-purple-500 text-white px-4 py-2 rounded-lg shadow hover:scale-105 transition-transform"
          onClick={() => handleExport("docx")}
          disabled={exporting || !reportId}
        >
          Export DOCX
        </button>
        <button
          className="bg-red-500 text-white px-4 py-2 rounded-lg shadow hover:scale-105 transition-transform"
          onClick={() => handleExport("pdf")}
          disabled={exporting || !reportId}
        >
          Export PDF
        </button>
        <button
          className="bg-green-500 text-white px-4 py-2 rounded-lg shadow hover:scale-105 transition-transform"
          onClick={() => fetchPreview()}
          disabled={!reportId}
        >
          Refresh Preview
        </button>
      </div>
      {message && <div className="mt-4 text-sm text-gray-700">{message}</div>}

      {/* Help text */}
      {preview && preview.sections && (
        <div className="mt-4 p-3 bg-blue-50 text-blue-800 text-xs rounded">
          <p className="font-medium">
            💡 Pro tip: Click on any citation reference like [doc_id:page] to
            see the source content.
          </p>
        </div>
      )}
    </div>
  );
}
