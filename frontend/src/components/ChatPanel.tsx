import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, BookOpen, AlertTriangle, Database, Search, X } from 'lucide-react';
import Button from './ui/Button';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

type SourceType = 'law_db' | 'web';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: Array<{ id: string; title: string; content?: string }>;
    status?: string;
}

interface ChatPanelProps {
    onSelectDocument: (docId: string) => void;
    messages: Message[];
    onMessagesUpdate: (messages: Message[]) => void;
    conversationId: string | null;
}

const MarkdownComponents: Components = {
    p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed text-sm">{children}</p>,
    ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1 text-sm">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1 text-sm">{children}</ol>,
    li: ({ children }) => <li className="pl-1">{children}</li>,
    h1: ({ children }) => <h1 className="text-lg font-bold mb-2 text-white mt-4 first:mt-0">{children}</h1>,
    h2: ({ children }) => <h2 className="text-base font-bold mb-2 text-white mt-3 first:mt-0">{children}</h2>,
    h3: ({ children }) => <h3 className="text-sm font-bold mb-1 text-white mt-2">{children}</h3>,
    blockquote: ({ children }) => <blockquote className="border-l-2 border-amber-500 pl-4 py-1 italic text-slate-400 my-2 bg-amber-500/5 rounded-r">{children}</blockquote>,
    code: ({ node, className, children, ...props }) => {
        // @ts-ignore
        const inline = props.inline || (node && node.properties && !node.properties.className);
        return !inline ? (
            <div className="bg-slate-950/50 rounded-lg p-3 my-2 border border-slate-700 overflow-x-auto">
                <code className={`font-mono text-xs ${className}`} {...props}>
                    {children}
                </code>
            </div>
        ) : (
            <code className="bg-slate-700/50 px-1.5 py-0.5 rounded text-amber-200 font-mono text-xs" {...props}>
                {children}
            </code>
        );
    },
    a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 hover:underline">{children}</a>,
    table: ({ children }) => <div className="overflow-x-auto my-3"><table className="min-w-full divide-y divide-slate-700 border border-slate-700 rounded-lg overflow-hidden text-sm">{children}</table></div>,
    thead: ({ children }) => <thead className="bg-slate-800">{children}</thead>,
    tbody: ({ children }) => <tbody className="divide-y divide-slate-700 bg-slate-900/30">{children}</tbody>,
    tr: ({ children }) => <tr className="hover:bg-slate-800/50 transition-colors">{children}</tr>,
    th: ({ children }) => <th className="px-3 py-2 text-left text-xs font-bold text-slate-200 uppercase tracking-wider">{children}</th>,
    td: ({ children }) => <td className="px-3 py-2 whitespace-normal text-slate-300">{children}</td>,
    hr: () => <hr className="border-slate-700 my-4" />,
};

