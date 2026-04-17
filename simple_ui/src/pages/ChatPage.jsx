import React, { useState, useRef, useEffect, useCallback } from 'react';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import { sendChatStream } from '../api/chat';
import { useAuth } from '../context/AuthContext';

const INITIAL_MESSAGES = [
  { sender: 'bot', text: 'Sana nasıl yardımcı olabilirim?' },
];

export default function ChatPage() {
  const { logout } = useAuth();
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeNode, setActiveNode] = useState(null);

  const bottomRef = useRef(null);
  const conversationHistory = useRef([]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeNode]);

  const sendMessage = useCallback(async (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userText = inputText.trim();
    setInputText('');
    setIsLoading(true);
    setActiveNode('başlatılıyor...');

    // Kullanıcı mesajını ekle
    setMessages(prev => [...prev, { sender: 'user', text: userText }]);

    // Bot placeholder (streaming)
    setMessages(prev => [...prev, { sender: 'bot', text: '', streaming: true }]);

    try {
      await sendChatStream(userText, conversationHistory.current, {
        onNode: (node) => setActiveNode(node),

        onToken: (fullText) => {
          setMessages(prev => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            updated[lastIdx] = { ...updated[lastIdx], text: fullText };
            return updated;
          });
        },

        onDone: (finalText) => {
          setActiveNode(null);
          setMessages(prev => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            updated[lastIdx] = { ...updated[lastIdx], text: finalText, streaming: false };
            return updated;
          });

          conversationHistory.current = [
            ...conversationHistory.current,
            { role: 'user', content: userText },
            { role: 'assistant', content: finalText },
          ];
        },
      });
    } catch (error) {
      console.error('Bağlantı hatası:', error);
      setActiveNode(null);
      setMessages(prev => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        updated[lastIdx] = {
          sender: 'bot',
          text: `Hata: ${error.message}`,
          streaming: false,
          error: true,
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading]);

  return (
    <div style={s.container}>
      <style>{`
        @keyframes cursorBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        .dot { width: 6px; height: 6px; border-radius: 50%; background: #6b6b80; display: inline-block; margin-right: 3px; animation: blink 1.2s infinite; }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes blink { 0%, 80%, 100% { opacity: 0.3; } 40% { opacity: 1; } }
      `}</style>

      {/* Header */}
      <div style={s.header}>
        <span style={s.headerTitle}>AI Assistant</span>
        <button style={s.logoutBtn} onClick={logout}>Çıkış</button>
      </div>

      {/* Mesajlar */}
      <div style={s.chatContainer}>
        {messages.map((msg, index) => (
          <ChatMessage key={index} msg={msg} activeNode={activeNode} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput
        value={inputText}
        onChange={setInputText}
        onSubmit={sendMessage}
        disabled={isLoading}
      />
    </div>
  );
}

const s = {
  container: {
    backgroundColor: '#0d0d0f', color: '#e8e8f0',
    minHeight: '100vh', display: 'flex', flexDirection: 'column',
    fontFamily: 'sans-serif',
  },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '14px 24px',
    backgroundColor: '#16161a', borderBottom: '1px solid #2a2a35',
  },
  headerTitle: { fontSize: '15px', fontWeight: 600, color: '#e8e8f0' },
  logoutBtn: {
    background: 'none', border: '1px solid #2a2a35',
    color: '#6b6b80', borderRadius: '8px',
    padding: '6px 14px', fontSize: '13px',
    cursor: 'pointer', transition: 'color 0.18s, border-color 0.18s',
  },
  chatContainer: {
    flex: 1, overflowY: 'auto', padding: '28px 20px',
    display: 'flex', flexDirection: 'column', gap: '20px',
    maxWidth: '800px', margin: '0 auto', width: '100%',
  },
};
