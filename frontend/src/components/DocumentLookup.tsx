import React, { useState } from 'react';
import { Search, FileText, ArrowRight } from 'lucide-react';

interface DocumentLookupProps {
    onSelectDocument: (docId: string) => void;
}

const DocumentLookup: React.FC<DocumentLookupProps> = ({ onSelectDocument }) => {
    const [docId, setDocId] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (docId.trim()) {
            onSelectDocument(docId.trim());
        }
    };

    return (
        <div className="flex flex-col h-full items-center justify-center p-6 bg-slate-900/50">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center space-y-2">
                    <div className="mx-auto w-16 h-16 bg-amber-500/10 rounded-2xl flex items-center justify-center mb-6 ring-1 ring-amber-500/20">
                        <FileText className="w-8 h-8 text-amber-500" />
                    </div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">Tra cứu văn bản</h2>
                    <p className="text-slate-400">
                        Nhập số hiệu văn bản hoặc ID để xem nội dung chi tiết
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="relative">
                    <div className="relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-amber-500/20 to-amber-600/20 rounded-xl blur opacity-0 group-hover:opacity-100 transition duration-500" />
                        <div className="relative flex shadow-xl">
                            <div className="relative flex-1">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                                <input
                                    type="text"
                                    value={docId}
                                    onChange={(e) => setDocId(e.target.value)}
                                    placeholder="Ví dụ: 15/2012/TT-BGTVT..."
                                    className="w-full bg-slate-900 border-y border-l border-slate-700 rounded-l-xl py-4 pl-12 pr-4 text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50 transition-all font-medium"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={!docId.trim()}
                                className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed text-slate-900 font-bold px-6 rounded-r-xl transition-all flex items-center gap-2 hover:shadow-[0_0_20px_rgba(245,158,11,0.3)]"
                            >
                                <span>Xem</span>
                                <ArrowRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </form>

                <div className="text-center">
                    <p className="text-xs text-slate-600">
                        Hỗ trợ tra cứu VBQPPL và Pháp điển
                    </p>
                </div>
            </div>
        </div>
    );
};

export default DocumentLookup;
