// File: src/context/AuthContext.tsx
import { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { UserProfile, LoginCredentials ,apiService } from '@/services/apiService';

export interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in on initial app load
    const checkUser = () => {
      const cachedUser = apiService.getCachedUserProfile();
      if (cachedUser) {
        setUser(cachedUser);
      }
      setIsLoading(false);
    };
    checkUser();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    const { user: loggedInUser } = await apiService.login(credentials);
    setUser(loggedInUser);
  };

  const logout = () => {
    apiService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

