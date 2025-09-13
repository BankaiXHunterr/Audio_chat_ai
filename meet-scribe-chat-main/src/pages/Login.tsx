import { useState } from "react";
import { Link, redirect, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageSquare, Eye, EyeOff, Building2, Chrome } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiService } from "@/services/apiService";
import { useAuth } from "@/hooks/useAuth";
import { supabase } from "@/lib/supabaseClient";

export default function Login() {
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: ""
  });
  const { toast } = useToast();
  const navigate = useNavigate();

// Handle Google OAuth login
  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      // Use the signInWithOAuth method provided by the Supabase JS library
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          // This will redirect the user back to your app after authentication.
          // Make sure this URL is in your Supabase Auth Providers config.
          redirectTo: window.location.origin 
        },
      });

      if (data.url){
        window.location.href = data.url;
      }

      // The rest of the authentication flow is handled by the AuthContext listener.
      console.log('[Login.tsx][line-43] Google login initiated:', data);

    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Google login failed",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    setIsLoading(true);

    try {
      // Use the signInWithOAuth method provided by the Supabase JS library
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'azure',
        options: {
          scopes:'email',
          redirectTo:window.location.origin
        },
      });

      if (data.url){
        window.location.href = data.url;
      }

      // The rest of the authentication flow is handled by the AuthContext listener.
      console.log('[Login.tsx][line-43] Microsoft login initiated:', data);

    } catch (error) {
      toast({
        title: "Error",
        description: "Microsoft login failed",
        variant: "destructive",
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {

      // const { user, tokens } = await apiService.login({
      //   email: formData.email,
      //   password: formData.password
      // });
      await login({
        email: formData.email,
        password: formData.password
      });
      
      // Display welcome toast
      const user = apiService.getCachedUserProfile();
      if (!user) throw new Error("User data not found after login");

      toast({
        title: "Success",
        description: `Welcome back, ${user.firstName}!`,
      });
      
      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error) {
      toast({
        title: "Login Failed", 
        description: error instanceof Error ? error.message : "Invalid credentials",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="w-12 h-12 bg-gradient-icici rounded-lg flex items-center justify-center">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">Welcome Back</CardTitle>
          <CardDescription>
            Sign in to your MeetingSummarizer account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </form>

          {/* OAuth Login Options */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Or continue with
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                onClick={handleGoogleLogin}
                disabled={isLoading}
                className="w-full"
              >
                <Chrome className="mr-2 h-4 w-4 text-red-500" />
                Google
              </Button>
              <Button
                variant="outline"
                onClick={handleMicrosoftLogin}
                disabled={isLoading}
                className="w-full"
              >
                <Building2 className="mr-2 h-4 w-4 text-blue-600" />
                Microsoft
              </Button>
            </div>
          </div>

          <div className="mt-6 text-center text-sm">
            <Link to="/forgot-password" className="text-primary hover:underline">
              Forgot your password?
            </Link>
          </div>
          
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link to="/register" className="text-primary hover:underline">
              Sign up
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}