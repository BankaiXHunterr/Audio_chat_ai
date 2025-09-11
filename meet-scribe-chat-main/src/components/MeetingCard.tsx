import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Clock, Calendar, Users, Play, Trash2, Loader2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Meeting } from "@/services/apiService";
// interface MeetingCardProps {
//   id: string;
//   title: string;
//   date: Date;
//   duration: string;
//   summary: string;
//   participants: Array<{
//     name: string;
//     avatar?: string;
//   }>;
//   status: "completed" | "processing" | "failed";
//   onDelete?: (id: string) => void;
// }

// 1. Update the props to accept a single 'meeting' object
interface MeetingCardProps {
  meeting: Meeting;
  onDelete: (id: string) => void;
  isDeleting?: boolean;
}

// export function MeetingCard({
//   meeting,
//   onDelete
// }: MeetingCardProps) {
//   const { id, title, date, duration, summary, participants, status } = meeting;

//   participants,
//   status,
//   onDelete
// }: MeetingCardProps) {
//   const getStatusColor = (status: string) => {
//     switch (status) {
//       case "completed":
//         return "bg-success text-success-foreground";
//       case "processing":
//         return "bg-warning text-warning-foreground";
//       case "failed":
//         return "bg-destructive text-destructive-foreground";
//       default:
//         return "bg-muted text-muted-foreground";
//     }
//   };

//   const handleDelete = (e: React.MouseEvent) => {
//     e.preventDefault();
//     e.stopPropagation();
//     if (onDelete) {
//       onDelete(id);
//     }
//   };

export function MeetingCard({
  meeting,
  onDelete,
  isDeleting,
}: MeetingCardProps) {
  // 2. Update the status logic to use the new status fields
  const getStatusInfo = () => {
    if (meeting.status === "failed") {
      return {
        text: "Failed",
        color: "bg-destructive text-destructive-foreground",
      };
    }

    if (meeting.status === "processing") {
      return {
        text: "Embedding...",
        color: "bg-warning text-warning-foreground",
      };
    }
    if (meeting.status === "completed") {
      return { text: "Completed", color: "bg-success text-success-foreground" };
    }
    return { text: "Processing", color: "bg-muted text-muted-foreground" };
  };

  const statusInfo = getStatusInfo();

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onDelete(meeting.id);
  };

  return (
    <div className="relative group">
      <Link to={`/meeting/${meeting.id}`}>
        <Card className="group h-full bg-gradient-card hover:shadow-card transition-all duration-500 cursor-pointer border border-border/50 hover:border-primary/30 hover:scale-[1.03] rounded-2xl overflow-hidden backdrop-blur-sm">
          <div className="absolute inset-0 bg-gradient-primary opacity-0 group-hover:opacity-5 transition-opacity duration-500"></div>

          <CardHeader className="pb-4 relative">
            <div className="flex justify-between items-start mb-3">
              <Badge
                className={`${statusInfo.color} px-3 py-1 rounded-full text-xs font-medium shadow-sm`}
                variant="secondary"
              >
                {/* {status === "completed" && <Play className="w-3 h-3 mr-1.5" />}
                {status.charAt(0).toUpperCase() + status.slice(1)} */}

                {statusInfo.text.includes("ing") && (
                  <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
                )}
                {statusInfo.text === "Completed" && (
                  <Play className="w-3 h-3 mr-1.5" />
                )}
                {statusInfo.text}
              </Badge>
            </div>

            <h3 className="font-bold text-xl group-hover:text-primary transition-colors line-clamp-2 mb-3">
              {meeting.title || "Untitled Meeting"}
            </h3>

            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2 text-muted-foreground group-hover:text-accent transition-colors">
                <div className="p-1.5 rounded-lg bg-accent/10 group-hover:bg-accent/20 transition-colors">
                  <Calendar className="w-3.5 h-3.5" />
                </div>
                <span className="font-medium">
                  {formatDistanceToNow(meeting.date, { addSuffix: true })}
                </span>
              </div>
              <div className="flex items-center space-x-2 text-muted-foreground group-hover:text-primary transition-colors">
                <div className="p-1.5 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                  <Clock className="w-3.5 h-3.5" />
                </div>
                <span className="font-medium">{meeting.duration}</span>
              </div>
            </div>
          </CardHeader>

          <CardContent className="pt-0 relative">
            <p className="text-muted-foreground line-clamp-3 mb-5 leading-relaxed">
              {meeting.summary}
            </p>

            {meeting.participants.length > 0 && (
              <div className="flex items-center justify-between p-3 bg-muted/30 rounded-xl border border-border/40">
                <div className="flex items-center space-x-3">
                  <div className="p-1.5 rounded-lg bg-success/10">
                    <Users className="w-4 h-4 text-success" />
                  </div>
                  <div className="flex -space-x-2">
                    {/* {meeting.participants.slice(0, 4).map((participant, index) => (
                    <Avatar key={index} className="w-7 h-7 border-3 border-background shadow-sm">
                      <AvatarImage src={participant.avatar} alt={participant.name} />
                      <AvatarFallback className="text-xs font-semibold bg-gradient-primary text-primary-foreground">
                        {participant.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                  ))} */}

                    {meeting.participants.slice(0, 4).map((email) => (
                      <Avatar key={email} className="w-7 h-7 ...">
                        <AvatarFallback className="text-xs ...">
                          {/* Create avatar from the first two letters of the email */}
                          {email.substring(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                    ))}

                    {meeting.participants.length > 4 && (
                      <div className="w-7 h-7 rounded-full bg-gradient-accent border-3 border-background flex items-center justify-center shadow-sm">
                        <span className="text-xs font-bold text-white">
                          +{meeting.participants.length - 4}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                <span className="text-xs font-medium text-muted-foreground bg-background/60 px-2 py-1 rounded-md">
                  {meeting.participants.length} participant
                  {meeting.participants.length !== 1 ? "s" : ""}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </Link>

      {onDelete && (
        <button
          onClick={handleDelete}
          // highlight-start
          disabled={isDeleting} // Disable the button while deleting
          className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-all duration-300 bg-destructive/90 hover:bg-destructive text-destructive-foreground rounded-full p-2 shadow-lg backdrop-blur-sm z-10 disabled:opacity-50 disabled:cursor-not-allowed"
          // highlight-end
          aria-label="Delete meeting"
        >
          {/* highlight-start */}
          {/* Show a spinner when deleting, otherwise show the trash icon */}
          {isDeleting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Trash2 className="w-4 h-4" />
          )}
          {/* highlight-end */}
        </button>
      )}
    </div>
  );
}
