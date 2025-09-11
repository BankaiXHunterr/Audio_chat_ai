// File: src/components/ProtectedRoute.tsx
import { useAuth } from '@/hooks/useAuth';
import { Loader2 } from 'lucide-react';
import { Navigate, Outlet } from 'react-router-dom';

export const ProtectedRoute = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <Loader2 />;
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />;
};