"use client";
import React, { useState, useEffect } from "react";

export default function TemplateSelector({
  onTemplateSelect,
  currentTemplate,
}) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("All");

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await fetch("http://localhost:8000/templates/list");
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error("Error fetching templates:", error);
    }
    setLoading(false);
  };

  const categories = [
    "All",
    ...new Set(templates.map((t) => t.category).filter(Boolean)),
  ];

  const filteredTemplates =
    selectedCategory === "All"
      ? templates
      : templates.filter((t) => t.category === selectedCategory);

  const handleTemplateClick = (template) => {
    if (onTemplateSelect) {
      onTemplateSelect(template);
    }
  };

  if (loading) {
    return (
      <div className="border rounded-lg p-6 bg-white shadow-lg">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          <span className="text-gray-600">Loading templates...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-6 bg-white shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-xl text-purple-700">
          📋 Available Templates
        </h3>
        <div className="text-sm text-gray-500">
          {templates.length} templates available
        </div>
      </div>

      {/* Category Filter */}
      <div className="mb-4">
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedCategory === category
                  ? "bg-purple-500 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTemplates.map((template) => (
          <div
            key={template.id}
            onClick={() => handleTemplateClick(template)}
            className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
              currentTemplate && currentTemplate.id === template.id
                ? "border-purple-500 bg-purple-50"
                : "border-gray-200 hover:border-purple-300"
            }`}
          >
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-semibold text-gray-800 text-sm">
                {template.name}
              </h4>
              {currentTemplate && currentTemplate.id === template.id && (
                <span className="text-xs bg-purple-500 text-white px-2 py-1 rounded-full">
                  Selected
                </span>
              )}
            </div>

            <p className="text-xs text-gray-600 mb-3">{template.description}</p>

            <div className="mb-3">
              <div className="text-xs font-medium text-gray-700 mb-1">
                Sections ({template.template.length}):
              </div>
              <div className="text-xs text-gray-600">
                {template.template.slice(0, 3).join(", ")}
                {template.template.length > 3 && "..."}
              </div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {template.category}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleTemplateClick(template);
                }}
                className="text-xs bg-purple-500 text-white px-3 py-1 rounded hover:bg-purple-600 transition-colors"
              >
                Use Template
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredTemplates.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">📝</div>
          <p>No templates found for "{selectedCategory}"</p>
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-semibold text-gray-700 mb-2">💡 Quick Actions</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <p>• Click any template to use it for report generation</p>
          <p>• Use the chat to create custom templates</p>
          <p>• Templates are automatically saved for future use</p>
        </div>
      </div>
    </div>
  );
}
