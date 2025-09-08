"use client";
import React, { useState } from "react";

export default function AIChatBox({ setReportId, setGenerateData }) {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setResponse("");
    try {
      const res = await fetch("http://localhost:8000/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sections: ["Executive Summary", "Key Findings", "Recommendations"],
          query: input,
        }),
      });
      const data = await res.json();

      // Save the response to debug panel
      if (setGenerateData) {
        setGenerateData(data);
      }

      if (data.report_id) {
        setResponse("Report generated successfully! See preview below.");
        setReportId(data.report_id);
      } else if (data.error) {
        setResponse("Error: " + data.error);
      } else {
        setResponse("Error: " + (data.message || "Unknown error"));
      }
    } catch (error) {
      console.error("API Error:", error);
      setResponse("Backend error.");
      if (setGenerateData) {
        setGenerateData({ error: "API call failed" });
      }
    }
    setLoading(false);
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-lg flex flex-col items-center">
      <h2 className="font-bold text-xl mb-4 text-green-700">AI Chat Box</h2>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Refine your template or report..."
        className="w-full mb-4 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-green-400"
      />
      <button
        className="bg-gradient-to-r from-green-500 to-green-700 text-white px-6 py-2 rounded-lg shadow hover:scale-105 transition-transform disabled:opacity-50"
        onClick={handleSend}
        disabled={loading}
      >
        {loading ? "Sending..." : "Send"}
      </button>
      {response && <div className="mt-4 text-sm text-gray-700">{response}</div>}
    </div>
  );
}
