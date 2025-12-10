import React, { useEffect, useState, useRef } from 'react';
import { Post } from '../data/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface Citation {
  title?: string;
  uri?: string;
  text?: string;
}

interface ChatItem {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

const PracticeRAG: React.FC = () => {
  const [serviceReady, setServiceReady] = useState<boolean>(false);
  const [storeInfo, setStoreInfo] = useState<any>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [postsLoading, setPostsLoading] = useState(true);
  const [postQuery, setPostQuery] = useState('');
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [message, setMessage] = useState('');
  const [metadataFilter, setMetadataFilter] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [metadataJson, setMetadataJson] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [fileInputRef, setFileInputRef] = useState<HTMLInputElement | null>(null);
  const token = localStorage.getItem('token') || '';
  const endRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); };

  useEffect(() => { loadStatus(); }, []);
  useEffect(() => { loadPosts(); }, []);

  const loadStatus = async () => {
    try {
      const s = await fetch('/api/rag/status');
      if (s.ok) {
        const status = await s.json();
        setServiceReady(Boolean(status.configured) || Boolean(status.store_name));
        await Promise.all([loadStoreInfo(), loadFiles()]);
      } else {
        setServiceReady(false);
      }
    } catch {
      setServiceReady(false);
    }
  };

  const loadStoreInfo = async () => {
    const res = await fetch('/api/rag/store-info');
    if (res.ok) setStoreInfo(await res.json());
  };

  const loadFiles = async () => {
    const res = await fetch('/api/rag/files');
    if (res.ok) {
      const data = await res.json();
      setFiles(data.files || []);
    }
  };

  const loadPosts = async () => {
    setPostsLoading(true);
    try {
      const res = await fetch('/api/posts?page=1&page_size=50');
      if (res.ok) {
        const payload = await res.json();
        const items = Array.isArray(payload) ? payload : (payload?.data || []);
        const mapped: Post[] = items.map((p: any) => ({
          id: p.id,
          title: p.title,
          author: p.author || '',
          date: p.date,
          subject: p.subject,
          category: p.category,
          description: p.description || '',
          views: p.views || 0,
          downloads: p.downloads || 0,
          comments: 0,
          fileUrl: p.file_url || p.fileUrl
        }));
        setPosts(mapped.filter(p => !!p.fileUrl));
      }
    } finally {
      setPostsLoading(false);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const uploadFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setIsUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      if (metadataJson) fd.append('metadata', metadataJson);
      const res = await fetch('/api/rag/upload', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: fd,
      });
      if (res.ok) {
        await Promise.all([loadStoreInfo(), loadFiles()]);
        setFile(null);
        if (fileInputRef) fileInputRef.value = '';
      } else {
        alert('Tải lên thất bại hoặc chưa cấu hình RAG');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = message.trim();
    if (!text) return;
    setIsSending(true);
    const userItem: ChatItem = { role: 'user', content: text };
    setMessages(prev => [...prev, userItem]);
    setMessage('');
    try {
      const res = await fetch('/api/rag/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, metadata_filter: metadataFilter, system_prompt: systemPrompt })
      });
      if (res.ok) {
        const data = await res.json();
        const assistant: ChatItem = { role: 'assistant', content: data.response || '', citations: data.metadata?.citations };
        setMessages(prev => [...prev, assistant]);
        scrollToBottom();
      } else {
        alert('Chat thất bại. Vui lòng tải lên tài liệu hoặc cấu hình RAG.');
      }
    } finally {
      setIsSending(false);
    }
  };

  const clearConversation = async () => {
    const res = await fetch('/api/rag/clear', { method: 'POST' });
    if (res.ok) setMessages([]);
  };

  const deleteStore = async () => {
    const res = await fetch('/api/rag/delete-store', { method: 'DELETE', headers: token ? { Authorization: `Bearer ${token}` } : undefined });
    if (res.ok) {
      setStoreInfo(null);
      setFiles([]);
    }
  };

  const deleteFile = async (index: number) => {
    const res = await fetch(`/api/rag/delete-file/${index}`, { method: 'DELETE', headers: token ? { Authorization: `Bearer ${token}` } : undefined });
    if (res.ok) await loadFiles();
  };

  const extractDriveId = (url: string): string | null => {
    try {
      const u = new URL(url);
      if (!u.hostname.includes('drive.google.com') && !u.hostname.includes('docs.google.com')) return null;
      const idParam = u.searchParams.get('id');
      if (idParam) return idParam;
      const pathMatch = url.match(/\/file\/d\/([a-zA-Z0-9_-]+)/);
      if (pathMatch) return pathMatch[1];
      return null;
    } catch {
      return null;
    }
  };

  const importFromPost = async (post: Post) => {
    if (!post.fileUrl) return;
    if (files.length >= 5) return;

    // Check for Google Drive URL
    const driveId = extractDriveId(post.fileUrl);
    if (driveId) {
      try {
        const downloadUrl = `https://drive.google.com/uc?export=download&id=${driveId}`;
        const res = await fetch('/api/rag/import-url', {
          method: 'POST',
          headers: token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: downloadUrl,
            filename: sanitizeFilename(post.title) + '.pdf', // Assume PDF for Google Drive books
            metadata: JSON.stringify({ subject: post.subject, title: post.title }),
            chunking_config: JSON.stringify({ enabled: true, max_tokens_per_chunk: 200, max_overlap_tokens: 20 })
          })
        });

        if (res.ok) {
          await loadFiles();
        } else {
          const err = await res.json().catch(() => ({}));
          alert('Không thể thêm tài liệu từ Google Drive: ' + (err?.detail || 'Lỗi không xác định'));
        }
      } catch (e) {
        alert('Lỗi khi thêm tài liệu từ Google Drive');
      }
      return;
    }

    try {
      const cacheRes = await fetch('/api/files/cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: post.fileUrl, filename: sanitizeFilename(post.title) })
      });
      if (!cacheRes.ok) {
        const err = await cacheRes.json().catch(() => ({}));
        alert('Không thể cache tài liệu: ' + (err?.detail || 'Lỗi không xác định'));
        return;
      }
      const cached = await cacheRes.json();
      const localUrl = cached.local_url as string;
      const res = await importLocalUrlToRag(localUrl, post, token || undefined);
      if (res.ok) {
        await loadFiles();
      } else {
        const err = await res.json().catch(() => ({}));
        alert('Không thể thêm tài liệu: ' + (err?.detail || 'Lỗi không xác định'));
      }
    } catch (e) {
      alert('Không thể tải tài liệu từ website. Vui lòng thử tài liệu khác.');
    }
  };

  return (
    <div className="w-full h-full bg-white">
      <div className="h-full flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex-shrink-0">
          <h2 className="text-2xl font-bold text-gray-900">Luyện tập cùng NeuraViet AI</h2>
        </div>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 p-4 overflow-hidden min-h-0">
          <div className="lg:col-span-1 space-y-3 overflow-y-auto pr-2">
            <div className="border border-gray-200 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-900 text-base">Kho tài liệu</h3>
                <span className={`text-xs px-2 py-1 rounded ${serviceReady ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{serviceReady ? 'Sẵn sàng' : 'Chưa cấu hình'}</span>
              </div>
              <div className="text-sm text-gray-600">
                {storeInfo?.store_exists ? (
                  <div className="space-y-0.5">
                    <div>Tên: {storeInfo.name}</div>
                    <div>Tài liệu: {storeInfo.document_count}</div>
                    <button onClick={deleteStore} className="mt-1.5 text-red-600 hover:text-red-800 text-xs px-2 py-0.5 rounded-md bg-red-100 hover:bg-red-200">Xóa kho</button>
                  </div>
                ) : (
                  <div>Chưa có kho. Vui lòng tải lên tài liệu.</div>
                )}
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-3">
              <h3 className="font-semibold text-gray-900 mb-3 text-base">Tải lên tài liệu</h3>

              {/* Drag and Drop Zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef?.click()}
                className={`relative border-2 border-dashed rounded-lg p-5 mb-3 cursor-pointer transition-all duration-200 ${isDragging
                    ? 'border-blue-500 bg-blue-50'
                    : file
                      ? 'border-green-400 bg-green-50'
                      : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
                  }`}
              >
                <input
                  ref={(el) => setFileInputRef(el)}
                  type="file"
                  onChange={handleFileInputChange}
                  className="hidden"
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.rtf,.odt,.ods,.odp"
                />
                <div className="flex flex-col items-center justify-center text-center">
                  <div className={`mb-3 ${isDragging || file ? 'text-blue-600' : 'text-gray-400'}`}>
                    <svg
                      className="w-12 h-12 mx-auto"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                  </div>
                  {file ? (
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-gray-900">{file.name}</p>
                      <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
                      <p className="text-xs text-blue-600 mt-2">Nhấp để chọn file khác</p>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm font-medium text-gray-700 mb-1">
                        Kéo thả file vào đây hoặc nhấp để chọn file
                      </p>
                      <p className="text-xs text-gray-500 mt-2">
                        Hỗ trợ: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, RTF, ODT, ODS, ODP
                      </p>
                    </>
                  )}
                </div>
              </div>

              {/* Metadata and Upload Button */}
              <form onSubmit={uploadFile} className="space-y-2">
                <textarea
                  placeholder="Metadata JSON (tùy chọn)"
                  value={metadataJson}
                  onChange={(e) => setMetadataJson(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                />
                <button
                  type="submit"
                  disabled={isUploading || !file || files.length >= 5}
                  className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium transition-colors"
                >
                  {isUploading ? 'Đang tải...' : 'Tải lên'}
                </button>
                {files.length >= 5 && (
                  <p className="text-xs text-red-600 text-center">Đã đạt giới hạn 5 tài liệu</p>
                )}
              </form>

              {/* File List */}
              <div className="mt-3">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-800 text-sm">Danh sách tài liệu</h4>
                  <span className="text-xs text-gray-500">Đã tải: {Math.min(files.length, 5)}/5</span>
                </div>
                <ul className="space-y-1.5 text-sm max-h-32 overflow-y-auto">
                  {files.length === 0 && <li className="text-gray-500 text-sm py-1">Chưa có tài liệu</li>}
                  {files.map((f, idx) => (
                    <li key={idx} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                      <div className="truncate flex-1 mr-2 text-sm">{f.filename} • {Math.round((f.size || 0) / 1024)}KB</div>
                      <button
                        onClick={() => deleteFile(idx)}
                        className="text-red-600 hover:text-red-800 text-sm flex-shrink-0 font-medium"
                      >
                        Xóa
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-3">
              <h3 className="font-semibold text-gray-900 mb-2 text-base">Chọn từ website</h3>
              <input
                value={postQuery}
                onChange={(e) => setPostQuery(e.target.value)}
                placeholder="Tìm nhanh theo tiêu đề/môn/mô tả..."
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm mb-2"
              />
              {postsLoading ? (
                <div className="text-sm text-gray-500">Đang tải...</div>
              ) : (
                <ul className="space-y-1 text-sm max-h-48 overflow-y-auto">
                  {posts
                    .filter((p) => {
                      const q = postQuery.trim().toLowerCase();
                      if (!q) return true;
                      return (
                        (p.title || '').toLowerCase().includes(q) ||
                        (p.subject || '').toLowerCase().includes(q) ||
                        (p.description || '').toLowerCase().includes(q)
                      );
                    })
                    .slice(0, 50)
                    .map((p) => (
                      <li key={p.id} className="flex items-center justify-between gap-1">
                        <div className="truncate flex-1 text-sm">{p.title}</div>
                        <button
                          disabled={files.length >= 5}
                          onClick={() => importFromPost(p)}
                          className={`text-sm px-2 py-1 rounded-md flex-shrink-0 ${files.length >= 5 ? 'bg-gray-200 text-gray-500' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
                        >Thêm</button>
                      </li>
                    ))}
                </ul>
              )}
            </div>
          </div>

          <div className="lg:col-span-3 border border-gray-200 rounded-lg p-4 flex flex-col h-full overflow-hidden">
            <div className="mb-2 flex-shrink-0">
              <label className="block text-sm font-medium text-gray-700 mb-1">Lọc theo metadata (tùy chọn)</label>
              <input
                placeholder="Ví dụ: subject=Toán học"
                value={metadataFilter}
                onChange={(e) => setMetadataFilter(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex-1 overflow-y-auto border border-gray-100 rounded-md p-4 bg-gray-50 mb-2 min-h-0">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full py-12">
                  <div className="text-center max-w-md">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Chào mừng đến với NeuraViet AI</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      Chọn chế độ trả lời phù hợp và đặt câu hỏi của bạn ở ô bên dưới để nhận được hỗ trợ tốt nhất.
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((m, i) => (
                  <div key={i} className={`mb-4 ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
                    <div className={`inline-block px-4 py-2.5 rounded-lg max-w-[85%] ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-800 shadow-sm'}`}>
                      {m.role === 'user' ? (
                        <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">{m.content}</div>
                      ) : (
                        <div className="prose prose-sm max-w-none text-gray-800 prose-headings:font-semibold prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-pre:bg-gray-100 prose-pre:border prose-pre:border-gray-300 prose-table:border-collapse prose-table:border prose-table:border-gray-300 prose-th:border prose-th:border-gray-300 prose-th:bg-gray-100 prose-th:p-2 prose-td:border prose-td:border-gray-300 prose-td:p-2">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkMath]}
                            rehypePlugins={[rehypeKatex]}
                          >
                            {m.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                    {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
                      <div className="mt-1.5 text-xs text-gray-500">{m.citations.length} trích dẫn</div>
                    )}
                  </div>
                ))
              )}
              <div ref={endRef}></div>
            </div>
            <div className="border-t border-gray-200 pt-2 flex-shrink-0">
              <div className="mb-2">
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Chế độ trả lời</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setSystemPrompt('Hỏi đáp tấn công và phòng thủ mạng')}
                    className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${systemPrompt === 'Hỏi đáp tấn công và phòng thủ mạng'
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
                      }`}
                  >
                    Hỏi đáp tấn công và phòng thủ mạng
                  </button>
                  <button
                    type="button"
                    onClick={() => setSystemPrompt('Đào tạo mạng')}
                    className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${systemPrompt === 'Đào tạo mạng'
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
                      }`}
                  >
                    Đào tạo mạng
                  </button>
                </div>
              </div>
              <form onSubmit={sendMessage} className="flex gap-2">
                <input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Nhập câu hỏi của bạn..."
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  disabled={isSending || !message.trim()}
                  className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium text-sm"
                >
                  {isSending ? 'Đang gửi...' : 'Gửi'}
                </button>
                <button
                  type="button"
                  onClick={clearConversation}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium text-sm"
                >
                  Xóa
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

async function importLocalUrlToRag(localUrl: string, post: Post, token?: string): Promise<Response> {
  const res = await fetch(localUrl);
  const ct = res.headers.get('content-type') || '';
  const blob = await res.blob();
  let ext = 'txt';
  if (ct.includes('pdf')) ext = 'pdf';
  else if (ct.includes('html')) ext = 'html';
  else if (ct.includes('json')) ext = 'json';
  const filename = `${sanitizeFilename(post.title)}.${ext}`;
  const fd = new FormData();
  fd.append('file', new File([blob], filename));
  fd.append('metadata', JSON.stringify({ subject: post.subject, title: post.title }));
  fd.append('chunking_config', JSON.stringify({ enabled: true, max_tokens_per_chunk: 200, max_overlap_tokens: 20 }));
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
  return fetch('/api/rag/upload', { method: 'POST', headers, body: fd });
}

function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9-_]+/g, '_').slice(0, 60);
}


export default PracticeRAG;
