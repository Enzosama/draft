import React, { useState, useRef, useEffect } from 'react';
import { Category, User, Notification } from '../data/types';
import { BookOpenIcon, DocumentTextIcon, PencilAltIcon, UserIcon, LogoutIcon, ChatAltIcon, ChevronDownIcon, BellIcon } from './icons';

interface HeaderProps {
  activeCategory: Category;
  setActiveCategory: (category: Category) => void;
  currentUser: User | null;
  onLoginClick: () => void;
  onRegisterClick: () => void;
  onLogout: () => void;
  onProfileClick: () => void;
  onLogoClick: () => void;
}

const Header: React.FC<HeaderProps> = ({
  activeCategory,
  setActiveCategory,
  currentUser,
  onLoginClick,
  onRegisterClick,
  onLogout,
  onProfileClick,
  onLogoClick
}) => {
  // Ẩn các tab "Đề Thi" (Category.EXAM) và "Thi Thử" (Category.MOCK_TEST) khỏi menu
  // nhưng vẫn giữ enum Category để không ảnh hưởng logic nơi khác.
  const navItems = [
    { name: Category.MATERIAL, icon: <DocumentTextIcon className="w-5 h-5 mr-2" /> },
    { name: Category.PRACTICE, icon: <ChatAltIcon className="w-5 h-5 mr-2" /> },
    ...(currentUser?.role === 'teacher' ? [{
      name: 'Bảng điều khiển giáo viên' as any,
      icon: <BookOpenIcon className="w-5 h-5 mr-2" />,
      isDashboard: true
    }] : []),
  ];

  return (
    <header className="bg-white shadow-md sticky top-0 z-10">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <div className="flex-shrink-0">
            <h1
              onClick={onLogoClick}
              className="text-2xl md:text-3xl font-bold text-[#1e40af] cursor-pointer"
            >
              NeuraViet
            </h1>
          </div>
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {navItems.map((item) => {
                const isActive = activeCategory === item.name;
                const isDashboard = (item as any).isDashboard;

                const buttonClass = isActive
                  ? 'bg-[#1e40af] text-white'
                  : 'text-gray-700 hover:bg-sky-100';

                return (
                  <button
                    key={item.name}
                    onClick={() => {
                      if (isDashboard) {
                        window.dispatchEvent(new CustomEvent('navigate-dashboard', { detail: 'teacher' }));
                      } else {
                        setActiveCategory(item.name);
                      }
                    }}
                    className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors duration-300 ${buttonClass}`}
                  >
                    {item.icon}
                    {(item as any).displayName || item.name}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {currentUser ? (
              <>
                {/* Notification Bell - Only for teachers */}
                {currentUser.role === 'teacher' && (
                  <NotificationBell currentUser={currentUser} />
                )}

                {/* Account Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => {
                      const event = new CustomEvent('toggle-account-menu');
                      window.dispatchEvent(event);
                    }}
                    className="flex items-center bg-transparent text-gray-700 hover:bg-sky-100 px-4 py-2 rounded-md text-sm font-medium transition-colors duration-300">
                    <UserIcon className="mr-2" />
                    Tài khoản
                    <ChevronDownIcon className="ml-2 w-4 h-4" />
                  </button>
                  <AccountDropdown
                    currentUser={currentUser}
                    onProfileClick={onProfileClick}
                    onLogout={onLogout}
                  />
                </div>
              </>
            ) : (
              <>
                <button onClick={onLoginClick} className="bg-transparent text-gray-700 hover:bg-sky-100 px-4 py-2 rounded-md text-sm font-medium transition-colors duration-300">
                  Đăng nhập
                </button>
                <button onClick={onRegisterClick} className="ml-2 bg-[#1e40af] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-900 transition-colors duration-300">
                  Đăng ký
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

// Account Dropdown Component
interface AccountDropdownProps {
  currentUser: User;
  onProfileClick: () => void;
  onLogout: () => void;
}

const AccountDropdown: React.FC<AccountDropdownProps> = ({ currentUser, onProfileClick, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleToggle = () => setIsOpen(prev => !prev);
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    window.addEventListener('toggle-account-menu', handleToggle as EventListener);
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      window.removeEventListener('toggle-account-menu', handleToggle as EventListener);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogoutClick = () => {
    setIsOpen(false);
    onLogout();
  };

  if (!isOpen) return null;

  return (
    <>
      <div
        ref={dropdownRef}
        className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 z-50"
      >
        <div className="py-1">
          <div className="px-4 py-3 border-b border-gray-200">
            <p className="text-sm font-medium text-gray-900">{currentUser.name}</p>
            <p className="text-xs text-gray-500">{currentUser.email}</p>
          </div>

          <button
            onClick={() => {
              setIsOpen(false);
              onProfileClick();
            }}
            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
          >
            <UserIcon className="w-4 h-4 mr-2" />
            Hồ sơ
          </button>


          {currentUser.role === 'admin' && (
            <button
              onClick={() => {
                setIsOpen(false);
                window.dispatchEvent(new CustomEvent('navigate-dashboard', { detail: 'admin' }));
              }}
              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
            >
              <BookOpenIcon className="w-4 h-4 mr-2" />
              Bảng điều khiển quản trị
            </button>
          )}

          <div className="border-t border-gray-200 my-1"></div>

          <button
            onClick={handleLogoutClick}
            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
          >
            <LogoutIcon className="w-4 h-4 mr-2" />
            Đăng xuất
          </button>
        </div>
      </div>
    </>
  );
};

// Notification Bell Component
interface NotificationBellProps {
  currentUser: User;
}

interface SystemNotification {
  id: number;
  type: 'submission' | 'system' | 'other';
  title: string;
  content: string;
  classroom_id?: number;
  created_at: string;
  is_read: boolean;
}

const NotificationBell: React.FC<NotificationBellProps> = ({ currentUser }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<SystemNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [classrooms, setClassrooms] = useState<any[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      // TODO: Fetch system notifications (student submissions, system alerts, etc.)
      // This should NOT include teacher-created notifications
      // For now, we'll use empty array or demo data for system notifications

      if (!token) {
        // Demo mode - system notifications
        const mockSystemNotifications: SystemNotification[] = [
          {
            id: 1,
            type: 'submission',
            title: 'Học sinh nộp bài',
            content: 'Nguyễn Văn A đã nộp bài tập môn Toán học',
            classroom_id: 1,
            created_at: new Date().toISOString(),
            is_read: false
          },
          {
            id: 2,
            type: 'system',
            title: 'Thông báo hệ thống',
            content: 'Hệ thống đã cập nhật tính năng mới',
            created_at: new Date(Date.now() - 3600000).toISOString(),
            is_read: false
          }
        ];
        setNotifications(mockSystemNotifications);
        setUnreadCount(mockSystemNotifications.filter(n => !n.is_read).length);
        setLoading(false);
        return;
      }

      // TODO: Replace with actual API endpoint for system notifications
      // Example: /api/teacher/system-notifications
      // This endpoint should return:
      // - Student submissions notifications
      // - System alerts
      // - Other non-teacher-created notifications

      // Fetch classrooms for displaying classroom names in notifications
      const classroomsRes = await fetch('/api/teacher/classrooms', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const classroomsData = classroomsRes.ok ? await classroomsRes.json() : [];
      setClassrooms(classroomsData);

      // For now, set empty array (will be populated when API is ready)
      setNotifications([]);
      setUnreadCount(0);
    } catch (error) {
      console.error('Error fetching system notifications:', error);
      setNotifications([]);
      setUnreadCount(0);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDashboard = () => {
    setIsOpen(false);
    window.dispatchEvent(new CustomEvent('navigate-dashboard', { detail: 'teacher' }));
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative flex items-center justify-center bg-transparent text-gray-700 hover:bg-sky-100 px-3 py-2 rounded-md transition-colors duration-300"
        title="Thông báo"
      >
        <BellIcon className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border border-gray-200 z-50 max-h-96 overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Thông báo hệ thống</h3>
            {unreadCount > 0 && (
              <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-1 rounded-full">
                {unreadCount} chưa đọc
              </span>
            )}
          </div>

          <div className="overflow-y-auto flex-1">
            {loading ? (
              <div className="p-4 text-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-500 mt-2">Đang tải...</p>
              </div>
            ) : notifications.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {notifications.map((notification) => {
                  const classroom = classrooms.find(c => c.id === notification.classroom_id);
                  const isUnread = !notification.is_read;
                  return (
                    <div
                      key={notification.id}
                      className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={handleOpenDashboard}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="text-sm font-medium text-gray-900 line-clamp-1">
                              {notification.title}
                            </h4>
                            {notification.type === 'submission' && (
                              <span className="px-1.5 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">
                                Nộp bài
                              </span>
                            )}
                            {notification.type === 'system' && (
                              <span className="px-1.5 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">
                                Hệ thống
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                            {notification.content}
                          </p>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            {classroom && (
                              <span>{classroom.name}</span>
                            )}
                            {classroom && <span>•</span>}
                            <span>{new Date(notification.created_at).toLocaleDateString('vi-VN')}</span>
                          </div>
                        </div>
                        {isUnread && (
                          <span className="ml-2 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center flex-shrink-0">
                            !
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-8 text-center">
                <BellIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-sm text-gray-500">Chưa có thông báo hệ thống nào</p>
                <p className="text-xs text-gray-400 mt-1">Thông báo về học sinh nộp bài, hệ thống sẽ hiển thị ở đây</p>
              </div>
            )}
          </div>

          {notifications.length > 0 && (
            <div className="p-3 border-t border-gray-200">
              <button
                onClick={handleOpenDashboard}
                className="w-full text-center text-sm text-blue-600 hover:text-blue-700 font-medium py-2 hover:bg-blue-50 rounded-md transition-colors"
              >
                Xem tất cả thông báo hệ thống
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Header;
