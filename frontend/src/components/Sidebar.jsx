import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Trash2, Layers, HardDrive, CheckSquare, Square, AlertCircle } from 'lucide-react';

export default function Sidebar({
  documents,
  selectedDocIds,
  onToggleSelectDoc,
  onUploadFile,
  onDeleteDoc,
  isUploading,
  uploadError
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      onUploadFile(file);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onUploadFile(e.target.files[0]);
      e.target.value = '';
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <aside className="w-80 h-full bg-slate-900 border-r border-slate-800 flex flex-col justify-between select-none">
      {/* App Header */}
      <div className="p-4 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/30">
          <Layers className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-base text-slate-100 tracking-tight">DocuRAG</h1>
          <p className="text-[11px] text-slate-400">Production PDF Q&A Pipeline</p>
        </div>
      </div>

      {/* Upload Zone & Documents List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Upload Box */}
        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
            Ingest Document
          </label>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all ${
              isDragOver
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-slate-700 hover:border-slate-600 bg-slate-950/50'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,application/pdf"
              className="hidden"
            />
            <div className="flex flex-col items-center space-y-2">
              <div className="w-10 h-10 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                <UploadCloud className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-slate-200">
                  {isUploading ? 'Ingesting PDF...' : 'Click or Drag PDF here'}
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">Max 15MB · PDF format only</p>
              </div>
            </div>
          </div>

          {uploadError && (
            <div className="mt-2.5 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-start space-x-2 animate-fade-in">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{uploadError}</span>
            </div>
          )}
        </div>

        {/* Documents List */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Documents ({documents.length})
            </span>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
              No PDFs uploaded yet.
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => {
                const isSelected = selectedDocIds.includes(doc.document_id);
                return (
                  <div
                    key={doc.document_id}
                    className={`p-3 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-slate-800/90 border-indigo-500/50 shadow-md shadow-indigo-950/30'
                        : 'bg-slate-950/40 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-2.5 min-w-0 pr-2">
                        <button
                          onClick={() => onToggleSelectDoc(doc.document_id)}
                          className="mt-0.5 text-indigo-400 hover:text-indigo-300 focus:outline-none"
                          title="Toggle search scope"
                        >
                          {isSelected ? (
                            <CheckSquare className="w-4 h-4 text-indigo-400" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-600" />
                          )}
                        </button>
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-slate-200 truncate" title={doc.document_name}>
                            {doc.document_name}
                          </p>
                          <div className="flex items-center space-x-2 mt-1 text-[10px] text-slate-400 font-mono">
                            <span>{doc.page_count} pgs</span>
                            <span>·</span>
                            <span>{doc.chunk_count} chunks</span>
                            <span>·</span>
                            <span>{formatBytes(doc.file_size_bytes)}</span>
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => onDeleteDoc(doc.document_id)}
                        className="text-slate-500 hover:text-rose-400 transition-colors p-1 rounded hover:bg-slate-800"
                        title="Delete document"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <HardDrive className="w-3.5 h-3.5 text-slate-400" />
          <span>Vector DB: ChromaDB</span>
        </div>
        <span className="font-mono text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-indigo-400">
          MiniLM-L6-v2
        </span>
      </div>
    </aside>
  );
}
