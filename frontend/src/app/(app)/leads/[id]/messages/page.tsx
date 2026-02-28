"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { cn, formatDateTime } from "@/lib/utils";

interface Message {
  id: number;
  direction: string;
  channel: string;
  from_number: string | null;
  to_number: string | null;
  body: string;
  ai_intent: string | null;
  ai_suggested_reply: string | null;
  sent_by: string | null;
  created_at: string;
}

export default function MessagesPage() {
  const params = useParams();
  const leadId = Number(params.id);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);

  const fetchMessages = useCallback(async () => {
    try {
      const data = await api.getMessages(leadId);
      setMessages(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load messages");
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  async function handleSend() {
    if (!newMessage.trim()) return;
    setSending(true);
    try {
      await api.sendMessage(leadId, newMessage);
      setNewMessage("");
      await fetchMessages();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Failed to send");
    } finally {
      setSending(false);
    }
  }

  async function handleUseSuggested(reply: string) {
    setNewMessage(reply);
  }

  const intentColor = (intent: string | null) => {
    const colors: Record<string, string> = {
      opt_out: "bg-red-100 text-red-800",
      interested: "bg-green-100 text-green-800",
      appointment_request: "bg-emerald-100 text-emerald-800",
      question: "bg-blue-100 text-blue-800",
      not_interested: "bg-gray-100 text-gray-600",
      greeting: "bg-yellow-100 text-yellow-800",
    };
    return colors[intent || ""] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Link href={`/leads/${leadId}`} className="text-sm text-gray-500 hover:text-gray-700">
          &larr; Back to lead
        </Link>
        <h1 className="text-xl font-bold text-gray-900">Messages</h1>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Message Thread */}
      <div className="rounded-xl bg-white shadow-sm border border-gray-200 p-4 space-y-3 min-h-[400px] max-h-[600px] overflow-y-auto">
        {loading ? (
          <div className="text-center text-gray-400 py-12">Loading messages...</div>
        ) : messages.length === 0 ? (
          <div className="text-center text-gray-400 py-12">No messages yet</div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "max-w-[80%] rounded-lg p-3",
                msg.direction === "outbound"
                  ? "ml-auto bg-solar-50 border border-solar-200"
                  : "mr-auto bg-gray-50 border border-gray-200"
              )}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-gray-500">
                  {msg.direction === "outbound" ? (msg.sent_by || "System") : (msg.from_number || "Lead")}
                </span>
                <span className="text-xs text-gray-400">{formatDateTime(msg.created_at)}</span>
                {msg.ai_intent && (
                  <span className={cn("inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium", intentColor(msg.ai_intent))}>
                    {msg.ai_intent}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-800">{msg.body}</p>

              {/* AI Suggested Reply */}
              {msg.direction === "inbound" && msg.ai_suggested_reply && (
                <div className="mt-2 rounded-lg bg-blue-50 border border-blue-200 p-2">
                  <p className="text-xs font-medium text-blue-700 mb-1">AI Suggested Reply:</p>
                  <p className="text-xs text-blue-800">{msg.ai_suggested_reply}</p>
                  <button
                    onClick={() => handleUseSuggested(msg.ai_suggested_reply!)}
                    className="mt-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Use this reply
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Send Message */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
        />
        <button
          onClick={handleSend}
          disabled={!newMessage.trim() || sending}
          className="rounded-lg bg-solar-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-solar-700 disabled:opacity-50 transition-colors"
        >
          {sending ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}
