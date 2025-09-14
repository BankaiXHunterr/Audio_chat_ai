


import { useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PWAInstallPrompt } from "@/components/PWAInstallPrompt";
import { useAuth } from "./hooks/useAuth";
import { ProtectedRoute } from "./components/ProtectedRoute";

// Import Pages
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Record from "./pages/Record";
import MeetingDetails from "./pages/MeetingDetails";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

// A new component to contain the routes and the redirect logic
const AppRoutes = () => {
  const { user, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Wait for the auth state to be determined
    if (isLoading) {
      return;
    }

    const isPublicRoute = ['/', '/login', '/register'].includes(window.location.pathname);

    // If a logged-in user lands on a public route, redirect them to the dashboard.
    // This is the logic that will fire after a successful Google login.
    if (user && isPublicRoute) {
      navigate('/dashboard', { replace: true });
    }
    
  }, [user, isLoading, navigate]);

  // While checking auth, you might want to show a global loader
  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        {/* Or your Loader2 component */}
        <p>Loading application...</p>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Login />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected Routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/record" element={<Record />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/meeting/:meetingId" element={<MeetingDetails />} />
      </Route>
      
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <PWAInstallPrompt />
      <BrowserRouter>
        {/* The AppRoutes component now contains all the logic */}
        <AppRoutes />
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
