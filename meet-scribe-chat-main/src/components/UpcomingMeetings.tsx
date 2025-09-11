import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ScheduleMeetingModal } from "./ScheduleMeetingModal";
import { 
  Plus, 
  Calendar, 
  Clock, 
  Users, 
  Video,
  ExternalLink,
  Trash2
} from "lucide-react";
import { format } from "date-fns";

interface UpcomingMeeting {
  id: string;
  title: string;
  scheduledDate: Date;
  meetingUrl: string;
  duration?: string;
  participants: Array<{
    name: string;
    email: string;
    avatar?: string;
  }>;
  status: "scheduled" | "in-progress" | "recording" | "completed";
  organizer: string;
  description?: string;
}

// Mock data for upcoming meetings
const mockUpcomingMeetings: UpcomingMeeting[] = [
  {
    id: "upcoming-1",
    title: "Weekly Sprint Planning",
    scheduledDate: new Date(2025, 0, 2, 10, 0), // Tomorrow at 10 AM
    meetingUrl: "https://teams.microsoft.com/l/meetup-join/...",
    duration: "1h",
    participants: [
      { name: "John Doe", email: "john@company.com", avatar: "/placeholder.svg" },
      { name: "Jane Smith", email: "jane@company.com", avatar: "/placeholder.svg" },
      { name: "Mike Johnson", email: "mike@company.com", avatar: "/placeholder.svg" }
    ],
    status: "scheduled",
    organizer: "john@company.com",
    description: "Weekly sprint planning and backlog grooming session"
  },
  {
    id: "upcoming-2", 
    title: "Client Demo Session",
    scheduledDate: new Date(2025, 0, 3, 14, 30), // Day after tomorrow at 2:30 PM
    meetingUrl: "https://teams.microsoft.com/l/meetup-join/...",
    duration: "45m",
    participants: [
      { name: "Sarah Wilson", email: "sarah@company.com", avatar: "/placeholder.svg" },
      { name: "Client Rep", email: "client@external.com" }
    ],
    status: "scheduled",
    organizer: "sarah@company.com",
    description: "Product demo for new client onboarding"
  }
];

const getStatusColor = (status: UpcomingMeeting["status"]) => {
  switch (status) {
    case "scheduled": return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300";
    case "in-progress": return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300";
    case "recording": return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300";
    case "completed": return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300";
    default: return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300";
  }
};

const getStatusIcon = (status: UpcomingMeeting["status"]) => {
  switch (status) {
    case "scheduled": return <Calendar className="w-3 h-3" />;
    case "in-progress": return <Video className="w-3 h-3" />;
    case "recording": return <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />;
    case "completed": return <div className="w-3 h-3 bg-green-500 rounded-full" />;
    default: return <Calendar className="w-3 h-3" />;
  }
};

export function UpcomingMeetings() {
  const [meetings, setMeetings] = useState<UpcomingMeeting[]>(mockUpcomingMeetings);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleScheduleMeeting = (meetingData: {
    title: string;
    meetingUrl: string;
    scheduledDate: Date;
    participants: string[];
    description?: string;
  }) => {
    const newMeeting: UpcomingMeeting = {
      id: `upcoming-${Date.now()}`,
      title: meetingData.title,
      scheduledDate: meetingData.scheduledDate,
      meetingUrl: meetingData.meetingUrl,
      participants: meetingData.participants.map(email => ({
        name: email.split('@')[0],
        email: email
      })),
      status: "scheduled",
      organizer: "current-user@company.com", // This should come from auth context
      description: meetingData.description
    };

    setMeetings(prev => [...prev, newMeeting]);
    setIsModalOpen(false);
  };

  const handleDeleteMeeting = (meetingId: string) => {
    setMeetings(prev => prev.filter(m => m.id !== meetingId));
  };

  const handleJoinMeeting = (meetingUrl: string) => {
    window.open(meetingUrl, '_blank');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold">Upcoming Meetings</h2>
          <p className="text-muted-foreground text-sm">
            Scheduled meetings with automatic recording
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} variant="outline">
          <Plus className="w-4 h-4 mr-2" />
          Schedule Meeting
        </Button>
      </div>

      {meetings.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {meetings.map((meeting) => (
            <Card key={meeting.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{meeting.title}</CardTitle>
                    <CardDescription className="mt-1">
                      {format(meeting.scheduledDate, "MMM d, yyyy 'at' h:mm a")}
                    </CardDescription>
                  </div>
                  <Badge 
                    variant="outline" 
                    className={`ml-2 ${getStatusColor(meeting.status)}`}
                  >
                    {getStatusIcon(meeting.status)}
                    <span className="ml-1 capitalize">{meeting.status}</span>
                  </Badge>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {meeting.description && (
                  <p className="text-sm text-muted-foreground">
                    {meeting.description}
                  </p>
                )}

                <div className="flex items-center text-sm text-muted-foreground">
                  <Clock className="w-4 h-4 mr-1" />
                  {meeting.duration || "Duration TBD"}
                </div>

                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <div className="flex -space-x-2">
                    {meeting.participants.slice(0, 4).map((participant, index) => (
                      <Avatar key={index} className="w-6 h-6 border-2 border-background">
                        <AvatarImage src={participant.avatar} />
                        <AvatarFallback className="text-xs">
                          {participant.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                    ))}
                    {meeting.participants.length > 4 && (
                      <div className="w-6 h-6 bg-muted border-2 border-background rounded-full flex items-center justify-center">
                        <span className="text-xs text-muted-foreground">
                          +{meeting.participants.length - 4}
                        </span>
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground ml-2">
                    {meeting.participants.length} participant{meeting.participants.length !== 1 ? 's' : ''}
                  </span>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleJoinMeeting(meeting.meetingUrl)}
                    className="flex-1"
                  >
                    <ExternalLink className="w-4 h-4 mr-1" />
                    Join Meeting
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDeleteMeeting(meeting.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-8 text-center">
          <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No upcoming meetings</h3>
          <p className="text-muted-foreground mb-4">
            Schedule your first meeting with automatic recording and transcription
          </p>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Schedule Your First Meeting
          </Button>
        </Card>
      )}

      <ScheduleMeetingModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        onSchedule={handleScheduleMeeting}
      />
    </div>
  );
}