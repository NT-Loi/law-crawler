import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import DocumentPanel from './components/DocumentPanel';
import DocumentLibrary from './components/DocumentLibrary';

interface Document {
  metadata: {
    id: string;
    title: string;
    url: string;
    source?: string;  // 'vbqppl' | 'phapdien'
  };
  content: Array<{
    type: string;
    title: string;
    content: string;
  }>;
  full_content?: string;
  references?: Array<{ name: string; link: string }>;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{ id: string; title: string; content?: string }>;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

const STORAGE_KEY = 'lawvina_conversations';

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [chatWidth, setChatWidth] = useState(55);
  const [isResizing, setIsResizing] = useState(false);

  // Chat history state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Load conversations from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as Conversation[];
        setConversations(parsed);
        if (parsed.length > 0) {
          setActiveConversationId(parsed[0].id);
        }
      } catch (e) {
        console.error('Failed to parse saved conversations:', e);
      }
    }
  }, []);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    }
  }, [conversations]);

  // Create new conversation
  const handleNewConversation = useCallback(() => {
    const newConv: Conversation = {
      id: generateId(),
      title: 'Cuộc trò chuyện mới',
      messages: [{
        role: 'assistant',
        content: 'Xin chào! Tôi là trợ lý pháp luật AI của LawVina. Tôi có thể giúp bạn tra cứu và phân tích các quy định pháp luật Việt Nam.',
      }],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
  }, []);

  // Initialize with a conversation if none exists
  useEffect(() => {
    if (conversations.length === 0) {
      handleNewConversation();
    }
  }, [conversations.length, handleNewConversation]);

  // Update messages for active conversation
  const handleMessagesUpdate = useCallback((messages: Message[]) => {
    if (!activeConversationId) return;

    setConversations(prev => prev.map(conv => {
      if (conv.id === activeConversationId) {
        // Update title based on first user message
        const firstUserMsg = messages.find(m => m.role === 'user');
        const title = firstUserMsg
          ? firstUserMsg.content.slice(0, 50) + (firstUserMsg.content.length > 50 ? '...' : '')
          : conv.title;

        return {
          ...conv,
          title,
          messages,
          updatedAt: Date.now(),
        };
      }
      return conv;
    }));
  }, [activeConversationId]);

  // Select conversation
  const handleSelectConversation = useCallback((convId: string) => {
    setActiveConversationId(convId);
  }, []);

  // Delete conversation
  const handleDeleteConversation = useCallback((convId: string) => {
    setConversations(prev => {
      const filtered = prev.filter(c => c.id !== convId);
      // If deleting active conversation, switch to first remaining or create new
      if (convId === activeConversationId) {
        if (filtered.length > 0) {
          setActiveConversationId(filtered[0].id);
        } else {
          setActiveConversationId(null);
        }
      }
      return filtered;
    });
  }, [activeConversationId]);

  const handleSelectDocument = async (docId: string) => {
    try {
      const response = await axios.get(`http://localhost:8888/document/${docId}`);
      setSelectedDocument(response.data);
    } catch (error) {
      console.error('Failed to load document:', error);
    }
  };

  const handleCloseDocument = () => {
    setSelectedDocument(null);
  };

  // Resizing logic
  const startResizing = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = (e.clientX / window.innerWidth) * 100;
      if (newWidth > 30 && newWidth < 70) {
        setChatWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  // Get active conversation
  const activeConversation = conversations.find(c => c.id === activeConversationId);

  return (
    <div className={`h-screen w-screen flex bg-slate-950 overflow-hidden ${isResizing ? 'cursor-col-resize select-none' : ''}`}>
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex min-w-0 relative">
        {/* Chat Panel or Document Lookup */}
        <div
          className="h-full p-4 transition-[width] duration-0 ease-linear"
          style={{ width: selectedDocument ? `${chatWidth}%` : '100%' }}
        >
          {activeTab === 'chat' ? (
            <ChatPanel
              onSelectDocument={handleSelectDocument}
              messages={activeConversation?.messages || []}
              onMessagesUpdate={handleMessagesUpdate}
              conversationId={activeConversationId}
            />
          ) : (
            <DocumentLibrary onSelectDocument={handleSelectDocument} />
          )}
        </div>

        {/* Resizer Handle */}
        {selectedDocument && (
          <div
            className="w-4 -ml-2 hover:bg-amber-500/10 cursor-col-resize flex items-center justify-center transition-colors z-20 group relative"
            onMouseDown={startResizing}
          >
            {/* Visual Line */}
            <div className="w-1 h-12 bg-slate-700/50 group-hover:bg-amber-500/50 rounded-full transition-colors backdrop-blur-sm" />
          </div>
        )}

        {/* Document Panel */}
        {selectedDocument && (
          <div
            className="h-full p-4 pl-0 min-w-0"
            style={{ width: `${100 - chatWidth}%` }}
          >
            <DocumentPanel document={selectedDocument} onClose={handleCloseDocument} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
