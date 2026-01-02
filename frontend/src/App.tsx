import { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import DocumentPanel from './components/DocumentPanel';

interface Document {
  metadata: {
    id: string;
    title: string;
    url: string;
  };
  content: Array<{
    id: number;
    doc_id: string;
    anchor: string;
    type: string;
    title: string;
    content: string;
    is_structure: boolean;
  }>;
}

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [chatWidth, setChatWidth] = useState(55); // Percentage width of chat panel when document is open
  const [isResizing, setIsResizing] = useState(false);

  const handleSelectDocument = async (docId: string) => {
    try {
      const response = await axios.get(`http://localhost:8000/document/${docId}`);
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

      // Calculate new width percentage
      const newWidth = (e.clientX / window.innerWidth) * 100;
      // Limit bounds (30% to 70%)
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

  return (
    <div className={`h-screen w-screen flex bg-slate-950 overflow-hidden ${isResizing ? 'cursor-col-resize select-none' : ''}`}>
      {/* Sidebar */}
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content Area */}
      <main className="flex-1 flex min-w-0 relative">
        {/* Chat Panel */}
        <div
          className="h-full p-4 transition-[width] duration-0 ease-linear"
          style={{ width: selectedDocument ? `${chatWidth}%` : '100%' }}
        >
          <ChatPanel onSelectDocument={handleSelectDocument} />
        </div>

        {/* Resizer Handle */}
        {selectedDocument && (
          <div
            className="w-1 bg-slate-800 hover:bg-amber-500/50 cursor-col-resize flex items-center justify-center transition-colors z-10"
            onMouseDown={startResizing}
          >
            <div className="w-0.5 h-8 bg-slate-600 rounded-full" />
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
