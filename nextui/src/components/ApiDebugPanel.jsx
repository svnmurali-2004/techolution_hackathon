"use client";
import React, { useState, useEffect } from "react";

export default function ApiDebugPanel({ reportId, generateResponse }) {
  const [previewResponse, setPreviewResponse] = useState(null);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (!reportId) return;

    // Fetch preview data for debugging
    const fetchPreviewData = async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/reports/preview/${reportId}`
        );
        const data = await res.json();
        setPreviewResponse(data);
      } catch (error) {
        setPreviewResponse({ error: "Failed to fetch preview data" });
      }
    };

    fetchPreviewData();
  }, [reportId]);

  // No longer needed as we're getting generateResponse directly as a prop

  const toggleVisibility = () => {
    setIsVisible(!isVisible);
  };

  if (!isVisible) {
    return (
      <div className="fixed bottom-5 right-5">
        <button
          onClick={toggleVisibility}
          className="bg-gray-700 text-white p-2 rounded-lg shadow"
        >
          Show Debug
        </button>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4 bg-gray-800 text-white shadow-lg mt-6 relative">
      <button
        onClick={toggleVisibility}
        className="absolute top-2 right-2 bg-gray-600 text-white p-1 rounded"
      >
        Hide
      </button>
      <h2 className="font-bold text-xl mb-2 text-yellow-400">
        API Debug Panel
      </h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold text-green-400 mb-2">
            Generate API Response:
          </h3>
          <div className="bg-gray-900 p-3 rounded overflow-auto max-h-60 text-green-300 font-mono text-xs">
            <pre>{JSON.stringify(generateResponse, null, 2)}</pre>
          </div>
        </div>
        <div>
          <h3 className="font-semibold text-blue-400 mb-2">
            Preview API Response:
          </h3>
          <div className="bg-gray-900 p-3 rounded overflow-auto max-h-60 text-blue-300 font-mono text-xs">
            <pre>{JSON.stringify(previewResponse, null, 2)}</pre>
          </div>
        </div>
      </div>
      <div className="mt-4">
        <h3 className="font-semibold text-purple-400">Current Report ID:</h3>
        <div className="bg-gray-900 p-3 rounded text-purple-300 font-mono text-xs">
          {reportId || "No report ID set"}
        </div>
      </div>
    </div>
  );
}
