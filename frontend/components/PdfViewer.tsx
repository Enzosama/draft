import React, { useEffect, useState } from 'react';

interface PdfViewerProps {
  fileUrl: string;
  title: string;
  onClose: () => void;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ fileUrl, title, onClose }) => {
  const [src, setSrc] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError(null);
      
      // Check if fileUrl is valid
      if (!fileUrl || !fileUrl.trim()) {
        setError('Không có đường dẫn tài liệu. Vui lòng kiểm tra lại.');
        setLoading(false);
        return;
      }
      
      console.log('PdfViewer - Loading file:', fileUrl);
      
      try {
        const id = extractDriveId(fileUrl);
        if (id) {
          console.log('PdfViewer - Google Drive ID found:', id);
          setSrc(`https://drive.google.com/file/d/${id}/preview`);
          setLoading(false);
          return;
        }
        
        const isPdf = /\.pdf(\?.*)?$/i.test(fileUrl);
        
        // Check if it's a relative URL (starts with /)
        const isRelativeUrl = fileUrl.startsWith('/');
        
        if (isRelativeUrl) {
          // For relative URLs (like /cache/...), use directly or via proxy
          console.log('PdfViewer - Relative URL, using directly');
          if (isPdf) {
            setSrc(fileUrl);
          } else {
            // For non-PDF relative URLs, try to serve directly
            setSrc(fileUrl);
          }
          setLoading(false);
          return;
        }
        
        if (isPdf) {
          console.log('PdfViewer - Direct PDF URL');
          // For PDF files, try direct URL first, then proxy if needed
          setSrc(fileUrl);
          setLoading(false);
          return;
        }
        
        // Only try resolve-pdf for absolute URLs (http/https)
        if (fileUrl.startsWith('http://') || fileUrl.startsWith('https://')) {
          try {
            console.log('PdfViewer - Attempting to resolve PDF from URL');
            const r = await fetch(`/api/files/resolve-pdf?url=${encodeURIComponent(fileUrl)}`);
            if (r.ok) {
              const data = await r.json();
              const pdfUrl = data?.pdf_url;
              if (pdfUrl) {
                console.log('PdfViewer - Resolved PDF URL:', pdfUrl);
                setSrc(`/api/files/proxy?url=${encodeURIComponent(pdfUrl)}`);
                setLoading(false);
                return;
              }
            } else {
              console.warn('PdfViewer - Resolve PDF failed:', r.status);
            }
          } catch (e) {
            console.error('PdfViewer - Error resolving PDF:', e);
          }
        }
        
        // Fallback to Google Viewer (only for absolute URLs)
        if (fileUrl.startsWith('http://') || fileUrl.startsWith('https://')) {
          console.log('PdfViewer - Using Google Viewer as fallback');
          const gviewSrc = `https://docs.google.com/gview?url=${encodeURIComponent(fileUrl)}&embedded=true`;
          setSrc(gviewSrc);
        } else {
          // For relative URLs, just use them directly
          setSrc(fileUrl);
        }
        setLoading(false);
      } catch (err: any) {
        console.error('PdfViewer - Error loading PDF:', err);
        setError('Không thể tải tài liệu. Vui lòng thử lại hoặc tải về để xem.');
        setLoading(false);
      }
    };
    run();
  }, [fileUrl]);

function extractDriveId(url: string): string | null {
  try {
    const u = new URL(url);
    if (!u.hostname.includes('drive.google.com') && !u.hostname.includes('docs.google.com')) return null;
    const idParam = u.searchParams.get('id');
    if (idParam) return idParam;
    const m = u.pathname.match(/\/file\/d\/([^/]+)\//);
    if (m && m[1]) return m[1];
    const m2 = u.pathname.match(/uc\/?$/) ? u.searchParams.get('id') : null;
    return m2 || null;
  } catch {
    return null;
  }
}

  return (
    <div className="bg-white p-4 sm:p-6 rounded-lg shadow-lg">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
        <h2 className="text-xl font-bold text-gray-800 text-center sm:text-left line-clamp-2">{title}</h2>
        <div className="flex items-center gap-2">
          <a
            href={fileUrl}
            target="_blank"
            rel="noreferrer"
            className="hidden sm:inline-flex bg-gray-100 text-gray-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            Mở tab mới
          </a>
          <a
            href={fileUrl}
            download
            className="hidden sm:inline-flex bg-gray-100 text-gray-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            Tải về
          </a>
          <button
            onClick={onClose}
            className="flex-shrink-0 bg-[#1e40af] text-white px-5 py-2 rounded-md text-sm font-medium hover:bg-blue-900 transition-colors duration-300"
          >
            &larr; Quay lại danh sách
          </button>
        </div>
      </div>
      <div className="w-full h-[75vh] border-2 border-gray-200 rounded-md overflow-hidden bg-gray-100 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Đang tải tài liệu...</p>
            </div>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <div className="text-center p-6">
              <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-600 font-medium mb-2">Lỗi tải tài liệu</p>
              <p className="text-gray-600 text-sm mb-4">{error}</p>
              <a
                href={fileUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                Mở trong tab mới
              </a>
            </div>
          </div>
        )}
        {!error && src && (
          <iframe
            src={src}
            title={title}
            width="100%"
            height="100%"
            style={{ border: 'none' }}
            onLoad={() => {
              console.log('PdfViewer - Iframe loaded successfully');
              setLoading(false);
            }}
            onError={(e) => {
              console.error('PdfViewer - Iframe error:', e);
              setError('Không thể hiển thị tài liệu trong iframe. Vui lòng mở trong tab mới.');
              setLoading(false);
            }}
            sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
          />
        )}
        {!error && !src && !loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <div className="text-center p-6">
              <p className="text-gray-600">Đang chuẩn bị tài liệu...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PdfViewer;
