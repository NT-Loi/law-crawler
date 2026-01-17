import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, FileText, ExternalLink, Scale } from 'lucide-react';

interface DocMetadata {
    id: string;
    title: string;
    doc_number?: string;
    url: string;
    doc_date?: string;
}

interface DocumentLibraryProps {
    onSelectDocument: (docId: string) => void;
}

const DocumentLibrary: React.FC<DocumentLibraryProps> = ({ onSelectDocument }) => {
    const [documents, setDocuments] = useState<DocMetadata[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const fetchDocuments = async (query: string = '') => {
        setIsLoading(true);
        try {
            const response = await axios.get(`http://localhost:8888/documents`, {
                params: { q: query, limit: 50 },
                headers: {
                    'ngrok-skip-browser-warning': 'true'
                }
            });
            setDocuments(response.data);
        } catch (error) {
            console.error('Failed to fetch documents:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        fetchDocuments(searchQuery);
    };

    return (
        <div className="flex flex-col h-full bg-slate-900/50 rounded-2xl border border-slate-800 backdrop-blur-sm overflow-hidden">
            {/* Header / Search */}
            <div className="p-6 border-b border-slate-800 bg-slate-900/80">
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-amber-500/10 rounded-lg">
                        <Scale className="w-5 h-5 text-amber-500" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">Thư viện Văn bản</h2>
                        <p className="text-sm text-slate-400">Tra cứu và xem nguyên văn các văn bản pháp luật</p>
                    </div>
                </div>

                <form onSubmit={handleSearch} className="relative">
                    <input
                        type="text"
                        placeholder="Tìm kiếm theo tiêu đề hoặc số hiệu văn bản..."
                        className="w-full bg-slate-950/50 border border-slate-700 text-white rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500/50 transition-all placeholder:text-slate-600"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                </form>
            </div>

            {/* Results List */}
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center h-full space-y-4">
                        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                        <p className="text-slate-500 font-medium">Đang tải danh sách văn bản...</p>
                    </div>
                ) : documents.length > 0 ? (
                    <div
                        className="grid gap-4"
                        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}
                    >
                        {documents.map((doc) => (
                            <div
                                key={doc.id}
                                onClick={() => onSelectDocument(doc.id)}
                                className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-4 cursor-pointer hover:bg-slate-800/50 hover:border-amber-500/30 transition-all group relative overflow-hidden flex flex-col h-full"
                                title={doc.title}
                            >
                                {/* Accent Glow */}
                                <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 blur-3xl rounded-full translate-x-16 -translate-y-16 group-hover:bg-amber-500/10 transition-colors" />

                                <div className="flex items-start justify-between mb-3">
                                    <div className="p-2 bg-slate-900 rounded-lg group-hover:bg-amber-500/10 transition-colors">
                                        <FileText className="w-5 h-5 text-slate-500 group-hover:text-amber-500 transition-colors" />
                                    </div>
                                    {doc.url && (
                                        <a
                                            href={doc.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={(e) => e.stopPropagation()}
                                            className="p-1.5 hover:bg-slate-700 rounded-lg text-slate-500 hover:text-slate-300 transition-colors"
                                            title="Xem bản gốc"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                        </a>
                                    )}
                                </div>

                                <h3 className="text-white font-semibold text-base line-clamp-3 mb-3 group-hover:text-amber-500 transition-colors flex-1">
                                    {doc.title}
                                </h3>

                                <div className="flex flex-col gap-2 text-xs text-slate-400 mt-auto border-t border-slate-700/50 pt-3">
                                    <span className="font-medium text-slate-300">
                                        {doc.doc_number || doc.id}
                                    </span>
                                    {doc.doc_date && (
                                        <span className="flex items-center gap-1.5 opacity-75">
                                            Ban hành: {new Date(doc.doc_date).toLocaleDateString('vi-VN')}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full py-20 text-center">
                        <div className="p-4 bg-slate-900 rounded-full mb-4">
                            <Search className="w-10 h-10 text-slate-700" />
                        </div>
                        <h3 className="text-white font-semibold text-lg">Không tìm thấy văn bản nào</h3>
                        <p className="text-slate-500 mt-1 max-w-sm">
                            Hãy thử tìm kiếm với từ khóa khác hoặc kiểm tra lại số hiệu văn bản.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DocumentLibrary;
