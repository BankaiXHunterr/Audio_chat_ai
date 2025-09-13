// // Create a new file: frontend/src/context/SocketProvider.tsx

// import React, {
//   createContext,
//   useContext,
//   useEffect,
//   useState,
//   ReactNode,
// } from "react";
// import { io, Socket } from "socket.io-client";
// import { getAccessToken } from "@/services/apiService"; // Your function to get the JWT

// // Define the shape of the context
// interface SocketContextType {
//   socket: Socket | null;
//   isConnected: boolean;
// }

// // Create the context with a default value
// const SocketContext = createContext<SocketContextType>({
//   socket: null,
//   isConnected: false,
// });

// // Define the props for the provider component
// interface SocketProviderProps {
//   children: ReactNode;
// }

// // Create a custom hook for easy access to the context
// export const useSocket = () => {
//   return useContext(SocketContext);
// };

// export const SocketProvider = ({ children }: SocketProviderProps) => {
//   const [socket, setSocket] = useState<Socket | null>(null);
//   const [isConnected, setIsConnected] = useState(false);
//   const apiUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:7888";

//   useEffect(() => {
//     const token = getAccessToken();

//     // Only attempt to connect if the user is logged in (has a token)
//     if (token) {
//       // Establish the connection with the backend, passing the token for auth
//       const newSocket = io(apiUrl, {
//         auth: {
//           token: token,
//         },
//         transports: ["websocket"], // Prefer WebSocket for performance
//       });

//       setSocket(newSocket);

//       newSocket.on("connect", () => {
//         console.log("✅ Socket connected:", newSocket.id);
//         setIsConnected(true);
//       });

//       newSocket.on("disconnect", () => {
//         console.log("❌ Socket disconnected");
//         setIsConnected(false);
//       });

//       newSocket.on("authenticated", (data) => {
//         console.log("🔒 Socket authentication successful:", data);
//       });

//       newSocket.on("connect_error", (err) => {
//         console.error("❌ Socket connection error:", err.message);
//       });

//       // Cleanup function to disconnect the socket when the component unmounts
//       // or when the user logs out (and the token changes).
//       return () => {
//         newSocket.disconnect();
//       };
//     };

//     const cleanupPromise = connectSocket();

//     // The effect's cleanup function handles the disconnection
//     return () => {
//       cleanupPromise.then(cleanup => {
//         if (cleanup) {
//           cleanup();
//         }
//       });
//     };

//   }, [apiUrl]); // Re-run effect if API URL changes

//   return (
//     <SocketContext.Provider value={{ socket, isConnected }}>
//       {children}
//     </SocketContext.Provider>
//   );
// };

// frontend/src/context/SocketProvider.tsx

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { io, Socket } from "socket.io-client";
import { getAccessToken } from "@/services/apiService"; // Your async function to get the JWT
// It's good practice to tie the connection to the auth state
// import { useAuth } from './AuthProvider';

// Define the shape of the context
interface SocketContextType {
  socket: Socket | null;
  isConnected: boolean;
}

// Create the context with a default value
const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false,
});

// Create a custom hook for easy access to the context
export const useSocket = () => {
  return useContext(SocketContext);
};

// Define the props for the provider component
interface SocketProviderProps {
  children: ReactNode;
}

export const SocketProvider = ({ children }: SocketProviderProps) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const apiUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:7888";
  // const { user } = useAuth(); // Assuming you have an AuthProvider that gives you the user

  useEffect(() => {
    // We need an async function to await the token
    const connectSocket = async () => {
      const token = await getAccessToken(); // Await the token here // Only attempt to connect if the user is logged in (has a token)

      if (token) {
        const newSocket = io(apiUrl, {
          auth: {
            token: token, // Now this is the actual JWT string
          },
          path: "/socket.io", // Ensure the path is correct
          transports: ["websocket"],
        });

        setSocket(newSocket);

        newSocket.on("connect", () => {
          console.log("✅ Socket connected:", newSocket.id);
          setIsConnected(true);
        });

        newSocket.on("disconnect", () => {
          console.log("❌ Socket disconnected");
          setIsConnected(false);
        });

        newSocket.on("authenticated", (data) => {
          console.log("🔒 Socket authentication successful:", data);
        });
        newSocket.on("connect_error", (err) => {
          console.error("❌ Socket connection error:", err.message);
        }); // Return a cleanup function

        return () => {
          newSocket.disconnect();
        };
      }
    };

    const cleanupPromise = connectSocket();

    // The effect's cleanup function handles the disconnection
    return () => {
      cleanupPromise.then((cleanup) => {
        if (cleanup) {
          cleanup();
        }
      });
    };
    // It's best to run this effect when the user's login state changes.
    // If you have an AuthProvider, you would add `user` or `token` to the dependency array.
  }, [apiUrl]);

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
};
