import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { Navigation } from "@/components/Navigation";
import { ChatInterface } from "@/components/ChatInterface";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft,
  Play,
  Pause,
  Volume2,
  Copy,
  Download,
  CheckSquare,
  Clock,
  Calendar,
  Users,
  MessageSquare,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import {
  apiService,
  Meeting,
  ActionItem,
  Participant,
  TranscriptEntry,
} from "@/services/apiService";
import { useToast } from "@/components/ui/use-toast";
import { Spinner } from "@/components/Spinner";

// Mock meeting data

export default function MeetingDetails() {
  const { meetingId } = useParams<{ meetingId: string }>();
  const { toast } = useToast();

  const [meetingData, setMeetingData] = useState<Meeting | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // --- START AUDIO PLAYER STATE ---
  const audioRef = useRef<HTMLAudioElement | null>(null); // 2. Create a ref for the audio element
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  // --- END AUDIO PLAYER STATE ---

  // const [meetingData, setMeetingData] = useState<typeof meetingData | null>(null);
  // 2. useEffect to fetch the data when the component loads
  useEffect(() => {
    if (!meetingId) {
      setError("No meeting ID provided.");
      setIsLoading(false);
      return;
    }

    const fetchMeetingData = async () => {
      try {
        setIsLoading(true);
        const data = await apiService.getMeetingDetails(meetingId);
        setMeetingData(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Failed to fetch meeting details.";
        setError(errorMessage);
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchMeetingData();
  }, [meetingId, toast]);

  // --- START AUDIO PLAYER LOGIC ---
  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const formatTime = (timeInSeconds: number) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(
      2,
      "0"
    )}`;
  };
  // --- END AUDIO PLAYER LOGIC ---

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could show a toast here
  };

  const copyAllHighlights = () => {
    const text = meetingData.keyHighlights
      .map((highlight, index) => `${index + 1}. ${highlight}`)
      .join("\n");
    copyToClipboard(text);
  };

  const copyAllActionItems = () => {
    const text = meetingData.actionItems
      .map(
        (item, index) =>
          `${index + 1}. ${item.task} (Assigned: ${item.assignee}, Due: ${
            item.deadline
          })`
      )
      .join("\n");
    copyToClipboard(text);
  };

  // --- ADD THIS BLOCK ---
  // 1. Render a loading state while fetching data
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="flex justify-center items-center py-20">
          <Spinner /> {/* Or any loading indicator */}
        </div>
      </div>
    );
  }

  // 2. Render an error state if the fetch fails or data is missing
  if (error || !meetingData) {
    return (
      <div className="min-h-screen bg-background text-center py-10">
        <Navigation />
        <h2 className="text-2xl font-bold text-destructive">Error</h2>
        <p className="text-muted-foreground">
          {error || "Could not load meeting data."}
        </p>
        <Button asChild className="mt-4">
          <Link to="/dashboard">Go Back to Dashboard</Link>
        </Button>
      </div>
    );
  }
  // --- END BLOCK ---

  return (
    <div className="min-h-screen bg-background pb-20">
      <Navigation />

      {/* 3. Add the hidden audio element */}
      {meetingData.recordingUrl && (
        <audio
          ref={audioRef}
          src={meetingData.recordingUrl}
          onTimeUpdate={() =>
            setCurrentTime(audioRef.current?.currentTime || 0)
          }
          onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
          onEnded={() => setIsPlaying(false)}
        />
      )}

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Button asChild variant="ghost" size="icon">
              <Link to="/dashboard">
                <ArrowLeft className="w-4 h-4" />
              </Link>
            </Button>
            <div className="flex-1">
              <h1 className="text-3xl font-bold">{meetingData.title}</h1>
              <div className="flex items-center space-x-6 mt-2 text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-4 h-4" />
                  <span>
                    {formatDistanceToNow(meetingData.date, {
                      addSuffix: true,
                    })}
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4" />
                  <span>{meetingData.duration}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Users className="w-4 h-4" />
                  <span>{meetingData.participants.length} participants</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Media Player */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Volume2 className="w-5 h-5" />
                  <span>Recording Playback</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-muted rounded-lg p-4 flex items-center justify-center h-32">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-2">
                        <Volume2 className="w-8 h-8 text-primary" />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Audio Player
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setIsPlaying(!isPlaying)}
                      disabled={!meetingData.recordingUrl}
                    >
                      {isPlaying ? (
                        <Pause className="w-4 h-4" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                    </Button>

                    <div className="flex-1">
                      <div className="flex justify-between text-sm text-muted-foreground mb-1">
                        {/* <span>{currentTime}</span> */}
                        {/* <span>{totalTime}</span> */}

                        <span>{formatTime(currentTime)}</span>
                        <span>{formatTime(duration)}</span>
                      </div>
                      {/* <div className="w-full bg-muted rounded-full h-2">
                        <div className="bg-primary h-2 rounded-full w-1/3"></div>
                      </div> */}

                      <input
                        type="range"
                        min="0"
                        max={duration || 0}
                        value={currentTime}
                        onChange={(e) => {
                          if (audioRef.current) {
                            const newTime = Number(e.target.value);
                            audioRef.current.currentTime = newTime;
                            setCurrentTime(newTime);
                          }
                        }}
                        style={{
                          backgroundSize: `calc(${(currentTime / duration) * 100 || 0}%) 100%`,
                        }}
                        // MODIFIED: Removed 'bg-primary' and added 'appearance-none'
                        className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer progress-bar"
                      />
                    </div>

                    <Button variant="outline" size="icon">
                      <Volume2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Meeting Content Tabs */}
            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="transcript">Transcript</TabsTrigger>
                <TabsTrigger value="participants">Participants</TabsTrigger>
              </TabsList>

              <TabsContent value="summary" className="space-y-6">
                {/* Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle></CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm font-medium">{meetingData.summary}</p>
                  </CardContent>
                </Card>

                {/* Key Highlights */}
                {meetingData.keyHighlights &&
                  meetingData.keyHighlights.length > 0 && (
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Key Highlights</CardTitle>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={copyAllHighlights}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-3">
                          {meetingData.keyHighlights.map((highlight, index) => (
                            <li
                              key={index}
                              className="flex items-start space-x-3"
                            >
                              <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-xs font-semibold text-primary">
                                  {index + 1}
                                </span>
                              </div>
                              <p className="text-sm leading-relaxed">
                                {highlight}
                              </p>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}

                {/* Action Items */}
                {meetingData.actionItems &&
                  meetingData.actionItems.length > 0 && (
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Action Items</CardTitle>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={copyAllActionItems}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {meetingData.actionItems.map((item, index) => (
                            <div
                              key={index}
                              className="flex items-start space-x-3 p-3 bg-muted/30 rounded-lg"
                            >
                              <div className="pt-1">
                                <CheckSquare
                                  className={`w-4 h-4 ${
                                    item.status === "completed"
                                      ? "text-success"
                                      : "text-muted-foreground"
                                  }`}
                                />
                              </div>
                              <div className="flex-1 space-y-1">
                                <p className="text-sm font-medium">
                                  {item.task}
                                </p>
                                <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                                  <span>
                                    Assigned to:{" "}
                                    <strong>{item.assignee}</strong>
                                  </span>
                                  <span>Due: {item.deadline}</span>
                                  <Badge
                                    variant={
                                      item.status === "completed"
                                        ? "default"
                                        : "secondary"
                                    }
                                    className={
                                      item.status === "completed"
                                        ? "bg-success text-success-foreground"
                                        : ""
                                    }
                                  >
                                    {item.status}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
              </TabsContent>

              <TabsContent value="transcript">
                {meetingData.transcript &&
                  meetingData.transcript.length > 0 && (
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Full Transcript</CardTitle>
                        <div className="flex space-x-2">
                          <Button variant="outline" size="sm">
                            <Copy className="w-4 h-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Download className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4 max-h-[500px] overflow-y-auto pr-4 no-scrollbar">
                          {meetingData.transcript.map((entry, index) => (
                            <div key={index} className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                                  {entry.timestamp}
                                </span>
                                <span className="text-sm font-semibold text-primary">
                                  {entry.speaker}
                                </span>
                              </div>
                              <p className="text-sm leading-relaxed pl-4 border-l-2 border-muted">
                                {entry.text}
                              </p>
                              {index < meetingData.transcript.length - 1 && (
                                <Separator />
                              )}
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
              </TabsContent>

              <TabsContent value="participants">
                <Card>
                  <CardHeader>
                    <CardTitle>Meeting Participants</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {meetingData.participants.map((participant, index) => (
                        <div
                          key={index}
                          className="flex items-center space-x-4 p-3 bg-muted/30 rounded-lg"
                        >
                          <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                            <span className="text-sm font-semibold text-primary">
                              {participant.name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium">{participant.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {participant.role}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Chat Sidebar */}
          <div className="space-y-6">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold">Ask AI Assistant</h2>
            </div>
            <ChatInterface meetingId={meetingId || "1"} />
          </div>
        </div>
      </main>
    </div>
  );
}
