import { FileText, ExternalLink, ChevronRight, X } from 'lucide-react';
import Button from './ui/Button';

interface ContentSection {
    type: string;
    title: string;
    content: string;
}

interface Document {
    metadata: {
        id: string;
        title: string;
        url: string;
        source?: string;  // 'vbqppl' | 'phapdien'
    };
    content: ContentSection[];
    full_content?: string;
    references?: Array<{ name: string; link: string }>;
}

interface DocumentPanelProps {
    document: Document | null;
    onClose: () => void;
}

const DocumentPanel = ({ document, onClose }: DocumentPanelProps) => {
    if (!document) {
        return (
            <div className="h-full flex flex-col items-center justify-center bg-slate-900/30 rounded-2xl border border-slate-800 border-dashed">
                <div className="text-center space-y-4 p-8">
                    <div className="w-16 h-16 mx-auto rounded-2xl bg-slate-800 flex items-center justify-center">
                        <FileText className="w-8 h-8 text-slate-600" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-400">Chưa có văn bản</h3>
                        <p className="text-sm text-slate-600 mt-1">
                            Nhấp vào nguồn trích dẫn trong cuộc trò chuyện để xem văn bản pháp luật
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    const sourceBadge = document.metadata.source === 'phapdien'
        ? { label: 'Pháp Điển', color: 'bg-emerald-500/10 text-emerald-500' }
        : { label: 'VBQPPL', color: 'bg-amber-500/10 text-amber-500' };

    return (
        <div className="h-full flex flex-col bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden animate-fade-in">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
                        <span className={`px-2 py-0.5 rounded font-medium ${sourceBadge.color}`}>
                            {sourceBadge.label}
                        </span>
                        <ChevronRight className="w-3 h-3" />
                        <span className="truncate">{document.metadata.id}</span>
                    </div>
                    <h2 className="font-semibold text-white truncate pr-4">
                        {document.metadata.title}
                    </h2>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                    <a
                        href={document.metadata.url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-amber-500 hover:bg-slate-700 transition-all"
                        title="Xem văn bản gốc"
                    >
                        <ExternalLink className="w-4 h-4" />
                    </a>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-all"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
                {document.full_content ? (
                    <div className="bg-slate-800/30 p-8 rounded-2xl border border-slate-800/50 leading-relaxed whitespace-pre-wrap text-slate-300 font-sans text-base shadow-inner">
                        {document.full_content}
                    </div>
                ) : document.content && document.content.length > 0 ? (
                    document.content.map((section, index) => {
                        const title = section.title?.toLowerCase() || '';
                        const isChapter = title.includes('chương') || title.includes('phần');
                        const isArticle = title.includes('điều') || title.startsWith('điều');

                        return (
                            <article
                                key={index}
                                className={`animate-slide-up ${isChapter ? 'pt-4' : ''}`}
                                style={{ animationDelay: `${Math.min(index * 30, 300)}ms` }}
                            >
                                <div
                                    className={`rounded-xl transition-all ${isChapter
                                        ? 'bg-amber-500/5 border border-amber-500/10 p-5'
                                        : isArticle
                                            ? 'bg-slate-800/50 border border-slate-700/50 p-5 hover:border-slate-600'
                                            : 'bg-slate-800/30 p-4 border-l-2 border-slate-700'
                                        }`}
                                >
                                    {section.title && (
                                        <h3
                                            className={`font-bold mb-3 ${isChapter
                                                ? 'text-xl text-amber-500'
                                                : isArticle
                                                    ? 'text-base text-white'
                                                    : 'text-sm text-slate-300'
                                                }`}
                                        >
                                            {section.title}
                                        </h3>
                                    )}
                                    <div
                                        className={`leading-relaxed whitespace-pre-wrap ${isChapter
                                            ? 'text-sm text-slate-400 font-medium'
                                            : 'text-sm text-slate-400'
                                            }`}
                                    >
                                        {section.content}
                                    </div>
                                </div>
                            </article>
                        );
                    })
                ) : (
                    <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                        <FileText className="w-12 h-12 mb-4 opacity-20" />
                        <p>Nội dung văn bản đang được cập nhật...</p>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-600">
                    {document.content.length} mục được tìm thấy
                </span>
                <Button variant="ghost" size="sm" onClick={() => window.scrollTo(0, 0)}>
                    Về đầu trang
                </Button>
            </div>
        </div>
    );
};

export default DocumentPanel;
