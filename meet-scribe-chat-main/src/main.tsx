import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./hooks/useAuth";
import { SocketProvider } from './context/SocketProvider.tsx';
createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <AuthProvider>
        <SocketProvider>
          <App />
        </SocketProvider>
      </AuthProvider>
    </React.StrictMode>
);
