import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Navigation } from "@/components/Navigation";
import { FileUploader } from "@/components/FileUploader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon, ArrowLeft } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { Link } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { apiService } from "@/services/apiService";
import { EmailChipInput } from "@/components/EmailChipInput";

export default function Upload() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [meetingTitle, setMeetingTitle] = useState("");
  const [meetingDate, setMeetingDate] = useState<Date>();
  const [participants, setParticipants] = useState<string[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
    // Auto-generate title based on filename if empty
    if (!meetingTitle) {
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "");
      setMeetingTitle(nameWithoutExt.replace(/[_-]/g, " "));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile || !meetingTitle) {
      setError("Please select a file and provide a meeting title.");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // Convert File to Blob for API service
      const recordingBlob = new Blob([selectedFile], { type: selectedFile.type });
      
      // Prepare meeting data
      const meetingData = {
        title: meetingTitle,
        date: meetingDate ? meetingDate.toISOString() : new Date().toISOString(),
        participants: participants,
        recordingBlob: recordingBlob
      };

      // Simulate upload progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Submit to backend for processing
      const result = await apiService.processMeeting(meetingData);
      
      // Complete progress
      clearInterval(progressInterval);
      setUploadProgress(100);
      setIsUploading(false);
      setIsProcessing(true);

      toast({
        title: "Meeting Uploaded Successfully!",
        description: `"${meetingTitle}" is being processed. You'll see it in your dashboard shortly.`,
      });

      // Navigate to dashboard after a short delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
      
    } catch (error) {
      console.error('Upload error:', error);
      setError(error instanceof Error ? error.message : "Failed to upload and process the file. Please try again.");
      setIsUploading(false);
      setIsProcessing(false);
      setUploadProgress(0);
      
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload the meeting. Please try again.",
        variant: "destructive"
      });
    }
  };

  const canSubmit = selectedFile && meetingTitle && !isUploading && !isProcessing;

  return (
    <div className="min-h-screen bg-background pb-20">
      <Navigation />
      
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Button asChild variant="ghost" size="icon">
              <Link to="/dashboard">
                <ArrowLeft className="w-4 h-4" />
              </Link>
            </Button>
            <div>
              <h1 className="text-3xl font-bold">Upload Meeting</h1>
              <p className="text-muted-foreground">
                Upload your audio or video file to generate AI-powered summaries
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-8">
          {/* File Upload */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Select Recording</h2>
            <FileUploader
              onFileSelect={handleFileSelect}
              uploadProgress={uploadProgress}
              isUploading={isUploading}
              isProcessing={isProcessing}
              error={error}
            />
          </div>

          {/* Meeting Details Form */}
          {selectedFile && !isUploading && !isProcessing && (
            <Card>
              <CardHeader>
                <CardTitle>Meeting Details</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="title">Meeting Title *</Label>
                    <Input
                      id="title"
                      value={meetingTitle}
                      onChange={(e) => setMeetingTitle(e.target.value)}
                      placeholder="Enter meeting title..."
                      required
                    />
                  </div>

                  <EmailChipInput
                    emails={participants}
                    onChange={setParticipants}
                    label="Meeting Participants (Optional)"
                    placeholder="Add participant emails..."
                    required={false}
                  />

                  <div className="space-y-2">
                    <Label>Meeting Date (Optional)</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className={cn(
                            "w-full justify-start text-left font-normal",
                            !meetingDate && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {meetingDate ? format(meetingDate, "PPP") : "Select date"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={meetingDate}
                          onSelect={setMeetingDate}
                          disabled={(date) =>
                            date > new Date() || date < new Date("1900-01-01")
                          }
                          initialFocus
                          className="p-3 pointer-events-auto"
                        />
                      </PopoverContent>
                    </Popover>
                  </div>

                  <div className="pt-4 border-t">
                    <div className="flex justify-between items-center">
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p><strong>File:</strong> {selectedFile.name}</p>
                        <p><strong>Size:</strong> {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                        <p><strong>Type:</strong> {selectedFile.type}</p>
                        <p className="text-primary font-medium mt-2">
                          🤖 This file will be processed using AI to generate transcription, summary, and action items
                        </p>
                      </div>
                      <Button 
                        type="submit" 
                        variant="hero" 
                        size="lg"
                        disabled={!canSubmit}
                      >
                        {isProcessing ? "Processing with AI..." : "Submit for AI Processing"}
                      </Button>
                    </div>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Help Text */}
          {!selectedFile && (
            <Card className="bg-muted/30">
              <CardContent className="p-6">
                <h3 className="font-semibold mb-2">Supported Features</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>• AI-powered transcription and summarization</li>
                  <li>• Action item extraction and participant identification</li>
                  <li>• Interactive chat with meeting content</li>
                  <li>• Support for audio (MP3, WAV, M4A) and video (MP4, MOV, AVI) files</li>
                  <li>• Maximum file size: 500MB</li>
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}