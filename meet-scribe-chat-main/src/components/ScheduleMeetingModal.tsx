import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmailChipInput } from "./EmailChipInput";
import { useToast } from "@/hooks/use-toast";
import { Calendar, Clock, Link2, Users, FileText } from "lucide-react";

interface ScheduleMeetingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSchedule: (meetingData: {
    title: string;
    meetingUrl: string;
    scheduledDate: Date;
    participants: string[];
    description?: string;
  }) => void;
}

export function ScheduleMeetingModal({ 
  open, 
  onOpenChange, 
  onSchedule 
}: ScheduleMeetingModalProps) {
  const [title, setTitle] = useState("");
  const [meetingUrl, setMeetingUrl] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [participants, setParticipants] = useState<string[]>([]);
  const [description, setDescription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const { toast } = useToast();

  const validateMeetingUrl = (url: string) => {
    const microsoftTeamsPattern = /^https:\/\/teams\.microsoft\.com\/l\/meetup-join\//;
    const microsoftMeetingPattern = /^https:\/\/[a-zA-Z0-9-]+\.teams\.microsoft\.com\//;
    return microsoftTeamsPattern.test(url) || microsoftMeetingPattern.test(url);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      toast({
        title: "Missing title",
        description: "Please provide a meeting title",
        variant: "destructive"
      });
      return;
    }

    if (!meetingUrl.trim()) {
      toast({
        title: "Missing meeting URL",
        description: "Please provide a Microsoft Teams meeting URL",
        variant: "destructive"
      });
      return;
    }

    if (!validateMeetingUrl(meetingUrl)) {
      toast({
        title: "Invalid meeting URL",
        description: "Please provide a valid Microsoft Teams meeting URL",
        variant: "destructive"
      });
      return;
    }

    if (!date || !time) {
      toast({
        title: "Missing date/time",
        description: "Please select both date and time for the meeting",
        variant: "destructive"
      });
      return;
    }

    const scheduledDate = new Date(`${date}T${time}`);
    const now = new Date();
    
    if (scheduledDate <= now) {
      toast({
        title: "Invalid date/time",
        description: "Meeting must be scheduled for a future date and time",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);

    try {
      // Here you would typically make an API call to schedule the meeting
      // and set up the automated recording bot
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call

      onSchedule({
        title: title.trim(),
        meetingUrl: meetingUrl.trim(),
        scheduledDate,
        participants,
        description: description.trim() || undefined
      });

      toast({
        title: "Meeting scheduled successfully",
        description: "The meeting has been scheduled and will be automatically recorded",
      });

      // Reset form
      setTitle("");
      setMeetingUrl("");
      setDate("");
      setTime("");
      setParticipants([]);
      setDescription("");
      
    } catch (error) {
      toast({
        title: "Failed to schedule meeting",
        description: "There was an error scheduling your meeting. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Schedule Meeting with Auto-Recording
          </DialogTitle>
          <DialogDescription>
            Schedule a Microsoft Teams meeting that will be automatically joined and recorded by our AI bot.
            All participants will receive the meeting details and recordings in their dashboard.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="title" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Meeting Title *
            </Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Weekly Team Standup"
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="meetingUrl" className="flex items-center gap-2">
              <Link2 className="w-4 h-4" />
              Microsoft Teams Meeting URL *
            </Label>
            <Input
              id="meetingUrl"
              value={meetingUrl}
              onChange={(e) => setMeetingUrl(e.target.value)}
              placeholder="https://teams.microsoft.com/l/meetup-join/..."
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              Paste the Microsoft Teams meeting link. Our AI bot will join as a participant to record the meeting.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="date" className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Date *
              </Label>
              <Input
                id="date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="time" className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Time *
              </Label>
              <Input
                id="time"
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Participants Email Addresses
            </Label>
            <EmailChipInput
              emails={participants}
              onChange={setParticipants}
              placeholder="Enter email addresses of participants"
            />
            <p className="text-xs text-muted-foreground">
              Add participant email addresses to automatically share meeting recordings and summaries with them.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the meeting agenda or purpose"
              rows={3}
              disabled={isLoading}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isLoading}
              className="min-w-[120px]"
            >
              {isLoading ? "Scheduling..." : "Schedule Meeting"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}