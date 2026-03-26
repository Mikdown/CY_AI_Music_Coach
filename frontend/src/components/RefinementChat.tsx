import React, { useState, useRef, useEffect } from 'react';
import { coachAPI } from '../services/api';
import '../styles/RefinementChat.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface RefinementChatProps {
  sessionId: string;
  currentPlan: string;
  onBackToPlan: () => void;
}

export const RefinementChat: React.FC<RefinementChatProps> = ({
  sessionId,
  currentPlan,
  onBackToPlan,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: `I have your current practice plan. Feel free to request any modifications! You can ask me to:
      
• Add or remove sections
• Change time allocations
• Focus on different techniques
• Adjust difficulty levels
• Personalize any part of the plan

⚠️ **Note about links:** If you ask for video links or references, please verify they're still active before using them, as AI-generated links may be outdated.

What would you like to change?`,
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const requestTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setError(null);
    setLastFailedMessage(null);

    // Add user message to chat
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    // Set a timeout alert after 30 seconds
    const timeoutAlert = setTimeout(() => {
      console.warn('⚠️ Request taking longer than 30 seconds...');
      setError('Request is taking longer than expected (>30s). This might be a backend delay. Please wait or try a simpler request.');
    }, 30000);

    requestTimeoutRef.current = timeoutAlert;

    try {
      console.log('📨 Sending refinement request:', userMessage);
      const response = await coachAPI.refinePlan({
        message: userMessage,
        session_id: sessionId,
      });

      clearTimeout(requestTimeoutRef.current!);
      console.log('✅ Refinement response received');

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.response },
      ]);
      setIsLoading(false);
    } catch (err: any) {
      clearTimeout(requestTimeoutRef.current!);
      console.error('❌ Error sending refinement message:', err);
      
      const errorMsg = err.response?.data?.detail || 
                      err.message || 
                      'Failed to refine plan. Request may have timed out.';
      
      setError(`${errorMsg} Click below to try again.`);
      setLastFailedMessage(userMessage); // Store for retry
      setIsLoading(false);
    }
  };

  const handleRetry = async () => {
    if (lastFailedMessage) {
      console.log('🔄 Retrying failed message:', lastFailedMessage);
      setError(null);
      setInput(lastFailedMessage);
      // Simulate user clicking send
      setTimeout(() => {
        const form = document.querySelector('.chat-input-form') as HTMLFormElement;
        if (form) {
          form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        }
      }, 100);
    }
  };

  return (
    <div className="refinement-chat">
      <div className="chat-container">
        <div className="chat-header">
          <h2>Refine Your Practice Plan</h2>
          <button className="back-button" onClick={onBackToPlan}>
            ← Back to Plan
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.content.split('\n').map((line, lineIdx) => (
                  <p key={lineIdx}>{line || <br />}</p>
                ))}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant loading">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {error && (
          <div className="error-banner">
            <div className="error-content">
              <span>{error}</span>
              {lastFailedMessage && (
                <button 
                  type="button" 
                  className="retry-button"
                  onClick={handleRetry}
                  disabled={isLoading}
                >
                  🔄 Retry
                </button>
              )}
            </div>
          </div>
        )}

        <form className="chat-input-form" onSubmit={handleSendMessage}>
          <input
            type="text"
            placeholder="Describe how you'd like to modify the plan..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="send-button"
          >
            Send →
          </button>
        </form>
      </div>
    </div>
  );
};
