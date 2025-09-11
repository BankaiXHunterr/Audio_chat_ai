import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import apiService from "@/services/apiService";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  meetingId: string;
}

export function ChatInterface({ meetingId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "assistant",
      content: "Hello! I'm your AI assistant. Feel free to ask me anything about this meeting - I can help you find specific information, clarify discussions, or provide additional insights.",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // highlight-start
    // ---- Replace the mock response with a real API call ----
    try {
      // Call the new method from your apiService
      const response = await apiService.askQuestion(meetingId, userMessage.content);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: response.response, // Use the actual content from the API
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

    } catch (error) {
      console.error("Failed to fetch AI response:", error);
      // Create an error message to display in the chat UI
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: "Sorry, I encountered an error while trying to respond. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);

    } finally {
      // Ensure loading is set to false whether the call succeeds or fails
      setIsLoading(false);
      inputRef.current?.focus();
    }
// highlight-end

    // Simulate AI response
    // setTimeout(() => {
    //   const assistantMessage: Message = {
    //     id: (Date.now() + 1).toString(),
    //     type: "assistant",
    //     content: generateMockResponse(userMessage.content),
    //     timestamp: new Date()
    //   };
    //   setMessages(prev => [...prev, assistantMessage]);
    //   setIsLoading(false);
    // }, 1500);

    // inputRef.current?.focus();

  };


  return (
    <Card className="h-[600px] flex flex-col">
      <CardContent className="flex-1 flex flex-col p-6 space-y-4 overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2 no-scrollbar">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex space-x-3",
                message.type === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "flex space-x-3 max-w-[80%]",
                  message.type === "user" ? "flex-row-reverse space-x-reverse" : "flex-row"
                )}
              >
                <Avatar className="w-8 h-8 flex-shrink-0">
                  <AvatarFallback className={cn(
                    message.type === "user" 
                      ? "bg-primary text-primary-foreground" 
                      : "bg-accent text-accent-foreground"
                  )}>
                    {message.type === "user" ? (
                      <User className="w-4 h-4" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </AvatarFallback>
                </Avatar>
                
                <div
                  className={cn(
                    "rounded-lg px-4 py-3 shadow-soft",
                    message.type === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  )}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <p className={cn(
                    "text-xs mt-2 opacity-70",
                    message.type === "user" ? "text-primary-foreground" : "text-muted-foreground"
                  )}>
                    {message.timestamp.toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex space-x-3 justify-start">
              <Avatar className="w-8 h-8">
                <AvatarFallback className="bg-accent text-accent-foreground">
                  <Bot className="w-4 h-4" />
                </AvatarFallback>
              </Avatar>
              <div className="bg-muted rounded-lg px-4 py-3 shadow-soft">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about this meeting..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button 
            type="submit" 
            disabled={!input.trim() || isLoading}
            variant="default"
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}