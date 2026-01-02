import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, BookOpen } from 'lucide-react';
import Button from './ui/Button';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: Array<{ id: string; title: string }>;
}

interface ChatPanelProps {
    onSelectDocument: (docId: string) => void;
}

const ChatPanel = ({ onSelectDocument }: ChatPanelProps) => {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: 'Xin chào! Tôi là trợ lý pháp luật AI của LawVina. Tôi có thể giúp bạn tra cứu và phân tích các quy định pháp luật Việt Nam.',
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        // Create a placeholder assistant message
        setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: '', sources: [] },
        ]);

        try {
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: input,
                    history: messages.slice(-6),
                }),
            });

            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep the incomplete line in buffer

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);

                        setMessages((prev) => {
                            const newMessages = [...prev];
                            const lastIndex = newMessages.length - 1;
                            newMessages[lastIndex] = { ...newMessages[lastIndex] };

                            if (data.type === 'sources') {
                                newMessages[lastIndex].sources = data.data;
                            } else if (data.type === 'content') {
                                newMessages[lastIndex].content += data.delta;
                            }

                            return newMessages;
                        });
                    } catch (e) {
                        console.error('Error parsing JSON chunk', e);
                    }
                }
            }

        } catch (error) {
            setMessages((prev) => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                lastMsg.content += '\n\n[Lỗi kết nối: Không thể nhận phản hồi từ AI]';
                return newMessages;
            });
        } finally {
            setIsLoading(false);
        }
    };

    // Helper to render content with thinking blocks
    const renderContent = (content: string) => {
        const thinkStart = content.indexOf('<think>');
        if (thinkStart !== -1) {
            const thinkEnd = content.indexOf('</think>');
            const isThinking = thinkEnd === -1;

            const beforeThink = content.slice(0, thinkStart);
            const thinkContent = isThinking
                ? content.slice(thinkStart + 7)
                : content.slice(thinkStart + 7, thinkEnd);
            const afterThink = isThinking ? '' : content.slice(thinkEnd + 8);

            return (
                <div className="space-y-4">
                    {beforeThink && <p className="text-sm leading-relaxed whitespace-pre-wrap">{beforeThink}</p>}

                    <div className="border border-amber-500/20 bg-amber-500/5 rounded-xl overflow-hidden">
                        <details className="group" open={isThinking}>
                            <summary className="flex items-center gap-2 px-4 py-2 bg-amber-500/10 cursor-pointer hover:bg-amber-500/20 transition-colors text-xs font-medium text-amber-500 select-none">
                                <Sparkles className="w-3 h-3" />
                                <span>{isThinking ? 'Đang suy luận...' : 'Quy trình suy luận'}</span>
                            </summary>
                            <div className="p-4 text-xs text-slate-400 font-mono leading-relaxed whitespace-pre-wrap border-t border-amber-500/10 bg-slate-950/30">
                                {thinkContent || '...'}
                                {isThinking && <span className="inline-block w-1.5 h-3 ml-1 bg-amber-500 animate-pulse" />}
                            </div>
                        </details>
                    </div>

                    {afterThink && <p className="text-sm leading-relaxed whitespace-pre-wrap animate-fade-in">{afterThink}</p>}
                </div>
            );
        }

        return <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>;
    };

    return (
        <div className="h-full flex flex-col bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                        <Bot className="w-5 h-5 text-amber-500" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-white">Trợ lý Pháp luật AI</h2>
                        <div className="flex items-center gap-1.5">
                            <span className={`w-2 h-2 rounded-full ${isLoading ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`} />
                            <span className={`text-xs ${isLoading ? 'text-amber-500' : 'text-emerald-500'}`}>
                                {isLoading ? 'Đang trả lời...' : 'Đang hoạt động'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`flex gap-4 animate-slide-up ${message.role === 'user' ? 'flex-row-reverse' : ''
                            }`}
                    >
                        {/* Avatar */}
                        <div
                            className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${message.role === 'user'
                                ? 'bg-blue-600'
                                : 'bg-slate-700'
                                }`}
                        >
                            {message.role === 'user' ? (
                                <User className="w-4 h-4 text-white" />
                            ) : (
                                <Bot className="w-4 h-4 text-amber-500" />
                            )}
                        </div>

                        {/* Message Content */}
                        <div className={`flex-1 max-w-[85%] ${message.role === 'user' ? 'text-right' : ''}`}>
                            <div
                                className={`inline-block px-4 py-3 rounded-2xl w-full text-left ${message.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-md'
                                    : 'bg-slate-800 text-slate-100 rounded-tl-md border border-slate-700'
                                    }`}
                            >
                                {message.role === 'user'
                                    ? <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                                    : renderContent(message.content)
                                }
                            </div>

                            {/* Sources */}
                            {message.sources && message.sources.length > 0 && (
                                <div className={`mt-3 flex flex-wrap gap-2 ${message.role === 'user' ? 'justify-end' : ''}`}>
                                    {message.sources.map((source, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => onSelectDocument(source.id)}
                                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-full text-xs text-amber-500 hover:bg-slate-700 hover:border-amber-500/50 transition-all"
                                        >
                                            <BookOpen className="w-3 h-3" />
                                            <span className="max-w-[180px] truncate">{source.title}</span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-slate-800">
                <div className="flex gap-3 items-center bg-slate-800/50 border border-slate-700 rounded-2xl px-4 py-2 focus-within:border-amber-500/50 transition-all">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                        placeholder="Nhập câu hỏi pháp luật của bạn..."
                        className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder:text-slate-500 py-2"
                    />
                    <Button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        size="sm"
                    >
                        <Send className="w-4 h-4" />
                    </Button>
                </div>
                <p className="mt-2 text-center text-xs text-slate-600">
                    LawVina có thể mắc lỗi. Vui lòng kiểm tra thông tin quan trọng.
                </p>
            </div>
        </div>
    );
};

export default ChatPanel;
