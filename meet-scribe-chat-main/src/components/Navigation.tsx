import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
  Home, 
  Upload, 
  User, 
  LogOut, 
  Settings,
  MessageSquare,
  Mic
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import { apiService } from "@/services/apiService";
import { useAuth } from "@/hooks/useAuth";




export function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  const {user, logout} = useAuth();

  const handleLogout = async () => {
    try {
      // await apiService.logout();
      await logout();
      
      toast({
        title: "Logged out",
        description: "You have been successfully logged out",
      });
      navigate('/login');
    } catch (error) {
      console.warn('Logout error:', error);
      navigate('/login');
    }
  };

  const navItems = [
    {
      path: "/dashboard",
      icon: Home,
      label: "Dashboard",
      isActive: location.pathname === "/dashboard"
    },
    {
      path: "/upload",
      icon: Upload,
      label: "Upload",
      isActive: location.pathname === "/upload"
    },
    {
      path: "/record",
      icon: Mic,
      label: "Record",
      isActive: location.pathname === "/record"
    }
  ];

  return (
    <>
      {/* Top Header - Minimal */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            {/* Logo */}
            {/* Updated Logo Section */}
            <Link to="/dashboard" className="flex items-center space-x-3">
              <img src="/logo.png" alt="MeetingSummarizer Logo" className="h-20 w-auto" />
            </Link>
            {/* highlight-end */}
            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="relative h-8 w-8 rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="/placeholder.svg" alt="User" />
                    <AvatarFallback>U</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuItem asChild>
                  <Link to="/profile">
                    <User className="mr-2 h-4 w-4" />
                    <span>Profile</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/settings">
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Settings</span>
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur border-t supports-[backdrop-filter]:bg-background/80">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-around items-center py-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex flex-col items-center space-y-1 px-3 py-2 rounded-lg transition-colors min-w-[60px]",
                    item.isActive
                      ? "text-primary bg-primary/10"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-xs font-medium">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </nav>
    </>
  );
}