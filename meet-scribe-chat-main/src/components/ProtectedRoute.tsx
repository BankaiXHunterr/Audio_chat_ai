// File: src/components/ProtectedRoute.tsx
import { useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Loader2 } from "lucide-react";
import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";

export const ProtectedRoute = () => {
  const { user, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // We don't want to run any logic until the authentication status is confirmed.
    if (isLoading) {
      return;
    }

    // SCENARIO 1: The user is NOT logged in.
    // Redirect them to the login page.
    if (!user) {
      navigate("/login", { replace: true });
      return;
    }

    // SCENARIO 2: The user IS logged in but has landed on a public page.
    // This is the key logic that handles the post-Google OAuth redirect.
    // If the user is on the root, login, or register page, send them to the dashboard.
    const isPublicRoute = ["/", "/login", "/register"].includes(
      location.pathname
    );

    // const publicRoutes = ['/', '/login', '/register'];
    // if (publicRoutes.includes(location.pathname)) {
    //   navigate('/dashboard',{ replace: true });
    // }
    if (!user && !isPublicRoute) {
      navigate("/login", { replace: true });
      return;
    }

    if (user && isPublicRoute) {
      navigate("/dashboard", { replace: true });
    }
  }, [user, isLoading, navigate, location]);

  // While the authentication check is in progress, show a centered loader.
  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // If the user is authenticated, render the requested child route (e.g., Dashboard).
  // If not, render nothing while the redirect happens.
  return user ? <Outlet /> : null;
};
