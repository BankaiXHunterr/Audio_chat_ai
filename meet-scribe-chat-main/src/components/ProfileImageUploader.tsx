import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
  Upload, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  Camera,
  X
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface ProfileImageUploaderProps {
  currentAvatar?: string;
  userName: string;
  onAvatarUpdate: (avatarUrl: string) => void;
}

export function ProfileImageUploader({ 
  currentAvatar, 
  userName, 
  onAvatarUpdate 
}: ProfileImageUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('avatar', file);

      const token = localStorage.getItem('authToken');
      const response = await fetch('/api/user/avatar', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response.ok) {
        const data = await response.json();
        onAvatarUpdate(data.avatarUrl);
        toast({
          title: "Success",
          description: "Profile picture updated successfully",
        });
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      setError('Failed to upload profile picture');
      toast({
        title: "Error",
        description: "Failed to upload profile picture",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [onAvatarUpdate, toast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp', '.gif']
    },
    multiple: false,
    maxSize: 5 * 1024 * 1024, // 5MB
  });

  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative group">
        <Avatar className="h-24 w-24 border-4 border-primary/20 shadow-lg">
          <AvatarImage src={currentAvatar} alt={userName} />
          <AvatarFallback className="text-2xl bg-gradient-primary text-primary-foreground">
            {userName.split(' ').map(n => n[0]).join('')}
          </AvatarFallback>
        </Avatar>
        
        {isUploading && (
          <div className="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center">
            <Loader2 className="w-6 h-6 text-white animate-spin" />
          </div>
        )}
        
        <div
          {...getRootProps()}
          className={cn(
            "absolute inset-0 bg-black/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer flex items-center justify-center",
            isDragActive && "opacity-100"
          )}
        >
          <input {...getInputProps()} />
          <Camera className="w-6 h-6 text-white" />
        </div>
      </div>

      {uploadProgress > 0 && uploadProgress < 100 && (
        <div className="w-full max-w-xs space-y-2">
          <div className="flex justify-between text-sm">
            <span>Uploading...</span>
            <span>{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} className="w-full" />
        </div>
      )}

      {error && (
        <div className="flex items-center space-x-2 text-destructive text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      <div
        {...getRootProps()}
        className={cn(
          "cursor-pointer transition-colors",
          isDragActive && "scale-105"
        )}
      >
        <input {...getInputProps()} />
        <Button 
          variant="outline" 
          size="sm" 
          disabled={isUploading}
          className="hover:bg-primary/10"
        >
          <Upload className="w-4 h-4 mr-2" />
          {isUploading ? "Uploading..." : "Change Photo"}
        </Button>
      </div>

      <p className="text-xs text-muted-foreground text-center">
        Drag and drop or click to upload<br />
        Supports: JPEG, PNG, WebP, GIF (max 5MB)
      </p>
    </div>
  );
}