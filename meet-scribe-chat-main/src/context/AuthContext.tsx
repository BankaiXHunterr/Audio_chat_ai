// // File: src/context/AuthContext.tsx
// import { createContext, useState, useContext, useEffect, ReactNode } from 'react';
// import { UserProfile, LoginCredentials ,apiService } from '@/services/apiService';
// import { supabase } from "@/lib/supabaseClient"; // Import your Supabase client
// import { Session } from '@supabase/supabase-js';

// export interface AuthContextType {
//   user: UserProfile | null;
//   isLoading: boolean;
//   login: (credentials: LoginCredentials) => Promise<void>;
//   logout: () => void;
// }

// export const AuthContext = createContext<AuthContextType | undefined>(undefined);

// export const AuthProvider = ({ children }: { children: ReactNode }) => {
//   const [user, setUser] = useState<UserProfile | null>(null);
//   const [isLoading, setIsLoading] = useState(true);

//   useEffect(() => {
//     // Check if user is already logged in on initial app load
//     const checkUser = () => {
//       const cachedUser = apiService.getCachedUserProfile();
//       if (cachedUser) {
//         setUser(cachedUser);
//       }
//       setIsLoading(false);
//     };
//     checkUser();
//   }, []);

//   const login = async (credentials: LoginCredentials) => {
//     const { user: loggedInUser } = await apiService.login(credentials);
//     setUser(loggedInUser);
//   };

//   const logout = () => {
//     apiService.logout();
//     setUser(null);
//   };

//   return (
//     <AuthContext.Provider value={{ user, isLoading, login, logout }}>
//       {children}
//     </AuthContext.Provider>
//   );
// };

import {
  createContext,
  useState,
  useContext,
  useEffect,
  ReactNode,
} from "react";
import {
  UserProfile,
  LoginCredentials,
  apiService,
} from "@/services/apiService";
import { supabase } from "@/lib/supabaseClient"; // Import your Supabase client
import { Session } from "@supabase/supabase-js";

export interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // The key change: listen to Supabase auth state changes
  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        // A user is logged in (either via email/password or OAuth)
        // We'll create a UserProfile object from the Supabase session data
        const authUser = session.user;
        const fullName = authUser.user_metadata?.full_name || "";
        const nameParts = fullName.split(" ");

        const userProfile: UserProfile = {
          id: authUser.id,
          email: authUser.email!,
          firstName: authUser.user_metadata?.firstName || nameParts[0] || "",
          lastName:
            authUser.user_metadata?.lastName ||
            nameParts.slice(1).join(" ") ||
            "",
          avatar: authUser.user_metadata?.avatar_url || "",
        };

        // We also cache this profile so it's available for apiService
        localStorage.setItem(
          "meetingSummarizer_userProfile",
          JSON.stringify(userProfile)
        );

        setUser(userProfile);
      } else {
        // No user is logged in, clear local storage
        localStorage.removeItem("meetingSummarizer_userProfile");
        // No user is logged in
        setUser(null);
      }
      setIsLoading(false);
    });

    // Cleanup the subscription on unmount
    return () => {
      subscription.unsubscribe();
    };
  }, []); // Run only once on initial mount

  // const login = async (credentials: LoginCredentials) => {
  //   // This part remains the same as it's for email/password login
  //   const { user: loggedInUser } = await apiService.login(credentials);
  //   setUser(loggedInUser);
  // };
  const login = async (credentials: LoginCredentials) => {
    // Use Supabase for email/password login as well
    const { data, error } = await supabase.auth.signInWithPassword({
      email: credentials.email,
      password: credentials.password,
    });

    if (error) {
      throw error; // Let the UI component handle the login error
    }

    // The onAuthStateChange listener will automatically handle setting the user profile.
    // You don't need to do anything else here!
  };

  const logout = async () => {
    // We now use the Supabase logout method
    await supabase.auth.signOut();
    // The onAuthStateChange listener will handle setting the user to null
    // We also clear any local data from our old service
    // apiService.logout();
    // setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
