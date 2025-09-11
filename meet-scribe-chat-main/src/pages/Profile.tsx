import { useState, useEffect } from "react";
import { Navigation } from "@/components/Navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ProfileImageUploader } from "@/components/ProfileImageUploader";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { User, Mail, Building, Calendar, Phone } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Profile() {
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [profileData, setProfileData] = useState({
    name: "John Doe",
    email: "john.doe@icici.com",
    phone: "+91 98765 43210",
    department: "Technology",
    role: "Senior Manager",
    joinDate: "2023-01-15",
    avatar: ""
  });
  const { toast } = useToast();

  useEffect(() => {
    // Fetch user profile from your backend
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch('/api/user/profile', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setProfileData(data);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(profileData),
      });
      
      if (response.ok) {
        toast({
          title: "Success",
          description: "Profile updated successfully",
        });
        setIsEditing(false);
      } else {
        throw new Error('Update failed');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update profile",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAvatarUpdate = (avatarUrl: string) => {
    setProfileData({ ...profileData, avatar: avatarUrl });
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="max-w-4xl mx-auto px-4 py-6 pb-20">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
            <p className="text-muted-foreground">
              Manage your account information
            </p>
          </div>

          <Card>
            <CardHeader className="pb-6">
              <div className="flex flex-col md:flex-row items-center space-y-4 md:space-y-0 md:space-x-6">
                <ProfileImageUploader 
                  currentAvatar={profileData.avatar}
                  userName={profileData.name}
                  onAvatarUpdate={handleAvatarUpdate}
                />
                <div className="text-center md:text-left space-y-2">
                  <h2 className="text-2xl font-semibold">{profileData.name}</h2>
                  <p className="text-muted-foreground">{profileData.role}</p>
                  <Badge variant="secondary">{profileData.department}</Badge>
                </div>
              </div>
            </CardHeader>
            
            <CardContent>
              <div className="grid gap-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <div className="flex">
                      <User className="mr-2 mt-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="name"
                        value={profileData.name}
                        onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <div className="flex">
                      <Mail className="mr-2 mt-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="email"
                        type="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <div className="flex">
                      <Phone className="mr-2 mt-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="phone"
                        value={profileData.phone}
                        onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="department">Department</Label>
                    <div className="flex">
                      <Building className="mr-2 mt-2.5 h-4 w-4 text-muted-foreground" />
                      <Input
                        id="department"
                        value={profileData.department}
                        onChange={(e) => setProfileData({ ...profileData, department: e.target.value })}
                        disabled={!isEditing}
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label>Member Since</Label>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <Calendar className="mr-2 h-4 w-4" />
                    {new Date(profileData.joinDate).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </div>
                </div>

                <div className="flex justify-end space-x-2">
                  {isEditing ? (
                    <>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setIsEditing(false);
                          fetchProfile(); // Reset to original data
                        }}
                      >
                        Cancel
                      </Button>
                      <Button onClick={handleSave} disabled={isLoading}>
                        {isLoading ? "Saving..." : "Save Changes"}
                      </Button>
                    </>
                  ) : (
                    <Button onClick={() => setIsEditing(true)}>
                      Edit Profile
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}