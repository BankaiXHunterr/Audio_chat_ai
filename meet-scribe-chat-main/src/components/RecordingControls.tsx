import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Mic, Square, Pause, Play, AlertCircle } from 'lucide-react';
import { useMediaRecorder } from '@/hooks/useMediaRecorder';
import { RecordingSubmissionModal } from './RecordingSubmissionModal';
import { useToast } from '@/hooks/use-toast';

export const RecordingControls = () => {
  const [showSubmissionModal, setShowSubmissionModal] = useState(false);
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null);
  const { toast } = useToast();

  const {
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    error
  } = useMediaRecorder();

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const handleStartRecording = async () => {
    try {
      await startRecording();
      toast({
        title: "Recording Started",
        description: "Your meeting is now being recorded.",
      });
    } catch (error) {
      toast({
        title: "Recording Failed",
        description: "Failed to start recording. Please check your microphone permissions.",
        variant: "destructive"
      });
    }
  };

  const handleStopRecording = async () => {
    try {
      const blob = await stopRecording();
      if (blob) {
        setRecordingBlob(blob);
        setShowSubmissionModal(true);
        toast({
          title: "Recording Stopped",
          description: "Complete the meeting details to process your recording.",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to stop recording properly.",
        variant: "destructive"
      });
    }
  };

  const handleCloseModal = () => {
    setShowSubmissionModal(false);
    setRecordingBlob(null);
  };

  if (error) {
    return (
      <div className="flex items-center gap-3 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
        <AlertCircle className="h-5 w-5 text-destructive" />
        <span className="text-sm text-destructive">{error}</span>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center gap-4 p-6 bg-gradient-to-r from-primary/5 to-secondary/5 rounded-xl border border-primary/10">
        {/* Recording Status */}
        <div className="flex items-center gap-3">
          {isRecording ? (
            <>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-destructive rounded-full animate-pulse" />
                <Badge variant="destructive" className="font-medium">
                  RECORDING
                </Badge>
              </div>
              <div className="text-lg font-mono font-bold text-primary">
                {formatTime(recordingTime)}
              </div>
            </>
          ) : (
            <Badge variant="secondary">Ready to Record</Badge>
          )}
        </div>

        {/* Recording Controls */}
        <div className="flex items-center gap-2 ml-auto">
          {!isRecording ? (
            <Button
              onClick={handleStartRecording}
              variant="hero"
              size="lg"
              className="gap-2"
            >
              <Mic className="h-4 w-4" />
              Start Recording
            </Button>
          ) : (
            <Button
              onClick={handleStopRecording}
              variant="destructive"
              size="lg"
              className="gap-2"
            >
              <Square className="h-4 w-4" />
              Stop & Submit
            </Button>
          )}
        </div>
      </div>

      {/* Submission Modal */}
      <RecordingSubmissionModal
        isOpen={showSubmissionModal}
        onClose={handleCloseModal}
        recordingBlob={recordingBlob}
        recordingDuration={recordingTime}
      />
    </>
  );
};