import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BrainCircuit, MessageCircle, Send } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";

interface Message {
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  timestamp: Date;
}

export function Chatbot() {
  const [messages, setMessages] = useState<Message[]>(() => {
    const savedMessages = localStorage.getItem("chatMessages");
    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages);
        if (Array.isArray(parsedMessages) && parsedMessages.every(m => 'role' in m && 'content' in m && 'timestamp' in m)) {
          return parsedMessages.map((msg: Message) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          }));
        }
      } catch (e) {
        console.error("Could not parse chat messages from localStorage", e);
      }
    }
    return [
      {
        role: "assistant",
        content: "Hello! I'm your conveyor monitoring assistant. Ask me about current conditions, trends, or predictions.",
        timestamp: new Date(),
      },
    ];
  });
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsTyping(true);

    try {
      const apiUrl = import.meta.env.PROD
        ? `${import.meta.env.VITE_API_TARGET_URL || ''}prod/prompt`
        : '/api/prod/prompt';

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: currentInput }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      
      const data = await response.json();
      console.log("API Response:", data);

      const rawContent = data.result || "Sorry, I couldn't get a response.";
      const thinkingRegex = /<thinking>(.*?)<\/thinking>/s;
      const thinkingMatch = rawContent.match(thinkingRegex);

      const thinking = thinkingMatch ? thinkingMatch[1].trim() : undefined;
      const content = rawContent.replace(thinkingRegex, "").trim();

      const assistantMessage: Message = {
        role: "assistant",
        content: content,
        thinking: thinking,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Failed to fetch from API:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <Card className="bg-gradient-card border-border h-full flex flex-col">
      <div className="p-4 border-b border-border flex items-center gap-2">
        <MessageCircle className="h-5 w-5 text-primary" />
        <h3 className="font-bold text-lg text-foreground">AI Assistant</h3>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown rehypePlugins={[rehypeRaw]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm">{message.content}</p>
                )}
                {message.thinking && (
                  <Collapsible>
                    <CollapsibleTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-2 w-full justify-start text-xs p-1 h-auto"
                      >
                        <BrainCircuit className="h-4 w-4 mr-2" />
                        Show thought process
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="mt-2 p-2 bg-background/50 rounded-md border border-border">
                      <p className="text-xs italic opacity-80">
                        {message.thinking}
                      </p>
                    </CollapsibleContent>
                  </Collapsible>
                )}
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-secondary text-secondary-foreground rounded-lg p-3 max-w-[80%]">
                <p className="text-sm">Analyzing...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about machine conditions..."
            className="bg-secondary border-border"
          />
          <Button onClick={handleSend} size="icon" disabled={isTyping}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
