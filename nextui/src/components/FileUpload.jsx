"use client";
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  X,
  File,
  Image,
  FileSpreadsheet,
  Presentation,
  Sparkles,
  Video,
  Music,
} from "lucide-react";

export default function FileUpload({ sessionId, onUploadSuccess }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
    setMessage("");
    setUploadedFiles([]);
  };

  const getFileIcon = (file) => {
    const type = file.type;
    if (type.includes("pdf")) return FileText;
    if (type.includes("image")) return Image;
    if (type.includes("spreadsheet") || type.includes("excel"))
      return FileSpreadsheet;
    if (type.includes("presentation") || type.includes("powerpoint"))
      return Presentation;
    if (type.includes("video")) return Video;
    if (type.includes("audio")) return Music;
    return File;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleUpload = async () => {
    if (!files.length) {
      setMessage("Please select files to upload.");
      return;
    }
    setUploading(true);
    setMessage("");
    setUploadProgress(0);
    setUploadedFiles([]);

    for (let i = 0; i < files.length; i++) {
      const formData = new FormData();
      formData.append("file", files[i]);
      try {
        const res = await fetch("http://localhost:8000/documents/upload", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();

        if (data.status === "ingested") {
          setUploadedFiles((prev) => [
            ...prev,
            {
              name: files[i].name,
              status: "success",
              sourceId: data.source_id,
              documentCount: data.document_count,
            },
          ]);
          setMessage(`Successfully uploaded ${i + 1}/${files.length} files`);

          // Show success symbol and wait before redirecting
          if (onUploadSuccess) {
            setTimeout(() => {
              onUploadSuccess({
                fileName: files[i].name,
                sourceId: data.source_id,
                documentCount: data.document_count,
              });
            }, 2000); // 2 second delay to show success symbol
          }
        } else {
          setUploadedFiles((prev) => [
            ...prev,
            {
              name: files[i].name,
              status: "error",
              error: data.error || "Unknown error",
            },
          ]);
        }
      } catch (err) {
        setUploadedFiles((prev) => [
          ...prev,
          {
            name: files[i].name,
            status: "error",
            error: "Upload failed. Check backend connection.",
          },
        ]);
      }

      setUploadProgress(((i + 1) / files.length) * 100);
    }
    setUploading(false);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className="border-0 shadow-sm bg-white/60 backdrop-blur-sm">
        <CardHeader>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <CardTitle className="flex items-center space-x-2">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Upload className="h-5 w-5 text-primary" />
              </motion.div>
              <span>Document Upload</span>
              <motion.span
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-yellow-500"
              >
                ✨
              </motion.span>
            </CardTitle>
            <CardDescription>
              Upload PDF, DOCX, PPTX, XLSX, or image files for AI analysis
            </CardDescription>
          </motion.div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Input */}
          <div className="space-y-4">
            <div className="flex items-center justify-center w-full">
              <label
                htmlFor="file-upload"
                className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-primary/30 rounded-lg cursor-pointer bg-primary/5 hover:bg-primary/10 transition-colors"
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-8 h-8 mb-2 text-primary" />
                  <p className="mb-2 text-sm text-muted-foreground">
                    <span className="font-semibold">Click to upload</span> or
                    drag and drop
                  </p>
                  <p className="text-xs text-muted-foreground">
                    PDF, DOCX, PPTX, XLSX, Images, Videos, Audio (MAX. 50MB
                    each)
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    🎥 Videos will be transcribed automatically
                  </p>
                </div>
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.pptx,.xlsx,.jpg,.jpeg,.png,.gif,.bmp,.tiff,.mp4,.avi,.mov,.mkv,.wav,.mp3,.m4a,.flac"
                />
              </label>
            </div>

            {/* Selected Files */}
            {files.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">
                  Selected Files ({files.length})
                </h4>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {files.map((file, index) => {
                    const Icon = getFileIcon(file);
                    return (
                      <div
                        key={index}
                        className="flex items-center justify-between p-2 bg-muted/50 rounded-lg"
                      >
                        <div className="flex items-center space-x-2">
                          <Icon className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="text-sm font-medium">{file.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {formatFileSize(file.size)}
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(index)}
                          className="h-6 w-6 p-0"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Upload Progress */}
            {uploading && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Uploading files...</span>
                  <span>{Math.round(uploadProgress)}%</span>
                </div>
                <Progress value={uploadProgress} className="w-full" />
              </div>
            )}

            {/* Upload Button */}
            <Button
              onClick={handleUpload}
              disabled={uploading || files.length === 0}
              className="w-full"
              size="lg"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload{" "}
                  {files.length > 0
                    ? `${files.length} file${files.length > 1 ? "s" : ""}`
                    : "Files"}
                </>
              )}
            </Button>

            {/* Upload Results */}
            {uploadedFiles.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Upload Results</h4>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {uploadedFiles.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-muted/50 rounded-lg"
                    >
                      <div className="flex items-center space-x-2">
                        {file.status === "success" ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )}
                        <div>
                          <p className="text-sm font-medium">{file.name}</p>
                          {file.status === "success" ? (
                            <p className="text-xs text-green-600">
                              {file.documentCount} documents processed
                            </p>
                          ) : (
                            <p className="text-xs text-red-600">{file.error}</p>
                          )}
                        </div>
                      </div>
                      {file.status === "success" && (
                        <Badge variant="secondary" className="text-xs">
                          {file.sourceId}
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Status Message */}
            {message && (
              <div
                className={`p-3 rounded-lg text-sm flex items-center space-x-2 ${
                  message.includes("Error") || message.includes("failed")
                    ? "bg-red-50 text-red-700 border border-red-200"
                    : "bg-green-50 text-green-700 border border-green-200"
                }`}
              >
                {message.includes("Successfully") && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 500, damping: 15 }}
                    className="text-green-600"
                  >
                    ✓
                  </motion.div>
                )}
                <span>{message}</span>
                {message.includes("Successfully") && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="text-green-600"
                  >
                    🎉
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
