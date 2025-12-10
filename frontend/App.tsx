import React, { useState, useMemo, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import SearchBar from './components/SearchBar';
import PostList from './components/PostList';
import Footer from './components/Footer';
import PdfViewer from './components/PdfViewer';
import OnlineExam from './components/OnlineExam';
import AuthModal from './components/AuthModal';
import ProfilePage from './components/ProfilePage';
import AdminDashboard from './components/AdminDashboard';
import TeacherDashboard from './components/TeacherDashboard';
import PracticeRAG from './components/PracticeRAG';
import CyberTopics from './components/CyberTopics';

import { Post, Category, User } from './data/types';

type View = 'home' | 'pdf' | 'exam' | 'practice' | 'profile' | 'login' | 'register' | 'forgot-password' | 'admin' | 'teacher';

const App: React.FC = () => {
  console.log('App component mounting...');
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  // Mặc định chuyển sang tab "Tài Liệu" thay vì "Đề Thi" (đã ẩn khỏi header)
  const [activeCategory, setActiveCategory] = useState<Category>(Category.MATERIAL);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const [currentView, setCurrentView] = useState<View>('home');
  const [activePost, setActivePost] = useState<Post | null>(null);

  const [currentUser, setCurrentUser] = useState<User | null>(null);

  // Helper function to extract Google Drive ID from URL
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

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/posts?page=1&page_size=50');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const payload = await response.json();
        const items = Array.isArray(payload) ? payload : (payload?.data || []);
        console.log('App - Fetched posts:', items.length);
        const mapped: Post[] = items.map((p: any) => {
          const post: Post = {
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
            fileUrl: p.file_url || p.fileUrl || null
          };
          // Debug log for posts without fileUrl
          if (!post.fileUrl && post.category !== Category.MOCK_TEST) {
            console.warn('App - Post without fileUrl:', post.title, post.category);
          }
          return post;
        });
        setPosts(mapped);
        console.log('App - Mapped posts:', mapped.length);
      } catch (error) {
        console.error("App - Could not fetch posts:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPosts();
  }, []);

  const filteredPosts = useMemo(() => {
    return posts
      .filter((post) => post.category === activeCategory)
      .filter((post) =>
        post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        post.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
  }, [activeCategory, searchTerm, posts]);

  const resetToHome = () => {
    setCurrentView('home');
    setActivePost(null);
  }

  const handlePostAction = async (post: Post) => {
    console.log('handlePostAction - Post:', post);
    let targetPost = post;

    // For MOCK_TEST, go directly to exam view
    if (post.category === Category.MOCK_TEST) {
      console.log('handlePostAction - MOCK_TEST category, going to exam view');
      setActivePost(targetPost);
      setCurrentView('exam');
      return;
    }

    // For other categories, handle file URL
    if (post.fileUrl && post.fileUrl.trim()) {
      // Check if it's a Google Drive URL - use preview directly instead of caching
      const driveId = extractDriveId(post.fileUrl);
      if (driveId) {
        console.log('handlePostAction - Google Drive URL detected, using preview:', driveId);
        // Use Google Drive preview URL directly - no need to cache
        targetPost = { ...post, fileUrl: `https://drive.google.com/file/d/${driveId}/preview` };
      } else {
        console.log('handlePostAction - Has fileUrl, attempting to cache:', post.fileUrl);
        try {
          const cacheRes = await fetch('/api/files/cache', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: post.fileUrl, filename: sanitizeFilename(post.title) })
          });
          if (cacheRes.ok) {
            const cached = await cacheRes.json();
            // Only use cached URL if it's actually a PDF, not HTML
            if (cached?.local_url && cached?.content_type?.includes('pdf')) {
              console.log('handlePostAction - Cached PDF successfully:', cached.local_url);
              targetPost = { ...post, fileUrl: cached.local_url };
            } else if (cached?.local_url) {
              console.log('handlePostAction - Cached file is not PDF, using original URL');
              // Keep original URL for non-PDF files
            }
          } else {
            console.warn('handlePostAction - Cache failed:', cacheRes.status);
          }
        } catch (err) {
          console.error('handlePostAction - Cache error:', err);
          // Continue with original fileUrl even if cache fails
        }
      }
    } else {
      console.warn('handlePostAction - No fileUrl for post:', post.title);
    }

    setActivePost(targetPost);
    if (targetPost.fileUrl) {
      console.log('handlePostAction - Going to PDF view with URL:', targetPost.fileUrl);
      setCurrentView('pdf');
    } else {
      console.error('handlePostAction - No fileUrl, cannot view');
      alert('Tài liệu này không có đường dẫn file. Vui lòng liên hệ quản trị viên.');
    }
  };

  const handleSetActiveCategory = (category: Category | string) => {
    if (category === Category.PRACTICE) {
      setActiveCategory(category);
      setCurrentView('practice');
      window.location.hash = '';
    } else {
      setActiveCategory(category as Category);
      window.location.hash = '';
      resetToHome();
    }
  }

  const handleAuthSuccess = (user: User) => {
    setCurrentUser(user);
    if (user.role === 'admin') {
      setCurrentView('admin');
    } else if (user.role === 'teacher') {
      setCurrentView('teacher');
    } else {
      setCurrentView('home');
    }
  };

  // Allow direct access to teacher dashboard for demo (check URL params)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('view') === 'teacher' && !currentUser) {
      // Set a demo user for viewing
      setCurrentUser({
        name: 'Giáo viên Demo',
        email: 'teacher@demo.com',
        role: 'teacher'
      });
      setCurrentView('teacher');
    }
  }, [currentUser]);

  const handleLogout = async () => {
    console.log('App.tsx - handleLogout called');
    try {
      // Call backend logout endpoint
      const token = localStorage.getItem('token');
      console.log('App.tsx - Current token:', token ? 'Found' : 'Not found');

      if (token) {
        console.log('App.tsx - Calling /api/logout...');
        await fetch('/api/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        console.log('App.tsx - /api/logout call successful');
      }
    } catch (error) {
      console.error('App.tsx - Logout API error:', error);
    } finally {
      console.log('App.tsx - Clearing local state...');
      // Always clear local state regardless of API success
      localStorage.removeItem('token');
      setCurrentUser(null);
      resetToHome();
      try {
        fetch('/api/files/cache/clear', { method: 'DELETE' });
      } catch { }
      console.log('App.tsx - Local state cleared, redirected to home');
    }
  }

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as 'admin' | 'teacher';
      if (detail) setCurrentView(detail);
    };
    window.addEventListener('navigate-dashboard', handler as EventListener);
    return () => window.removeEventListener('navigate-dashboard', handler as EventListener);
  }, []);

  if (currentView === 'exam') {
    return activePost ? (
      <OnlineExam
        examInfo={activePost}
        onClose={resetToHome}
        onLoginRequired={() => setCurrentView('login')}
      />
    ) : null;
  }

  const renderContent = () => {
    switch (currentView) {
      case 'login':
      case 'register':
      case 'forgot-password':
        return (
          <AuthModal
            mode={currentView}
            onSwitchMode={(mode) => setCurrentView(mode)}
            onAuthSuccess={handleAuthSuccess}
          />
        );
      case 'profile':
        return currentUser ? <ProfilePage user={currentUser} onClose={resetToHome} /> : null;
      case 'pdf':
        return activePost && activePost.fileUrl ? (
          <PdfViewer fileUrl={activePost.fileUrl} title={activePost.title} onClose={resetToHome} />
        ) : null;
      case 'home':
        return (
          <div className="flex flex-col lg:flex-row gap-8">
            <Sidebar selectedTopic={selectedTopic} setSelectedTopic={setSelectedTopic} />
            <div className="flex-1">
              <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
              {isLoading ? (
                <div className="text-center py-16">
                  <h3 className="text-xl font-semibold text-gray-700">Đang tải dữ liệu...</h3>
                  <p className="text-gray-500 mt-2">Vui lòng chờ trong giây lát.</p>
                </div>
              ) : activeCategory === Category.MATERIAL ? (
                <CyberTopics selectedTopicSlug={selectedTopic} />
              ) : (
                <PostList posts={filteredPosts} onAction={handlePostAction} />
              )}
            </div>
          </div>
        );
      case 'practice':
        return (
          <div className="w-full" style={{ height: 'calc(100vh - 80px)' }}>
            <PracticeRAG />
          </div>
        );

      case 'admin':
        return currentUser ? <AdminDashboard currentUser={currentUser} onClose={resetToHome} /> : null;
      case 'teacher':
        return currentUser ? <TeacherDashboard currentUser={currentUser} onClose={resetToHome} /> : null;
      default:
        return null;
    }
  };

  const isAuthView = currentView === 'login' || currentView === 'register' || currentView === 'forgot-password';

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        activeCategory={activeCategory}
        setActiveCategory={handleSetActiveCategory}
        currentUser={currentUser}
        onLoginClick={() => setCurrentView('login')}
        onRegisterClick={() => setCurrentView('register')}
        onLogout={handleLogout}
        onProfileClick={() => setCurrentView('profile')}
        onLogoClick={resetToHome}
      />
      <main className={`flex-grow ${isAuthView ? 'flex flex-col' : currentView === 'practice' ? '' : 'container mx-auto px-4 sm:px-6 lg:px-8 py-8'}`}>
        {renderContent()}
      </main>

      {!isAuthView && currentView !== 'practice' && <Footer />}
    </div>
  );
};

export default App;

function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9-_]+/g, '_').slice(0, 60);
}
