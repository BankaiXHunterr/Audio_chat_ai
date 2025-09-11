import { useState, useEffect } from "react";
import { Navigation } from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Bell, Moon, Globe, Download, Trash2, Shield } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Settings() {
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      meetingReminders: true,
      summaryReady: true
    },
    preferences: {
      theme: "system",
      language: "en",
      autoDownload: false,
      dataRetention: "1year"
    },
    privacy: {
      shareAnalytics: false,
      autoTranscribe: true
    }
  });
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    // Fetch user settings from your backend
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch('/api/user/settings', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const saveSettings = async () => {
    setIsSaving(true);
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch('/api/user/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(settings),
      });
      
      if (response.ok) {
        toast({
          title: "Success",
          description: "Settings saved successfully",
        });
      } else {
        throw new Error('Save failed');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save settings",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const updateNotificationSetting = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: value
      }
    }));
  };

  const updatePreferenceSetting = (key: string, value: string | boolean) => {
    setSettings(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [key]: value
      }
    }));
  };

  const updatePrivacySetting = (key: string, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      privacy: {
        ...prev.privacy,
        [key]: value
      }
    }));
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="max-w-4xl mx-auto px-4 py-6 pb-20">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
            <p className="text-muted-foreground">
              Manage your application preferences
            </p>
          </div>

          {/* Notifications */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notifications
              </CardTitle>
              <CardDescription>
                Configure how you want to be notified
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive notifications via email
                  </p>
                </div>
                <Switch
                  checked={settings.notifications.email}
                  onCheckedChange={(checked) => updateNotificationSetting('email', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Push Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive push notifications in browser
                  </p>
                </div>
                <Switch
                  checked={settings.notifications.push}
                  onCheckedChange={(checked) => updateNotificationSetting('push', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Meeting Reminders</Label>
                  <p className="text-sm text-muted-foreground">
                    Get reminded about upcoming meetings
                  </p>
                </div>
                <Switch
                  checked={settings.notifications.meetingReminders}
                  onCheckedChange={(checked) => updateNotificationSetting('meetingReminders', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Summary Ready</Label>
                  <p className="text-sm text-muted-foreground">
                    Notify when meeting summary is ready
                  </p>
                </div>
                <Switch
                  checked={settings.notifications.summaryReady}
                  onCheckedChange={(checked) => updateNotificationSetting('summaryReady', checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Preferences */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Preferences
              </CardTitle>
              <CardDescription>
                Customize your app experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Theme</Label>
                  <p className="text-sm text-muted-foreground">
                    Choose your preferred theme
                  </p>
                </div>
                <Select
                  value={settings.preferences.theme}
                  onValueChange={(value) => updatePreferenceSetting('theme', value)}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Language</Label>
                  <p className="text-sm text-muted-foreground">
                    Select your preferred language
                  </p>
                </div>
                <Select
                  value={settings.preferences.language}
                  onValueChange={(value) => updatePreferenceSetting('language', value)}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="hi">Hindi</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto Download</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically download meeting summaries
                  </p>
                </div>
                <Switch
                  checked={settings.preferences.autoDownload}
                  onCheckedChange={(checked) => updatePreferenceSetting('autoDownload', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Data Retention</Label>
                  <p className="text-sm text-muted-foreground">
                    How long to keep your data
                  </p>
                </div>
                <Select
                  value={settings.preferences.dataRetention}
                  onValueChange={(value) => updatePreferenceSetting('dataRetention', value)}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="6months">6 Months</SelectItem>
                    <SelectItem value="1year">1 Year</SelectItem>
                    <SelectItem value="2years">2 Years</SelectItem>
                    <SelectItem value="forever">Forever</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Privacy */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Privacy & Security
              </CardTitle>
              <CardDescription>
                Control your privacy and security settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Share Analytics</Label>
                  <p className="text-sm text-muted-foreground">
                    Help improve the app by sharing anonymous usage data
                  </p>
                </div>
                <Switch
                  checked={settings.privacy.shareAnalytics}
                  onCheckedChange={(checked) => updatePrivacySetting('shareAnalytics', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto Transcribe</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically transcribe uploaded audio files
                  </p>
                </div>
                <Switch
                  checked={settings.privacy.autoTranscribe}
                  onCheckedChange={(checked) => updatePrivacySetting('autoTranscribe', checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-destructive/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <Trash2 className="h-5 w-5" />
                Danger Zone
              </CardTitle>
              <CardDescription>
                Irreversible actions for your account
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="destructive" className="w-full">
                Delete Account
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                This action cannot be undone. All your data will be permanently deleted.
              </p>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={saveSettings} disabled={isSaving}>
              {isSaving ? "Saving..." : "Save Settings"}
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}