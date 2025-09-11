import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  Upload, 
  File, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  FileAudio,
  FileVideo,
  X
} from "lucide-react";
import { cn } from "@/lib/utils";

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  uploadProgress: number;
  isUploading: boolean;
  isProcessing: boolean;
  error: string | null;
}

export function FileUploader({ 
  onFileSelect, 
  uploadProgress, 
  isUploading, 
  isProcessing,
  error 
}: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setSelectedFile(file);
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.aac'],
      'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    },
    multiple: false,
    maxSize: 500 * 1024 * 1024, // 500MB
  });

  const clearFile = () => {
    setSelectedFile(null);
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('audio/')) {
      return <FileAudio className="w-8 h-8 text-primary" />;
    } else if (file.type.startsWith('video/')) {
      return <FileVideo className="w-8 h-8 text-primary" />;
    }
    return <File className="w-8 h-8 text-primary" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (selectedFile && (isUploading || isProcessing || uploadProgress > 0)) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="p-8">
          <div className="text-center space-y-6">
            <div className="flex items-center justify-center space-x-4">
              {getFileIcon(selectedFile)}
              <div className="text-left">
                <h3 className="font-medium">{selectedFile.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>

            {uploadProgress > 0 && uploadProgress < 100 && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="w-full" />
              </div>
            )}

            {isProcessing && (
              <div className="space-y-4">
                <div className="flex items-center justify-center space-x-2">
                  <Loader2 className="w-5 h-5 animate-spin text-primary" />
                  <span className="text-lg font-medium">Processing your meeting...</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <CheckCircle className="w-4 h-4 text-success" />
                    <span>Upload complete</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span>Transcribing audio...</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <div className="w-4 h-4 rounded-full border-2 border-muted" />
                    <span>Generating summary...</span>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center justify-center space-x-2 text-destructive">
                <AlertCircle className="w-5 h-5" />
                <span>{error}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardContent className="p-8">
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-300",
            isDragActive 
              ? "border-primary bg-primary/5 scale-105" 
              : "border-muted hover:border-primary/50 hover:bg-muted/30"
          )}
        >
          <input {...getInputProps()} />
          
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              <Upload className={cn(
                "w-8 h-8 transition-colors",
                isDragActive ? "text-primary animate-bounce" : "text-primary/70"
              )} />
            </div>
            
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">
                {isDragActive ? "Drop your file here" : "Upload your meeting recording"}
              </h3>
              <p className="text-muted-foreground">
                Drag and drop your audio or video file, or click to browse
              </p>
            </div>

            <div className="flex flex-wrap justify-center gap-2 mt-4">
              <Badge variant="secondary">MP3</Badge>
              <Badge variant="secondary">MP4</Badge>
              <Badge variant="secondary">WAV</Badge>
              <Badge variant="secondary">MOV</Badge>
              <Badge variant="secondary">AVI</Badge>
            </div>

            <p className="text-xs text-muted-foreground">
              Maximum file size: 500MB
            </p>

            <Button variant="outline" size="lg" className="mt-4">
              <Upload className="w-4 h-4 mr-2" />
              Choose File
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}