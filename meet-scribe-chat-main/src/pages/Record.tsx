import { Navigation } from "@/components/Navigation";
import { RecordingControls } from "@/components/RecordingControls";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Mic, Volume2, Clock, Users } from "lucide-react";

export default function Record() {
  return (
    <div className="min-h-screen bg-background pb-20">
      <Navigation />
      
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold mb-2">Record Live Meeting</h1>
            <p className="text-muted-foreground">
              Start recording your meeting and automatically generate AI-powered summaries
            </p>
          </div>
        </div>

        {/* Recording Interface */}
        <div className="space-y-6">
          <RecordingControls />

          {/* Recording Tips */}
          <Card className="bg-gradient-to-r from-primary/5 to-secondary/5 border-primary/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mic className="h-5 w-5 text-primary" />
                Recording Tips
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-primary rounded-full mt-2" />
                    <div>
                      <h4 className="font-medium">Clear Audio</h4>
                      <p className="text-sm text-muted-foreground">
                        Ensure you're in a quiet environment with minimal background noise
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-primary rounded-full mt-2" />
                    <div>
                      <h4 className="font-medium">Microphone Permission</h4>
                      <p className="text-sm text-muted-foreground">
                        Allow microphone access when prompted by your browser
                      </p>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-primary rounded-full mt-2" />
                    <div>
                      <h4 className="font-medium">Meeting Details</h4>
                      <p className="text-sm text-muted-foreground">
                        Have participant emails and meeting title ready before starting
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-primary rounded-full mt-2" />
                    <div>
                      <h4 className="font-medium">Stable Connection</h4>
                      <p className="text-sm text-muted-foreground">
                        Ensure stable internet connection for processing
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Features Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Volume2 className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">AI Transcription</h3>
                <p className="text-sm text-muted-foreground">
                  Automatic speech-to-text conversion with speaker identification
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Clock className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">Smart Summary</h3>
                <p className="text-sm text-muted-foreground">
                  Key highlights and action items extracted automatically
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Users className="h-6 w-6 text-primary" />
                </div>
                <h3 className="font-semibold mb-2">Team Collaboration</h3>
                <p className="text-sm text-muted-foreground">
                  Share summaries with all meeting participants via email
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}