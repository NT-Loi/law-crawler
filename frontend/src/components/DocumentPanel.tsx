import { FileText, ExternalLink, ChevronRight, X } from 'lucide-react';
import Button from './ui/Button';

interface DocumentNode {
    id: number;
    doc_id: string;
    anchor: string;
    type: string;
    title: string;
    content: string;
    is_structure: boolean;
}

interface Document {
    metadata: {
        id: string;
        title: string;
        url: string;
    };
    content: DocumentNode[];
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

    return (
        <div className="h-full flex flex-col bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden animate-fade-in">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
                        <span className="px-2 py-0.5 bg-amber-500/10 text-amber-500 rounded font-medium">
                            VBQPPL
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
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
                {document.content.map((node, index) => {
                    const isChapter = node.type.includes('chuong');
                    const isArticle = node.type.includes('dieu');

                    return (
                        <article
                            key={index}
                            className={`animate-slide-up ${isChapter ? 'pt-4' : ''
                                }`}
                            style={{ animationDelay: `${index * 50}ms` }}
                        >
                            <div
                                className={`rounded-xl transition-all ${isChapter
                                        ? 'bg-amber-500/5 border border-amber-500/10 p-5'
                                        : isArticle
                                            ? 'bg-slate-800/50 border border-slate-700/50 p-5 hover:border-slate-600'
                                            : 'pl-4 border-l-2 border-slate-700'
                                    }`}
                            >
                                <h3
                                    className={`font-bold mb-3 ${isChapter
                                            ? 'text-xl text-amber-500'
                                            : isArticle
                                                ? 'text-base text-white'
                                                : 'text-sm text-slate-300'
                                        }`}
                                >
                                    {node.title}
                                </h3>
                                <div
                                    className={`leading-relaxed whitespace-pre-wrap ${isChapter
                                            ? 'text-sm text-slate-400 font-medium'
                                            : 'text-sm text-slate-400'
                                        }`}
                                >
                                    {node.content}
                                </div>
                            </div>
                        </article>
                    );
                })}
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