const ChatPanel = ({ onSelectDocument, messages, onMessagesUpdate, conversationId }: ChatPanelProps) => {
    const [localMessages, setLocalMessages] = useState<Message[]>(messages);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [warning, setWarning] = useState<string | null>(null);
    const [selectedSources, setSelectedSources] = useState<SourceType[]>(['law_db']); // Default to law_db
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const isStreamingRef = useRef(false);
    const lastUpdateRef = useRef(0);


    // Sync with parent when conversation changes
    useEffect(() => {
        // Only sync from parent if we are NOT currently streaming content locally.
        // This prevents the infinite loop where local usage updates parent -> parent updates props -> prop overwrites local state.
        if (!isStreamingRef.current) {
            setLocalMessages(messages);
        }
    }, [messages, conversationId]);

    // Notify parent of message changes
    useEffect(() => {
        if (localMessages !== messages) {
            onMessagesUpdate(localMessages);
        }
    }, [localMessages]);


    const toggleSource = (source: SourceType) => {
        setSelectedSources(prev => {
            if (prev.includes(source)) {
                // Don't allow removing if it's the only one
                if (prev.length === 1) return prev;
                return prev.filter(s => s !== source);
            }
            return [...prev, source];
        });
    };

    const getChatMode = (): string => {
        const hasLawDb = selectedSources.includes('law_db');
        const hasWeb = selectedSources.includes('web');
        if (hasLawDb && hasWeb) return 'hybrid';
        if (hasWeb) return 'web';
        return 'law_db';
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [localMessages, isLoading]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        isStreamingRef.current = true;

        const userMessage: Message = { role: 'user', content: input };
        setLocalMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);
        setWarning(null);

        // Create a placeholder assistant message
        setLocalMessages((prev) => [
            ...prev,
            { role: 'assistant', content: '', sources: [] },
        ]);

        try {
            const response = await fetch('http://localhost:8888/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: input,
                    history: localMessages.slice(-6),
                    mode: getChatMode(),
                }),
            });

            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            // Store all sources temporarily until we know which ones LLM actually used
            let allSources: Array<{ id: string; title: string }> = [];
            let accumulatedDelta = '';
            let usedDocsData: Array<{ id: string; title: string; content?: string }> | null = null;
            let currentStatus = '';


            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep the incomplete line in buffer

                let usedDocIds: string[] | null = null;
                let currentBatchUsedDocs: typeof usedDocsData = null;

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);

                        if (data.type === 'sources') {
                            // Store sources but don't display yet
                            allSources = data.data;
                            console.log('Stored sources (not displayed yet):', allSources.length);
                        } else if (data.type === 'content') {
                            accumulatedDelta += data.delta;
                        } else if (data.type === 'warning') {
                            setWarning(data.message);
                        } else if (data.type === 'used_docs') {
                            // LLM returned which docs it actually used
                            if (data.data) {
                                currentBatchUsedDocs = data.data;
                            } else {
                                usedDocIds = data.ids;
                            }
                            console.log('LLM used these docs:', data);
                        } else if (data.type === 'status') {
                            currentStatus = data.message;
                        }

                    } catch (e) {
                        console.error('Error parsing JSON chunk', e);
                    }
                }

                if (accumulatedDelta || usedDocIds || currentBatchUsedDocs || currentStatus) {
                    const now = Date.now();
                    // Throttle updates to every 30ms to prevent React render thrashing
                    // checking !done is not available here easily (infinite loop), but usedDocIds implies end or important event
                    if (now - lastUpdateRef.current > 30 || usedDocIds || currentBatchUsedDocs || currentStatus) {
                        setLocalMessages((prev) => {
                            const newMessages = [...prev];
                            const lastIndex = newMessages.length - 1;
                            newMessages[lastIndex] = { ...newMessages[lastIndex] };

                            if (accumulatedDelta) {
                                newMessages[lastIndex].content += accumulatedDelta;
                                // Clear status once we start receiving content
                                newMessages[lastIndex].status = undefined;
                            }

                            if (currentStatus) {
                                newMessages[lastIndex].status = currentStatus;
                            }

                            if (currentBatchUsedDocs) {
                                newMessages[lastIndex].sources = currentBatchUsedDocs;
                            } else if (usedDocIds && usedDocIds.length > 0) {
                                // Build sources directly from used_docs IDs using allSources
                                const sourcesMap = new Map(allSources.map(s => [s.id, s]));
                                newMessages[lastIndex].sources = usedDocIds.map(id =>
                                    sourcesMap.get(id) || { id, title: id }
                                );
                            }


                            return newMessages;
                        });

                        // Clear accumulated delta after flushing to state
                        lastUpdateRef.current = now;
                        accumulatedDelta = '';
                        currentStatus = '';
                    }
                    // If we didn't update state, we keep accumulatedDelta growing for the next loop
                }
            }

            // Final flush if there is any leftover text after the loop finishes
            if (accumulatedDelta) {
                setLocalMessages((prev) => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    const updatedMsg = { ...lastMsg, content: lastMsg.content + accumulatedDelta };
                    newMessages[newMessages.length - 1] = updatedMsg;
                    return newMessages;
                });
            }

        } catch (error) {
            setLocalMessages((prev) => {
                const newMessages = [...prev];
                const lastMsg = newMessages[newMessages.length - 1];
                lastMsg.content += '\n\n[Lỗi kết nối: Không thể nhận phản hồi từ AI]';
                return newMessages;
            });
        } finally {
            setIsLoading(false);
            isStreamingRef.current = false;
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
                    {beforeThink && (
                        <div className="markdown-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                                {beforeThink}
                            </ReactMarkdown>
                        </div>
                    )}

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

                    {afterThink && (
                        <div className="markdown-content animate-fade-in">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                                {afterThink}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            );
        }

        return (
            <div className="markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={MarkdownComponents}>
                    {content}
                </ReactMarkdown>
            </div>
        );
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
                {localMessages.map((message, index) => (
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
                                    : (
                                        <>
                                            {message.status && (
                                                <div className="flex items-center gap-2 mb-3 py-1 px-3 bg-slate-900/50 rounded-lg border border-slate-700/50 text-xs font-medium text-amber-500 animate-pulse">
                                                    <span className="relative flex h-2 w-2">
                                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                                                    </span>
                                                    {message.status}
                                                </div>
                                            )}
                                            {renderContent(message.content || '')}
                                        </>
                                    )
                                }
                            </div>

                            {/* Sources */}
                            {message.sources && message.sources.length > 0 && (
                                <div className={`mt-3 flex flex-wrap gap-2 ${message.role === 'user' ? 'justify-end' : ''}`}>
                                    {message.sources.map((source) => (
                                        <button
                                            key={source.id}
                                            onClick={() => onSelectDocument(source.id)}
                                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-full text-xs text-amber-500 hover:bg-slate-700 hover:border-amber-500/50 transition-all"
                                        >
                                            <BookOpen className="w-3 h-3" />
                                            <span className="max-w-[200px] truncate">{source.title || source.id}</span>
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
                {warning && (
                    <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3 animate-slide-up">
                        <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                        <div className="flex-1">
                            <h3 className="text-xs font-bold text-amber-500 uppercase tracking-wide mb-1">Cảnh báo giới hạn</h3>
                            <p className="text-sm text-amber-200/80 leading-relaxed">
                                {warning}
                            </p>
                        </div>
                        <button
                            onClick={() => setWarning(null)}
                            className="text-amber-500/50 hover:text-amber-500 transition-colors"
                        >
                            <span className="sr-only">Close</span>
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                )}

                {/* Source Selection Tags */}
                <div className="flex items-center gap-2 mb-3 flex-wrap">
                    <span className="text-xs text-slate-500 mr-1">Nguồn:</span>

                    {/* Law Database Tag */}
                    <button
                        onClick={() => toggleSource('law_db')}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${selectedSources.includes('law_db')
                            ? 'bg-blue-100 text-blue-700 border border-blue-200'
                            : 'bg-slate-700 text-slate-400 border border-slate-600 hover:bg-slate-600'
                            }`}
                    >
                        <Database className="w-3.5 h-3.5" />
                        <span>Kho VBQPPL</span>
                        {selectedSources.includes('law_db') && selectedSources.length > 1 && (
                            <X className="w-3 h-3 text-red-500 hover:text-red-600 ml-0.5" />
                        )}
                    </button>

                    {/* Web Search Tag */}
                    <button
                        onClick={() => toggleSource('web')}
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${selectedSources.includes('web')
                            ? 'bg-blue-100 text-blue-700 border border-blue-200'
                            : 'bg-slate-700 text-slate-400 border border-slate-600 hover:bg-slate-600'
                            }`}
                    >
                        <Search className="w-3.5 h-3.5" />
                        <span>Google</span>
                        {selectedSources.includes('web') && selectedSources.length > 1 && (
                            <X className="w-3 h-3 text-red-500 hover:text-red-600 ml-0.5" />
                        )}
                    </button>
                </div>

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
