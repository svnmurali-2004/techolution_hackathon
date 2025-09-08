"use client";
import React, { useState, useEffect } from "react";

export default function TemplateEditor() {
  const [sections, setSections] = useState([]);
  const [newSection, setNewSection] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/templates")
      .then((res) => res.json())
      .then((data) => {
        if (data.length > 0) setSections(data[0].template);
      });
  }, []);

  const handleAdd = () => {
    if (!newSection.trim()) return;
    setSections([...sections, newSection.trim()]);
    setNewSection("");
  };

  const handleRemove = (idx) => {
    setSections(sections.filter((_, i) => i !== idx));
  };

  const handleMove = (idx, dir) => {
    const newSections = [...sections];
    const swapIdx = dir === "up" ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= newSections.length) return;
    [newSections[idx], newSections[swapIdx]] = [
      newSections[swapIdx],
      newSections[idx],
    ];
    setSections(newSections);
  };

  const handleSave = async () => {
    setMessage("");
    try {
      const res = await fetch("http://localhost:8000/templates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template: sections }),
      });
      const data = await res.json();
      if (data.status === "created") {
        setMessage("Template saved!");
      } else {
        setMessage("Error saving template.");
      }
    } catch {
      setMessage("Backend error.");
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-lg">
      <h2 className="font-bold text-xl mb-4 text-purple-700">
        Template Editor
      </h2>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={newSection}
          onChange={(e) => setNewSection(e.target.value)}
          placeholder="Add section..."
          className="px-3 py-2 border rounded w-full focus:outline-none focus:ring-2 focus:ring-purple-400"
        />
        <button
          className="bg-purple-500 text-white px-4 py-2 rounded-lg shadow hover:scale-105 transition-transform"
          onClick={handleAdd}
        >
          Add
        </button>
      </div>
      <ul className="mb-4">
        {sections.map((section, idx) => (
          <li key={idx} className="flex items-center gap-2 mb-2">
            <span className="flex-1 text-gray-800">{section}</span>
            <button
              className="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300"
              onClick={() => handleMove(idx, "up")}
            >
              ↑
            </button>
            <button
              className="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300"
              onClick={() => handleMove(idx, "down")}
            >
              ↓
            </button>
            <button
              className="text-xs px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600"
              onClick={() => handleRemove(idx)}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <button
        className="bg-gradient-to-r from-purple-500 to-purple-700 text-white px-6 py-2 rounded-lg shadow hover:scale-105 transition-transform"
        onClick={handleSave}
      >
        Save Template
      </button>
      {message && <div className="mt-4 text-sm text-gray-700">{message}</div>}
    </div>
  );
}
