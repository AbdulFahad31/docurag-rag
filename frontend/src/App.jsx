import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import {
  fetchHealth,
  fetchDocuments,
  uploadDocument,
  deleteDocument,
  sendChatMessage
} from './api/client';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [llmProvider, setLlmProvider] = useState('gemini');

  // Load initial health status & document list
  useEffect(() => {
    loadHealth();
    loadDocuments();
  }, []);

  const loadHealth = async () => {
    try {
      const data = await fetchHealth();
      if (data.llm_provider) {
        setLlmProvider(data.llm_provider);
      }
    } catch (err) {
      console.warn('Health check warning:', err.message);
    }
  };

  const loadDocuments = async () => {
    try {
      const data = await fetchDocuments();
      if (data && data.documents) {
        setDocuments(data.documents);
      }
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  const handleUploadFile = async (file) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      await uploadDocument(file);
      await loadDocuments();
    } catch (err) {
      setUploadError(err.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDoc = async (documentId) => {
    try {
      await deleteDocument(documentId);
      setSelectedDocIds((prev) => prev.filter((id) => id !== documentId));
      await loadDocuments();
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const handleToggleSelectDoc = (documentId) => {
    setSelectedDocIds((prev) =>
      prev.includes(documentId)
        ? prev.filter((id) => id !== documentId)
        : [...prev, documentId]
    );
  };

  const handleSendMessage = async (question) => {
    // Append user message
    const userMsg = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const docIdsFilter = selectedDocIds.length > 0 ? selectedDocIds : null;
      const res = await sendChatMessage(question, docIdsFilter);

      const assistantMsg = {
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        passages: res.passages,
        has_grounded_answer: res.has_grounded_answer
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to get answer.'}`,
        sources: [],
        passages: []
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  return (
    <div className="app-container">
      <Sidebar
        documents={documents}
        selectedDocIds={selectedDocIds}
        onToggleSelectDoc={handleToggleSelectDoc}
        onUploadFile={handleUploadFile}
        onDeleteDoc={handleDeleteDoc}
        isUploading={isUploading}
        uploadError={uploadError}
      />
      <ChatPanel
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        hasDocuments={documents.length > 0}
        llmProvider={llmProvider}
        onClearChat={handleClearChat}
      />
    </div>
  );
}
