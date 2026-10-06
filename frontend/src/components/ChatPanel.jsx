import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BookOpen, AlertCircle, RefreshCw, Cpu, CheckCircle2 } from 'lucide-react';
import PassageAccordion from './PassageAccordion';

export default function ChatPanel({
  messages,
  onSendMessage,
  isLoading,
  hasDocuments,
  llmProvider,
  onClearChat
}) {
  const [inputQuestion, setInputQuestion] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputQuestion.trim() || isLoading) return;
    onSendMessage(inputQuestion.trim());
    setInputQuestion('');
  };

  return (
    <main className="flex-1 h-full flex flex-col bg-slate-950">
      {/* Top Bar */}
      <header className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/50 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <span>LLM Provider:</span>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 capitalize font-mono text-[11px]">
              {llmProvider || 'gemini'}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>RAG Engine Ready</span>
          </div>
          <button
            onClick={onClearChat}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center space-x-1 hover:bg-slate-800 px-2 py-1 rounded transition-colors"
            title="Clear Chat History"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4 text-slate-400">
            <div className="w-14 h-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shadow-inner">
              <Bot className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-200">PDF Question Answering RAG</h2>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Upload your research papers, legal contracts, or technical manuals on the sidebar.
                Ask any question and receive strictly grounded answers with page-level citations.
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex items-start space-x-3.5 max-w-3xl ${
                msg.role === 'user' ? 'ml-auto flex-row-reverse space-x-reverse' : ''
              } animate-fade-in`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-white ${
                  msg.role === 'user' ? 'bg-indigo-600' : 'bg-slate-800 border border-slate-700'
                }`}
              >
                {msg.role === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4 text-indigo-400" />
                )}
              </div>

              {/* Message Content Bubble */}
              <div className="flex-1 min-w-0">
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-none shadow-md shadow-indigo-950/20'
                      : 'bg-slate-900 border border-slate-800 text-slate-100 rounded-tl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Sources List if available */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap gap-1.5 items-center">
                      <span className="text-[11px] font-semibold text-slate-400 flex items-center space-x-1 mr-1">
                        <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Sources:</span>
                      </span>
                      {msg.sources.map((src, sIdx) => (
                        <span
                          key={sIdx}
                          className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-[11px] font-mono"
                        >
                          {src.document_name} · Pg {src.page_number}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Collapsible Passages Accordion */}
                {msg.role === 'assistant' && msg.passages && (
                  <PassageAccordion passages={msg.passages} />
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading skeleton indicator */}
        {isLoading && (
          <div className="flex items-start space-x-3 max-w-xl animate-pulse">
            <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-indigo-400">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 text-xs flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></span>
              <span>Searching vector embeddings & generating grounded response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Area */}
      <footer className="p-4 border-t border-slate-800 bg-slate-900/60 backdrop-blur-md">
        {!hasDocuments && (
          <div className="mb-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>Please upload at least one PDF document before asking questions.</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex items-center space-x-3">
          <input
            type="text"
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            placeholder={
              hasDocuments
                ? 'Ask a question about your uploaded documents...'
                : 'Upload a PDF to start asking questions...'
            }
            disabled={!hasDocuments || isLoading}
            className="flex-1 bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!hasDocuments || !inputQuestion.trim() || isLoading}
            className="w-11 h-11 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white flex items-center justify-center transition-colors shadow-lg shadow-indigo-600/30 flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </footer>
    </main>
  );
}
