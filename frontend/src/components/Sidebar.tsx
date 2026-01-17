import { Scale, MessageSquare, Settings, HelpCircle, Plus, Trash2, FileText } from 'lucide-react';
import type { Conversation } from '../App';

interface SidebarProps {
    activeTab: 'chat' | 'documents';
    onTabChange: (tab: 'chat' | 'documents') => void;
    conversations: Conversation[];
    activeConversationId: string | null;
    onNewConversation: () => void;
    onSelectConversation: (id: string) => void;
    onDeleteConversation: (id: string) => void;
}

const Sidebar = ({
    activeTab,
    onTabChange,
    conversations,
    activeConversationId,
    onNewConversation,
    onSelectConversation,
    onDeleteConversation,
}: SidebarProps) => {
    const navItems = [
        { id: 'chat' as const, icon: MessageSquare, label: 'Trợ lý AI' },
    ];

    const formatTime = (timestamp: number) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return 'Hôm qua';
        } else if (diffDays < 7) {
            return `${diffDays} ngày trước`;
        } else {
            return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
        }
    };

    return (
        <aside className="w-20 lg:w-72 h-full bg-slate-900 border-r border-slate-800 flex flex-col">
            {/* Logo Section */}
            <div className="p-4 lg:p-6 border-b border-slate-800">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 lg:w-12 lg:h-12 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg">
                        <Scale className="w-5 h-5 lg:w-6 lg:h-6 text-slate-900" />
                    </div>
                    <div className="hidden lg:block">
                        <h1 className="text-xl font-bold text-white tracking-tight">
                            Law<span className="text-gradient-gold">Vina</span>
                        </h1>
                        <p className="text-[10px] text-slate-500 font-medium tracking-widest uppercase">
                            Legal AI Assistant
                        </p>
                    </div>
                </div>
            </div>

            {/* New Chat Button */}
            <div className="p-3 lg:p-4 space-y-2">
                <button
                    onClick={onNewConversation}
                    className="w-full flex items-center justify-center lg:justify-start gap-2 px-3 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-900 font-medium text-sm transition-all"
                >
                    <Plus className="w-5 h-5" />
                    <span className="hidden lg:block">Cuộc trò chuyện mới</span>
                </button>

                <button
                    onClick={() => onTabChange('documents')}
                    className={`w-full flex items-center justify-center lg:justify-start gap-2 px-3 py-2.5 rounded-xl border font-medium text-sm transition-all ${activeTab === 'documents'
                        ? 'bg-slate-800 border-amber-500/50 text-amber-500'
                        : 'border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                        }`}
                >
                    <FileText className="w-5 h-5" />
                    <span className="hidden lg:block">Tra cứu văn bản</span>
                </button>
            </div>

            {/* Conversation History */}
            <div className="flex-1 overflow-y-auto px-3 lg:px-4 pb-2">
                <div className="hidden lg:block text-xs text-slate-500 font-medium uppercase tracking-wide mb-2 px-1">
                    Lịch sử
                </div>
                <div className="space-y-1">
                    {conversations.map((conv) => {
                        const isActive = conv.id === activeConversationId;

                        return (
                            <div
                                key={conv.id}
                                className={`group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${isActive
                                    ? 'bg-slate-800 text-white'
                                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                                    }`}
                                onClick={() => onSelectConversation(conv.id)}
                            >
                                <MessageSquare className="w-4 h-4 shrink-0" />
                                <div className="hidden lg:flex flex-1 min-w-0 items-center justify-between gap-2">
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium truncate">{conv.title}</div>
                                        <div className="text-xs text-slate-500 truncate">
                                            {formatTime(conv.updatedAt)}
                                        </div>
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDeleteConversation(conv.id);
                                        }}
                                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-slate-700 text-slate-500 hover:text-red-400 transition-all"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Navigation Tabs (hidden in favor of conversation list) */}
            <nav className="hidden p-3 lg:p-4 space-y-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;

                    return (
                        <button
                            key={item.id}
                            onClick={() => onTabChange(item.id)}
                            className={`
                w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200
                ${isActive
                                    ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                                }
              `}
                        >
                            <Icon className="w-5 h-5 shrink-0" />
                            <span className="hidden lg:block font-medium text-sm">{item.label}</span>
                        </button>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="p-3 lg:p-4 border-t border-slate-800 space-y-2">
                <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-all">
                    <Settings className="w-5 h-5 shrink-0" />
                    <span className="hidden lg:block text-sm">Cài đặt</span>
                </button>
                <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-all">
                    <HelpCircle className="w-5 h-5 shrink-0" />
                    <span className="hidden lg:block text-sm">Trợ giúp</span>
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
