"use client";
import React, { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Upload,
  FileText,
  Image,
  Video,
  Music,
  Archive,
  Presentation,
  Table,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  File,
  Trash2,
  Eye,
  Download,
} from "lucide-react";
import toast from "react-hot-toast";

const MultiFileUpload = ({ onUploadSuccess, onUploadError }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResults, setUploadResults] = useState(null);
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);

  // File type categories with icons and colors
  const fileCategories = {
    documents: {
      icon: FileText,
      color: "bg-blue-100 text-blue-800",
      label: "Documents",
    },
    presentations: {
      icon: Presentation,
      color: "bg-orange-100 text-orange-800",
      label: "Presentations",
    },
    spreadsheets: {
      icon: Table,
      color: "bg-green-100 text-green-800",
      label: "Spreadsheets",
    },
    images: {
      icon: Image,
      color: "bg-purple-100 text-purple-800",
      label: "Images",
    },
    videos: { icon: Video, color: "bg-red-100 text-red-800", label: "Videos" },
    audio: { icon: Music, color: "bg-pink-100 text-pink-800", label: "Audio" },
    archives: {
      icon: Archive,
      color: "bg-gray-100 text-gray-800",
      label: "Archives",
    },
    unknown: { icon: File, color: "bg-gray-100 text-gray-800", label: "Other" },
  };

  // Supported file types
  const supportedTypes = {
    documents: ["pdf", "doc", "docx", "txt", "rtf"],
    presentations: ["ppt", "pptx"],
    spreadsheets: ["xls", "xlsx", "csv"],
    images: ["png", "jpg", "jpeg", "gif", "bmp", "tiff"],
    videos: ["mp4", "avi", "mov", "mkv", "wmv", "flv"],
    audio: ["mp3", "wav", "m4a", "flac", "aac", "ogg"],
    archives: ["zip", "rar", "7z", "tar", "gz"],
  };

  const getFileCategory = (filename) => {
    const ext = filename.toLowerCase().split(".").pop();
    for (const [category, extensions] of Object.entries(supportedTypes)) {
      if (extensions.includes(ext)) {
        return category;
      }
    }
    return "unknown";
  };

  const getFileIcon = (category) => {
    const IconComponent = fileCategories[category]?.icon || File;
    return IconComponent;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const validateFile = (file) => {
    const maxSize = 100 * 1024 * 1024; // 100MB
    const ext = file.name.toLowerCase().split(".").pop();
    const allSupportedTypes = Object.values(supportedTypes).flat();

    if (file.size > maxSize) {
      return { valid: false, error: "File size exceeds 100MB limit" };
    }

    if (!allSupportedTypes.includes(ext)) {
      return { valid: false, error: `Unsupported file type: .${ext}` };
    }

    return { valid: true };
  };

  const handleFileSelect = useCallback((selectedFiles) => {
    const newFiles = Array.from(selectedFiles).map((file) => {
      const validation = validateFile(file);
      const category = getFileCategory(file.name);
      const IconComponent = getFileIcon(category);

      return {
        id: Math.random().toString(36).substr(2, 9),
        file,
        name: file.name,
        size: file.size,
        category,
        IconComponent,
        status: validation.valid ? "ready" : "error",
        error: validation.error,
        progress: 0,
      };
    });

    setFiles((prev) => [...prev, ...newFiles]);

    if (newFiles.some((f) => f.status === "error")) {
      toast.error("Some files were rejected due to validation errors");
    }
  }, []);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      e.currentTarget.classList.add("border-blue-500", "bg-blue-50");
    }
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      e.currentTarget.classList.remove("border-blue-500", "bg-blue-50");
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current = 0;
      e.currentTarget.classList.remove("border-blue-500", "bg-blue-50");

      const droppedFiles = e.dataTransfer.files;
      if (droppedFiles.length > 0) {
        handleFileSelect(droppedFiles);
      }
    },
    [handleFileSelect]
  );

  const removeFile = (fileId) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const clearAllFiles = () => {
    setFiles([]);
    setUploadResults(null);
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      toast.error("Please select files to upload");
      return;
    }

    const validFiles = files.filter((f) => f.status === "ready");
    if (validFiles.length === 0) {
      toast.error("No valid files to upload");
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      validFiles.forEach((fileObj) => {
        formData.append("files", fileObj.file);
      });

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 10;
        });
      }, 200);

      const response = await fetch(
        "http://localhost:8000/documents/upload-multiple",
        {
          method: "POST",
          body: formData,
        }
      );

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      setUploadResults(result);

      // Update file statuses
      setFiles((prev) =>
        prev.map((f) => {
          if (f.status === "ready") {
            const fileResult = result.summary.files.find(
              (rf) => rf.filename === f.name
            );
            return {
              ...f,
              status: fileResult?.status === "success" ? "success" : "error",
              error: fileResult?.error,
            };
          }
          return f;
        })
      );

      if (result.summary.successful_uploads > 0) {
        toast.success(
          `Successfully uploaded ${result.summary.successful_uploads} files!`
        );
        if (onUploadSuccess) {
          onUploadSuccess(result);
        }
      }

      if (result.summary.failed_uploads > 0) {
        toast.error(`${result.summary.failed_uploads} files failed to upload`);
        if (onUploadError) {
          onUploadError(result);
        }
      }
    } catch (error) {
      console.error("Upload error:", error);
      toast.error("Upload failed. Please try again.");
      setFiles((prev) =>
        prev.map((f) => ({
          ...f,
          status: f.status === "ready" ? "error" : f.status,
          error: f.status === "ready" ? "Upload failed" : f.error,
        }))
      );
      if (onUploadError) {
        onUploadError(error);
      }
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "ready":
        return <File className="h-4 w-4 text-gray-500" />;
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <File className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "ready":
        return "bg-gray-100 text-gray-800";
      case "success":
        return "bg-green-100 text-green-800";
      case "error":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Multi-File Upload
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center transition-colors duration-200 hover:border-gray-400"
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Drag & drop files here, or click to select
            </h3>
            <p className="text-gray-600 mb-4">
              Support for PDF, Word, Excel, PowerPoint, Images, Videos, Audio,
              and Archives
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Maximum 20 files, 100MB per file, 500MB total
            </p>
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="mb-4"
            >
              Select Files
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => handleFileSelect(e.target.files)}
              accept=".pdf,.doc,.docx,.txt,.rtf,.ppt,.pptx,.xls,.xlsx,.csv,.png,.jpg,.jpeg,.gif,.bmp,.tiff,.mp4,.avi,.mov,.mkv,.wmv,.flv,.mp3,.wav,.m4a,.flac,.aac,.ogg,.zip,.rar,.7z,.tar,.gz"
            />
          </div>
        </CardContent>
      </Card>

      {/* Upload Progress */}
      {uploading && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading files...</span>
                <span>{Math.round(uploadProgress)}%</span>
              </div>
              <Progress value={uploadProgress} className="w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="flex items-center gap-2">
                <File className="h-5 w-5" />
                Selected Files ({files.length})
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearAllFiles}
                  disabled={uploading}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
                <Button
                  onClick={uploadFiles}
                  disabled={
                    uploading ||
                    files.filter((f) => f.status === "ready").length === 0
                  }
                >
                  {uploading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Upload className="h-4 w-4 mr-2" />
                  )}
                  Upload Files
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <AnimatePresence>
                {files.map((fileObj) => {
                  const IconComponent = fileObj.IconComponent;
                  return (
                    <motion.div
                      key={fileObj.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <IconComponent className="h-8 w-8 text-gray-500" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {fileObj.name}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge
                              className={
                                fileCategories[fileObj.category]?.color
                              }
                            >
                              {fileCategories[fileObj.category]?.label}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              {formatFileSize(fileObj.size)}
                            </span>
                            <Badge className={getStatusColor(fileObj.status)}>
                              {getStatusIcon(fileObj.status)}
                              <span className="ml-1 capitalize">
                                {fileObj.status}
                              </span>
                            </Badge>
                          </div>
                          {fileObj.error && (
                            <p className="text-xs text-red-600 mt-1">
                              {fileObj.error}
                            </p>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(fileObj.id)}
                        disabled={uploading}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload Results */}
      {uploadResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Upload Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {uploadResults.summary.successful_uploads}
                </div>
                <div className="text-sm text-green-800">Successful</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {uploadResults.summary.failed_uploads}
                </div>
                <div className="text-sm text-red-800">Failed</div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {uploadResults.summary.document_count}
                </div>
                <div className="text-sm text-blue-800">Total Documents</div>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">File Details:</h4>
              {uploadResults.summary.files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded"
                >
                  <span className="text-sm">{file.filename}</span>
                  <Badge
                    className={
                      file.status === "success"
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }
                  >
                    {file.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MultiFileUpload;

