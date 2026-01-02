import { Scale, MessageSquare, Settings, HelpCircle } from 'lucide-react';

interface SidebarProps {
    activeTab: 'chat' | 'documents';
    onTabChange: (tab: 'chat' | 'documents') => void;
}

const Sidebar = ({ activeTab, onTabChange }: SidebarProps) => {
    const navItems = [
        { id: 'chat' as const, icon: MessageSquare, label: 'Trợ lý AI' },
        // { id: 'documents' as const, icon: FileText, label: 'Văn bản' }, // Hidden as requested
    ];

    return (
        <aside className="w-20 lg:w-64 h-full bg-slate-900 border-r border-slate-800 flex flex-col">
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

            {/* Navigation */}
            <nav className="flex-1 p-3 lg:p-4 space-y-2">
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
