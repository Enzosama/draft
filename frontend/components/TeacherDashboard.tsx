import React, { useState, useEffect } from 'react';
import { User, Classroom, Notification, TeacherPost } from '../data/types';
import { 
  PlusIcon, UserGroupIcon, BellIcon, DocumentTextIcon, 
  ChartBarIcon, UsersIcon, XIcon, EditIcon, TrashIcon,
  CopyIcon, CheckIcon, SearchIcon, FilterIcon
} from './icons';
import TeacherExamManager from './TeacherExamManager';
import ClassroomManager from './ClassroomManager';
import PostEditor from './PostEditor';
import NotificationManager from './NotificationManager';
import StudentManager from './StudentManager';

interface TeacherDashboardProps {
  currentUser: User;
  onClose: () => void;
}

interface DashboardStats {
  totalClassrooms: number;
  totalStudents: number;
  totalPosts: number;
  unreadNotifications: number;
}

type TabType = 'overview' | 'classrooms' | 'posts' | 'notifications' | 'exams' | 'students';

const TeacherDashboard: React.FC<TeacherDashboardProps> = ({ currentUser, onClose }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [stats, setStats] = useState<DashboardStats>({
    totalClassrooms: 0,
    totalStudents: 0,
    totalPosts: 0,
    unreadNotifications: 0
  });
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [posts, setPosts] = useState<TeacherPost[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [showClassroomManager, setShowClassroomManager] = useState(false);
  const [showPostEditor, setShowPostEditor] = useState(false);
  const [showNotificationManager, setShowNotificationManager] = useState(false);
  const [showStudentManager, setShowStudentManager] = useState(false);
  const [showExamManager, setShowExamManager] = useState(false);
  const [editingPost, setEditingPost] = useState<TeacherPost | undefined>(undefined);
  const [selectedClassroom, setSelectedClassroom] = useState<number | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [allStudents, setAllStudents] = useState<any[]>([]);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [studentSearchTerm, setStudentSearchTerm] = useState('');
  const [studentFilterStatus, setStudentFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [studentFilterClassroom, setStudentFilterClassroom] = useState<number | null>(null);

  useEffect(() => {
    // Check if we should use demo mode (no token or API fails)
    const token = localStorage.getItem('token');
    if (!token) {
      setDemoMode(true);
      loadDemoData();
    } else {
    fetchDashboardData();
    }
  }, []);

  const loadDemoData = () => {
    // Mock data for demo
    const mockClassrooms: Classroom[] = [
      {
        id: 1,
        name: 'Lớp Toán 10A1',
        description: 'Lớp học Toán học cho học sinh lớp 10',
        subject: 'Toán học',
        code: 'ABC123',
        is_active: true,
        student_count: 25,
        created_at: new Date().toISOString()
      },
      {
        id: 2,
        name: 'Lớp Vật lý 11B2',
        description: 'Lớp học Vật lý nâng cao',
        subject: 'Vật lý',
        code: 'XYZ789',
        is_active: true,
        student_count: 18,
        created_at: new Date().toISOString()
      },
      {
        id: 3,
        name: 'Lớp Hóa học 12C3',
        description: 'Lớp học Hóa học chuyên sâu',
        subject: 'Hóa học',
        code: 'DEF456',
        is_active: false,
        student_count: 0,
        created_at: new Date().toISOString()
      }
    ];

    const mockPosts: TeacherPost[] = [
      {
        id: 1,
        title: 'Đề thi thử Toán học kỳ 1',
        author: currentUser.name,
        date: new Date().toISOString().split('T')[0],
        subject: 'Toán học',
        category: 'Đề Thi' as any,
        description: 'Đề thi thử môn Toán học kỳ 1 năm học 2024-2025',
        views: 150,
        downloads: 45,
        comments: 0
      },
      {
        id: 2,
        title: 'Tài liệu ôn tập Vật lý',
        author: currentUser.name,
        date: new Date().toISOString().split('T')[0],
        subject: 'Vật lý',
        category: 'Tài Liệu' as any,
        description: 'Tài liệu tổng hợp các công thức và bài tập Vật lý',
        views: 89,
        downloads: 32,
        comments: 0
      }
    ];

    const mockNotifications: Notification[] = [
      {
        id: 1,
        classroom_id: 1,
        title: 'Thông báo kiểm tra giữa kỳ',
        content: 'Lớp sẽ có bài kiểm tra giữa kỳ vào tuần tới. Các em hãy chuẩn bị tốt.',
        is_announcement: true,
        created_by: 1,
        created_at: new Date().toISOString(),
        unread_count: 5
      },
      {
        id: 2,
        classroom_id: 2,
        title: 'Nhắc nhở nộp bài tập',
        content: 'Các em nhớ nộp bài tập về nhà trước thứ 6 tuần này.',
        is_announcement: false,
        created_by: 1,
        created_at: new Date().toISOString(),
        unread_count: 2
      }
    ];

    setClassrooms(mockClassrooms);
    setPosts(mockPosts);
    setNotifications(mockNotifications);
    
    setStats({
      totalClassrooms: mockClassrooms.length,
      totalStudents: mockClassrooms.reduce((sum, c) => sum + c.student_count, 0),
      totalPosts: mockPosts.length,
      unreadNotifications: mockNotifications.reduce((sum, n) => sum + (n.unread_count || 0), 0)
    });
    
    setLoading(false);
  };

  const fetchAllStudents = async () => {
    try {
      setStudentsLoading(true);
      const token = localStorage.getItem('token');
      
      if (!token || demoMode) {
        // Demo mode
        const mockStudents = [
          {
            id: 1,
            username: 'student1',
            email: 'student1@example.com',
            full_name: 'Nguyễn Văn Anh Tuấn',
            joined_at: new Date().toISOString(),
            is_active: true,
            classrooms: [
              { id: 1, name: 'Lớp Toán 10A1', subject: 'Toán học' },
              { id: 2, name: 'Lớp Vật lý 11B2', subject: 'Vật lý' }
            ]
          },
          {
            id: 2,
            username: 'student2',
            email: 'student2@example.com',
            full_name: 'Trần Thị Bích Ngọc',
            joined_at: new Date().toISOString(),
            is_active: true,
            classrooms: [
              { id: 1, name: 'Lớp Toán 10A1', subject: 'Toán học' }
            ]
          },
          {
            id: 3,
            username: 'student3',
            email: 'student3@example.com',
            full_name: 'Lê Văn Cường',
            joined_at: new Date().toISOString(),
            is_active: false,
            classrooms: [
              { id: 2, name: 'Lớp Vật lý 11B2', subject: 'Vật lý' }
            ]
          }
        ];
        setAllStudents(mockStudents);
        setStudentsLoading(false);
        return;
      }

      if (classrooms.length === 0) {
        setAllStudents([]);
        setStudentsLoading(false);
        return;
      }

      // Fetch all students from all classrooms
      const studentMap = new Map<number, any>();

      for (const classroom of classrooms) {
        try {
          const response = await fetch(`/api/teacher/classrooms/${classroom.id}/students`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const students = await response.json();
            for (const student of students) {
              if (!studentMap.has(student.id)) {
                studentMap.set(student.id, {
                  ...student,
                  full_name: student.fullname || student.full_name,
                  username: student.username || `user_${student.id}`,
                  is_active: student.is_active !== undefined ? student.is_active : true,
                  classrooms: []
                });
              }
              const studentData = studentMap.get(student.id);
              studentData.classrooms.push({
                id: classroom.id,
                name: classroom.name,
                subject: classroom.subject
              });
            }
          }
        } catch (e) {
          console.error('Error fetching students for classroom', classroom.id, e);
        }
      }

      setAllStudents(Array.from(studentMap.values()));
    } catch (error) {
      console.error('Error fetching all students:', error);
    } finally {
      setStudentsLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Fetch teacher's classrooms
      const classroomsRes = await fetch('/api/teacher/classrooms', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const classroomsData = classroomsRes.ok ? await classroomsRes.json() : [];

      // If no data and no token, use demo mode
      if (!token || (!classroomsRes.ok && classroomsData.length === 0)) {
        setDemoMode(true);
        loadDemoData();
        return;
      }

      // Fetch teacher's posts
      const postsRes = await fetch('/api/teacher/posts', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const postsData = postsRes.ok ? await postsRes.json() : { data: [] };

      // Fetch notifications (get from all classrooms)
      const allNotifications: Notification[] = [];
      for (const classroom of classroomsData) {
        try {
          const notifRes = await fetch(`/api/teacher/notifications/classroom/${classroom.id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (notifRes.ok) {
            const notifs = await notifRes.json();
            allNotifications.push(...(Array.isArray(notifs) ? notifs : []));
          }
        } catch (e) {
          console.error('Error fetching notifications for classroom', classroom.id, e);
        }
      }

      setClassrooms(classroomsData);
      setPosts(postsData.data || []);
      setNotifications(allNotifications);

      // Calculate stats
      const totalStudents = classroomsData.reduce((sum: number, c: Classroom) => sum + (c.student_count || 0), 0);
      const unreadNotifications = allNotifications.reduce((sum: number, n: Notification) => sum + (n.unread_count || 0), 0);
      
      setStats({
        totalClassrooms: classroomsData.length,
        totalStudents,
        totalPosts: postsData.data?.length || 0,
        unreadNotifications
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Fallback to demo mode on error
      setDemoMode(true);
      loadDemoData();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'students') {
      if (classrooms.length > 0) {
        fetchAllStudents();
      } else if (!loading) {
        // If classrooms are loaded but empty, set empty students
        setAllStudents([]);
      }
    }
  }, [activeTab, classrooms, loading]);

  const handleDeletePost = async (postId: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa bài đăng này?')) return;
    
    if (demoMode) {
      // Demo mode: just update local state
      setPosts(posts.filter(p => p.id !== postId));
      setStats(prev => ({ ...prev, totalPosts: prev.totalPosts - 1 }));
      alert('(Demo) Bài đăng đã được xóa');
      return;
    }
    
    try {
      const response = await fetch(`/api/teacher/posts/${postId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        setPosts(posts.filter(p => p.id !== postId));
        setStats(prev => ({ ...prev, totalPosts: prev.totalPosts - 1 }));
      }
    } catch (error) {
      console.error('Error deleting post:', error);
      alert('Xóa bài đăng thất bại');
    }
  };

  const handleSavePost = (savedPost: TeacherPost) => {
    if (demoMode) {
      // Demo mode: just update local state
      if (editingPost) {
        setPosts(posts.map(p => p.id === savedPost.id ? savedPost : p));
      } else {
        setPosts([savedPost, ...posts]);
        setStats(prev => ({ ...prev, totalPosts: prev.totalPosts + 1 }));
      }
      setShowPostEditor(false);
      setEditingPost(undefined);
      alert('(Demo) Bài đăng đã được lưu');
      return;
    }
    
    if (editingPost) {
      setPosts(posts.map(p => p.id === savedPost.id ? savedPost : p));
    } else {
      setPosts([savedPost, ...posts]);
      setStats(prev => ({ ...prev, totalPosts: prev.totalPosts + 1 }));
    }
    setShowPostEditor(false);
    setEditingPost(undefined);
    fetchDashboardData();
  };

  const copyClassroomCode = (code: string) => {
    navigator.clipboard.writeText(code);
    alert('Mã tham gia đã được sao chép!');
  };

  const StatCard: React.FC<{ title: string; value: number; icon: React.ReactNode; color: string; onClick?: () => void }> = ({ 
    title, value, icon, color, onClick 
  }) => (
    <div 
      onClick={onClick}
      className={`bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition-all cursor-pointer ${onClick ? '' : ''}`}
    >
              <div className="flex items-center justify-between">
                <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
                </div>
        <div className={`p-4 rounded-full ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  const tabs = [
    { id: 'overview' as TabType, label: 'Tổng quan', icon: <ChartBarIcon className="w-5 h-5" /> },
    { id: 'classrooms' as TabType, label: 'Lớp học', icon: <UserGroupIcon className="w-5 h-5" /> },
    { id: 'students' as TabType, label: 'Học sinh', icon: <UsersIcon className="w-5 h-5" /> },
    { id: 'posts' as TabType, label: 'Bài đăng', icon: <DocumentTextIcon className="w-5 h-5" /> },
    { id: 'notifications' as TabType, label: 'Tạo thông báo', icon: <BellIcon className="w-5 h-5" /> },
    { id: 'exams' as TabType, label: 'Đề thi', icon: <DocumentTextIcon className="w-5 h-5" /> },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Đang tải dữ liệu...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-bold text-gray-900">Bảng điều khiển giáo viên</h1>
                {demoMode && (
                  <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                    Chế độ Demo
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mt-1">Xin chào, {currentUser.name}</p>
            </div>
              <button
                onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              >
              <XIcon className="w-6 h-6" />
              </button>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-80px)]">
          <nav className="p-4 space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
                {tab.id === 'notifications' && stats.unreadNotifications > 0 && (
                  <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                    {stats.unreadNotifications}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                  title="Tổng số lớp học"
                  value={stats.totalClassrooms}
                  icon={<UserGroupIcon className="w-6 h-6 text-white" />}
                  color="bg-blue-500"
                  onClick={() => setActiveTab('classrooms')}
                />
                <StatCard
                  title="Tổng số học sinh"
                  value={stats.totalStudents}
                  icon={<UsersIcon className="w-6 h-6 text-white" />}
                  color="bg-green-500"
                  onClick={() => setActiveTab('classrooms')}
                />
                <StatCard
                  title="Tổng số bài đăng"
                  value={stats.totalPosts}
                  icon={<DocumentTextIcon className="w-6 h-6 text-white" />}
                  color="bg-purple-500"
                  onClick={() => setActiveTab('posts')}
                />
                <StatCard
                  title="Thông báo chưa đọc"
                  value={stats.unreadNotifications}
                  icon={<BellIcon className="w-6 h-6 text-white" />}
                  color="bg-red-500"
                  onClick={() => setActiveTab('notifications')}
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Classrooms */}
                <div className="bg-white rounded-lg shadow-md border border-gray-200">
                  <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900">Lớp học gần đây</h3>
                      <button
                        onClick={() => setShowClassroomManager(true)}
                        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                      >
                        Xem tất cả
                      </button>
                    </div>
                  </div>
                  <div className="p-6">
                    {classrooms.slice(0, 5).length > 0 ? (
                      <div className="space-y-4">
                        {classrooms.slice(0, 5).map((classroom) => (
                          <div key={classroom.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                            <div className="flex-1">
                              <p className="font-medium text-gray-900">{classroom.name}</p>
                              <p className="text-sm text-gray-500">
                                {classroom.subject} • {classroom.student_count || 0} học sinh
                              </p>
                            </div>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => copyClassroomCode(classroom.code)}
                                className="text-blue-600 hover:text-blue-700"
                                title="Sao chép mã"
                              >
                                <CopyIcon className="w-4 h-4" />
                              </button>
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                classroom.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                              }`}>
                                {classroom.is_active ? 'Hoạt động' : 'Tạm dừng'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <UserGroupIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-500">Chưa có lớp học nào</p>
                        <button
                          onClick={() => setShowClassroomManager(true)}
                          className="mt-3 text-blue-600 hover:text-blue-700 text-sm font-medium"
                        >
                          Tạo lớp học đầu tiên
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Recent Notifications */}
                <div className="bg-white rounded-lg shadow-md border border-gray-200">
                  <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900">Thông báo mới nhất</h3>
                      <button
                        onClick={() => setActiveTab('notifications')}
                        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                      >
                        Xem tất cả
                      </button>
                    </div>
                  </div>
                  <div className="p-6">
                    {notifications.slice(0, 5).length > 0 ? (
                      <div className="space-y-4">
                        {notifications.slice(0, 5).map((notification) => (
                          <div key={notification.id} className="p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="font-medium text-gray-900 mb-1">{notification.title}</p>
                                <p className="text-sm text-gray-600 line-clamp-2">{notification.content}</p>
                                <p className="text-xs text-gray-400 mt-2">
                                  {new Date(notification.created_at).toLocaleDateString('vi-VN')}
                                </p>
                              </div>
                              {notification.unread_count && notification.unread_count > 0 && (
                                <span className="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                                  {notification.unread_count}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <BellIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-500">Chưa có thông báo nào</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'classrooms' && (
            <div className="bg-white rounded-lg shadow-md border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Quản lý lớp học</h3>
                  <button
                    onClick={() => setShowClassroomManager(true)}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    <PlusIcon className="w-4 h-4 mr-2" />
                    Tạo lớp học mới
                  </button>
                </div>
              </div>
              <div className="p-6">
                {classrooms.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {classrooms.map((classroom) => (
                      <div key={classroom.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900 mb-1">{classroom.name}</h4>
                            {classroom.description && (
                              <p className="text-sm text-gray-600 mb-2">{classroom.description}</p>
                            )}
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            classroom.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {classroom.is_active ? 'Hoạt động' : 'Tạm dừng'}
                          </span>
                        </div>
                        <div className="space-y-2 mb-3">
                          {classroom.subject && (
                            <div className="flex items-center text-sm text-gray-600">
                              <span className="font-medium mr-2">Môn:</span>
                              <span>{classroom.subject}</span>
                            </div>
                          )}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center text-sm text-gray-600">
                              <UsersIcon className="w-4 h-4 mr-1" />
                              <span>{classroom.student_count || 0} học sinh</span>
                            </div>
                            <button
                              onClick={() => copyClassroomCode(classroom.code)}
                              className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center"
                            >
                              <CopyIcon className="w-4 h-4 mr-1" />
                              Mã: {classroom.code}
                            </button>
                          </div>
                        </div>
                        <div className="pt-3 border-t border-gray-100 flex gap-2">
                          <button
                            onClick={() => {
                              setSelectedClassroom(classroom.id);
                              setShowStudentManager(true);
                            }}
                            className="flex-1 text-sm text-blue-600 hover:text-blue-700 font-medium py-2 px-3 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
                          >
                            <UsersIcon className="w-4 h-4 inline mr-1" />
                            Quản lý học sinh
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <UserGroupIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có lớp học nào</h3>
                    <p className="text-gray-500 mb-4">Hãy tạo lớp học đầu tiên của bạn</p>
                    <button
                      onClick={() => setShowClassroomManager(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Tạo lớp học mới
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}


          {activeTab === 'posts' && (
            <div className="bg-white rounded-lg shadow-md border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Quản lý bài đăng</h3>
                  <button
                    onClick={() => {
                      setEditingPost(undefined);
                      setShowPostEditor(true);
                    }}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    <PlusIcon className="w-4 h-4 mr-2" />
                    Tạo bài đăng mới
                  </button>
                </div>
              </div>
              <div className="p-6">
                {posts.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {posts.map((post) => (
                      <div key={post.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="mb-3">
                          <h4 className="font-semibold text-gray-900 mb-2 line-clamp-2">{post.title}</h4>
                          <p className="text-sm text-gray-600 line-clamp-2 mb-2">{post.description}</p>
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">{post.subject}</span>
                            <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">{post.category}</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                          <span className="text-xs text-gray-500">
                            {new Date(post.date).toLocaleDateString('vi-VN')}
                          </span>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => {
                                setEditingPost(post);
                                setShowPostEditor(true);
                              }}
                              className="text-blue-600 hover:text-blue-700"
                            >
                              <EditIcon className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeletePost(post.id)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <TrashIcon className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có bài đăng nào</h3>
                    <p className="text-gray-500 mb-4">Hãy tạo bài đăng đầu tiên của bạn</p>
                    <button
                      onClick={() => {
                        setEditingPost(undefined);
                        setShowPostEditor(true);
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Tạo bài đăng mới
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="bg-white rounded-lg shadow-md border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Tạo và quản lý thông báo cho học sinh</h3>
                  <button
                    onClick={() => setShowNotificationManager(true)}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    <PlusIcon className="w-4 h-4 mr-2" />
                    Tạo thông báo mới
                  </button>
                </div>
              </div>
              <div className="p-6">
                {notifications.length > 0 ? (
                  <div className="space-y-4">
                    {notifications.map((notification) => {
                      const classroom = classrooms.find(c => c.id === notification.classroom_id);
                      return (
                        <div key={notification.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <h4 className="font-semibold text-gray-900">{notification.title}</h4>
                                {notification.is_announcement && (
                                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                                    Thông báo
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-600 mb-2">{notification.content}</p>
                              <div className="flex items-center space-x-4 text-xs text-gray-500">
                                {classroom && (
                                  <span>Lớp: {classroom.name}</span>
                                )}
                                <span>{new Date(notification.created_at).toLocaleDateString('vi-VN')}</span>
                                {notification.unread_count && notification.unread_count > 0 && (
                                  <span className="text-red-600 font-medium">
                                    {notification.unread_count} chưa đọc
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <BellIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có thông báo nào</h3>
                    <p className="text-gray-500 mb-4">Hãy tạo thông báo đầu tiên cho học sinh của bạn</p>
                    <button
                      onClick={() => setShowNotificationManager(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Tạo thông báo mới
                    </button>
                  </div>
                )}
              </div>
          </div>
        )}

        {activeTab === 'students' && (
          <div className="space-y-6">
            {/* Header */}
            <div className="bg-white rounded-lg shadow-md border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Quản lý toàn bộ học sinh</h3>
                  <button 
                    onClick={() => {
                      setShowStudentManager(true);
                      setSelectedClassroom(null);
                    }}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                  >
                    <UsersIcon className="w-4 h-4 mr-2" />
                    Quản lý chi tiết
                  </button>
                </div>
                
                {/* Search and Filters */}
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="flex-1 relative">
                    <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Tìm kiếm theo tên, email, username..."
                      value={studentSearchTerm}
                      onChange={(e) => setStudentSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <select
                    value={studentFilterStatus}
                    onChange={(e) => setStudentFilterStatus(e.target.value as 'all' | 'active' | 'inactive')}
                    className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="all">Tất cả trạng thái</option>
                    <option value="active">Đang hoạt động</option>
                    <option value="inactive">Tạm dừng</option>
                  </select>
                  
                  <select
                    value={studentFilterClassroom || ''}
                    onChange={(e) => setStudentFilterClassroom(e.target.value ? Number(e.target.value) : null)}
                    className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Tất cả lớp học</option>
                    {classrooms.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Students List */}
              <div className="p-6">
                {studentsLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Đang tải danh sách học sinh...</p>
                  </div>
                ) : (() => {
                  const filteredStudents = allStudents.filter(student => {
                    const matchesSearch = !studentSearchTerm || 
                      student.full_name?.toLowerCase().includes(studentSearchTerm.toLowerCase()) ||
                      student.email?.toLowerCase().includes(studentSearchTerm.toLowerCase()) ||
                      student.username?.toLowerCase().includes(studentSearchTerm.toLowerCase());
                    
                    const matchesStatus = studentFilterStatus === 'all' || 
                      (studentFilterStatus === 'active' && student.is_active) ||
                      (studentFilterStatus === 'inactive' && !student.is_active);
                    
                    const matchesClassroom = !studentFilterClassroom ||
                      student.classrooms?.some((c: any) => c.id === studentFilterClassroom);
                    
                    return matchesSearch && matchesStatus && matchesClassroom;
                  });

                  return filteredStudents.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {filteredStudents.map((student) => (
                        <div
                          key={student.id}
                          className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900 mb-1 truncate">
                                {student.full_name || student.fullname || 'Không có tên'}
                              </h4>
                              <p className="text-sm text-gray-500 truncate" title={student.email}>
                                {student.email}
                              </p>
                              <p className="text-xs text-gray-400 mt-1">@{student.username}</p>
                            </div>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              student.is_active 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {student.is_active ? 'Hoạt động' : 'Tạm dừng'}
                            </span>
                          </div>
                          
                          {student.classrooms && student.classrooms.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                              <p className="text-xs text-gray-500 mb-2">Lớp học đang tham gia:</p>
                              <div className="flex flex-wrap gap-1">
                                {student.classrooms.map((classroom: any) => (
                                  <span
                                    key={classroom.id}
                                    className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded"
                                  >
                                    {classroom.name}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs text-gray-400">
                              Tham gia: {new Date(student.joined_at).toLocaleDateString('vi-VN')}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <UsersIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Không tìm thấy học sinh</h3>
                      <p className="text-gray-500">
                        {studentSearchTerm || studentFilterStatus !== 'all' || studentFilterClassroom
                          ? 'Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm'
                          : 'Chưa có học sinh nào trong các lớp học của bạn'}
                      </p>
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'exams' && (
          <div className="bg-white rounded-lg shadow-md border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Quản lý đề thi</h3>
                <button 
                  onClick={() => setShowExamManager(true)}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  <PlusIcon className="w-4 h-4 mr-2" />
                  Quản lý đề thi
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="text-center py-12">
                <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Quản lý đề thi</h3>
                <p className="text-gray-500 mb-4">Nhấp vào nút "Quản lý đề thi" ở trên để xem và quản lý các đề thi của bạn</p>
                <button
                  onClick={() => setShowExamManager(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Mở quản lý đề thi
                </button>
              </div>
            </div>
          </div>
        )}
            </div>
          </div>

      {/* Modals */}
        {showClassroomManager && (
        <ClassroomManager onClose={() => {
          setShowClassroomManager(false);
          fetchDashboardData();
        }} />
        )}
        
        {showPostEditor && (
          <PostEditor 
            post={editingPost}
            onSave={handleSavePost}
            onClose={() => {
              setShowPostEditor(false);
              setEditingPost(undefined);
            }}
          />
        )}
        
        {showNotificationManager && (
        <NotificationManager onClose={() => {
          setShowNotificationManager(false);
          fetchDashboardData();
        }} />
        )}
        
        {showStudentManager && (
          <StudentManager 
            onClose={() => {
              setShowStudentManager(false);
              setSelectedClassroom(null);
            }}
            initialClassroomId={selectedClassroom}
          />
        )}
      
        {showExamManager && (
          <TeacherExamManager onClose={() => setShowExamManager(false)} />
        )}
    </div>
  );
};

export default TeacherDashboard;
