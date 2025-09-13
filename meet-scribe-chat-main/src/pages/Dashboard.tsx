import { useState, useEffect } from "react";
import { Navigation } from "@/components/Navigation";
import { MeetingCard } from "@/components/MeetingCard";
import { RecordingControls } from "@/components/RecordingControls";
import { UpcomingMeetings } from "@/components/UpcomingMeetings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Plus, Filter, Calendar, Clock, Users, BarChart3 } from "lucide-react";
import { Link } from "react-router-dom";
import { useToast } from "@/hooks/use-toast"; // For showing errors
import { apiService, Meeting } from "@/services/apiService";
import { Spinner } from "@/components/Spinner";
import { useSocket } from "@/context/SocketProvider"; // <-- Use the hook

export default function Dashboard() {
  const { toast } = useToast();
  const { socket, isConnected } = useSocket();

  // 1. Set up state for real meetings, loading, and errors
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State to track the ID of the meeting currently being deleted
  const [deletingId, setDeletingId] = useState<string | null>(null);
  // highlight-end

  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("date-desc");
  const [filterStatus, setFilterStatus] = useState("all");

  useEffect(() => {
    // Make sure the socket is connected before setting up listeners
    if (socket && isConnected) {
      // Listener for meeting progress updates
      const handleMeetingUpdate = (data: {
        meetingId: string;
        status: string;
        progress?: number;
      }) => {
        console.log("Received meeting update:", data);

        // Find the meeting in your local state and update its status
        // setMeetings(prevMeetings => ...);
      };

      // Set up the listener
      socket.on("meeting_processing_complete", handleMeetingUpdate);

      // Clean up the listener when the component unmounts
      return () => {
        socket.off("meeting_processing_complete", handleMeetingUpdate);
      };
    }
  }, [socket, isConnected]); // Re-run effect when connection status changes

  // 2. Use useEffect to fetch meetings when the component loads
  useEffect(() => {
    const fetchMeetings = async () => {
      try {
        setIsLoading(true);
        setError(null);
        // Call your apiService to get the meetings
        const result = await apiService.getMeetings();
        setMeetings(result.meetings); // Update the state with meetings from the API
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load meetings.";
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

    fetchMeetings();
  }, [toast]); // The dependency array ensures this runs once on mount


  // highlight-start
  // This new useEffect listens for real-time updates
  useEffect(() => {
    if (socket && isConnected) {
      // Define the handler function for the event
      const handleProcessingComplete = (data: { meetingId: string; status: string }) => {
        console.log("Processing complete event received:", data);
        
        // Update the status of the specific meeting in the local state
        setMeetings(prevMeetings =>
          prevMeetings.map(meeting =>
            meeting.id === data.meetingId
              ? { ...meeting, status: data.status as 'completed' | 'failed' }
              : meeting
          )
        );
        
        // Show a toast notification
        toast({
          title: "Processing Complete!",
          description: `The meeting is now ready to be viewed.`,
        });
      };

      // Set up the listener
      socket.on('meeting_processing_complete', handleProcessingComplete);

      // Clean up the listener when the component unmounts
      return () => {
        socket.off('meeting_processing_complete', handleProcessingComplete);
      };
    }
  }, [socket, isConnected, toast]); // Dependencies for the effect
  // highlight-end




  // 3. Update filtering/sorting to work with the new data structure
  const filteredMeetings = meetings
    .filter((meeting) => {
      const matchesSearch = meeting.title
        .toLowerCase()
        .includes(searchQuery.toLowerCase());
      // Your backend 'status' is now processing_status and embedding_status.
      // We'll use processing_status for this filter for now.
      const matchesStatus =
        filterStatus === "all" || meeting.status === filterStatus;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      // Convert date strings to Date objects for sorting
      const dateA = new Date(a.createdAt).getTime();
      const dateB = new Date(b.createdAt).getTime();
      switch (sortBy) {
        case "date-desc":
          return dateB - dateA;
        case "date-asc":
          return dateA - dateB;
        case "title-asc":
          return a.title.localeCompare(b.title);
        case "title-desc":
          return b.title.localeCompare(a.title);
        default:
          return 0;
      }
    });

  const stats = {
    total: meetings.length,
    thisWeek: meetings.filter((m) => {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return new Date(m.date) >= weekAgo;
    }).length,
    totalDuration: 0,
    participants: new Set(meetings.flatMap((m) => m.participants)).size,
  };

  const handleDeleteMeeting = async (meetingId: string) => {
    setDeletingId(meetingId);
    try {
      await apiService.deleteMeeting(meetingId);
      // After deleting, refetch the meetings to update the list
      setMeetings((prevMeetings) =>
        prevMeetings.filter((meeting) => meeting.id !== meetingId)
      );
      toast({
        title: "Success",
        description: "Meeting has been deleted.",
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to delete meeting.";
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setDeletingId(null); // Reset the loading state
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-3xl font-bold">Meeting Dashboard</h1>
              <p className="text-muted-foreground mt-2">
                Manage and explore your meeting summaries
              </p>
            </div>
            {/* <Button asChild variant="hero" size="lg">
              <Link to="/upload">
                <Plus className="w-5 h-5" />
                New Meeting
              </Link>
            </Button> */}
          </div>

          {/* Live Recording Controls */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Record Live Meeting</h2>
            <RecordingControls />
          </div>

          {/* Upcoming Meetings */}
          {/* <div className="mb-8">
            <UpcomingMeetings />
          </div> */}

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gradient-card rounded-lg p-4 border shadow-card">
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                <span className="text-sm font-medium text-muted-foreground">
                  Total Meetings
                </span>
              </div>
              <p className="text-2xl font-bold mt-1">{stats.total}</p>
            </div>
            <div className="bg-gradient-card rounded-lg p-4 border shadow-card">
              <div className="flex items-center space-x-2">
                <Calendar className="w-5 h-5 text-accent" />
                <span className="text-sm font-medium text-muted-foreground">
                  This Week
                </span>
              </div>
              <p className="text-2xl font-bold mt-1">{stats.thisWeek}</p>
            </div>
            <div className="bg-gradient-card rounded-lg p-4 border shadow-card">
              <div className="flex items-center space-x-2">
                <Clock className="w-5 h-5 text-success" />
                <span className="text-sm font-medium text-muted-foreground">
                  Total Duration
                </span>
              </div>
              <p className="text-2xl font-bold mt-1">{stats.totalDuration}</p>
            </div>
            <div className="bg-gradient-card rounded-lg p-4 border shadow-card">
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5 text-warning" />
                <span className="text-sm font-medium text-muted-foreground">
                  Participants
                </span>
              </div>
              <p className="text-2xl font-bold mt-1">{stats.participants}</p>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1">
            <Input
              placeholder="Search meetings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="max-w-md"
            />
          </div>
          <div className="flex gap-2">
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="date-desc">Newest First</SelectItem>
                <SelectItem value="date-asc">Oldest First</SelectItem>
                <SelectItem value="title-asc">Title A-Z</SelectItem>
                <SelectItem value="title-desc">Title Z-A</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-40">
                <Filter className="w-4 h-4" />
                <SelectValue placeholder="Filter" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Past Meetings */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Past Meetings</h2>
        </div>

        {/* Meetings Grid */}
        {filteredMeetings.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredMeetings.map((meeting) => (
              <MeetingCard
                key={meeting.id}
                meeting={meeting}
                onDelete={handleDeleteMeeting}
                // highlight-start
                // Pass the deleting state down to the card
                isDeleting={deletingId === meeting.id}
                // highlight-end
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-24 h-24 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <BarChart3 className="w-12 h-12 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No meetings found</h3>
            <p className="text-muted-foreground mb-6">
              {searchQuery || filterStatus !== "all"
                ? "Try adjusting your search or filters"
                : "Upload your first meeting recording to get started"}
            </p>
            {!searchQuery && filterStatus === "all" && (
              <Button asChild variant="hero" size="lg">
                <Link to="/upload">
                  <Plus className="w-5 h-5" />
                  Upload Your First Meeting
                </Link>
              </Button>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
