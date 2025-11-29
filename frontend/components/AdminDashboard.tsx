import React, { useState, useEffect } from 'react';
import { User } from '../data/types';
import { PlusIcon, UserIcon, UserGroupIcon, ChartBarIcon, CogIcon, CheckIcon, XIcon } from './icons';

interface AdminDashboardProps {
  currentUser: User;
  onClose: () => void;
}

interface Teacher {
  id: number;
  fullname: string;
  email: string;
  phone: string;
  is_active: boolean;
  created_at: string;
  classroom_count: number;
}

interface DashboardStats {
  totalTeachers: number;
  activeTeachers: number;
  totalStudents: number;
  totalClassrooms: number;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ currentUser, onClose }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'teachers' | 'classrooms' | 'posts' | 'exams' | 'settings'>('overview');
  const [stats, setStats] = useState<DashboardStats>({
    totalTeachers: 0,
    activeTeachers: 0,
    totalStudents: 0,
    totalClassrooms: 0
  });
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddTeacherModal, setShowAddTeacherModal] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // Fetch all teachers
      const teachersRes = await fetch('/api/admin/teachers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (teachersRes.ok) {
        const teachersData = await teachersRes.json();
        setTeachers(teachersData);
        
        const activeTeachers = teachersData.filter((t: Teacher) => t.is_active).length;
        const totalClassrooms = teachersData.reduce((sum, teacher: Teacher) => sum + teacher.classroom_count, 0);
        
        setStats({
          totalTeachers: teachersData.length,
          activeTeachers,
          totalStudents: 0, // Would need separate API call
          totalClassrooms
        });
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleTeacherStatus = async (teacherId: number, currentStatus: boolean) => {
    try {
      const response = await fetch(`/api/admin/teachers/${teacherId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ is_active: !currentStatus })
      });
      
      if (response.ok) {
        fetchDashboardData(); // Refresh data
      }
    } catch (error) {
      console.error('Error updating teacher status:', error);
    }
  };

  const StatCard: React.FC<{ title: string; value: number; icon: React.ReactNode; color: string }> = ({ title, value, icon, color }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  const AddTeacherModal: React.FC = () => {
    const [formData, setFormData] = useState({
      fullname: '',
      email: '',
      phone: '',
      password: ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      try {
        const response = await fetch('/api/admin/teachers', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(formData)
        });
        
        if (response.ok) {
          setShowAddTeacherModal(false);
          fetchDashboardData();
          setFormData({ fullname: '', email: '', phone: '', password: '' });
        }
      } catch (error) {
        console.error('Error adding teacher:', error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Thêm giáo viên mới</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Họ tên</label>
              <input
                type="text"
                value={formData.fullname}
                onChange={(e) => setFormData({...formData, fullname: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Số điện thoại</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Mật khẩu</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
            <div className="flex space-x-3">
              <button
                type="submit"
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
              >
                Thêm giáo viên
              </button>
              <button
                type="button"
                onClick={() => setShowAddTeacherModal(false)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400"
              >
                Hủy
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

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
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Bảng điều khiển quản trị</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Xin chào, {currentUser.name}</span>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-500"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', label: 'Tổng quan', icon: <ChartBarIcon className="w-4 h-4" /> },
              { id: 'teachers', label: 'Giáo viên', icon: <UserIcon className="w-4 h-4" /> },
              { id: 'classrooms', label: 'Lớp học', icon: <UserGroupIcon className="w-4 h-4" /> },
              { id: 'posts', label: 'Bài đăng', icon: <DocumentTextIcon className="w-4 h-4" /> },
              { id: 'exams', label: 'Đề thi', icon: <DocumentTextIcon className="w-4 h-4" /> },
              { id: 'settings', label: 'Cài đặt', icon: <CogIcon className="w-4 h-4" /> }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="Tổng số giáo viên"
                value={stats.totalTeachers}
                icon={<UserIcon className="w-6 h-6 text-white" />}
                color="bg-blue-500"
              />
              <StatCard
                title="Giáo viên đang hoạt động"
                value={stats.activeTeachers}
                icon={<UserIcon className="w-6 h-6 text-white" />}
                color="bg-green-500"
              />
              <StatCard
                title="Tổng số lớp học"
                value={stats.totalClassrooms}
                icon={<UserGroupIcon className="w-6 h-6 text-white" />}
                color="bg-purple-500"
              />
              <StatCard
                title="Tổng số học sinh"
                value={stats.totalStudents}
                icon={<UserGroupIcon className="w-6 h-6 text-white" />}
                color="bg-orange-500"
              />
            </div>
          </div>
        )}

        {activeTab === 'posts' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Quản lý bài đăng (toàn hệ thống)</h3>
            </div>
            <AdminPosts />
          </div>
        )}

        {activeTab === 'exams' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Quản lý đề thi (toàn hệ thống)</h3>
            </div>
            <AdminExams />
          </div>
        )}

        {activeTab === 'teachers' && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Quản lý giáo viên</h3>
                <button
                  onClick={() => setShowAddTeacherModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
                >
                  <PlusIcon className="w-4 h-4 mr-2" />
                  Thêm giáo viên
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {teachers.map((teacher) => (
                  <div key={teacher.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold text-gray-900">{teacher.fullname}</h4>
                        <p className="text-sm text-gray-500">{teacher.email}</p>
                        <p className="text-sm text-gray-500">{teacher.phone}</p>
                        <p className="text-sm text-gray-400">{teacher.classroom_count} lớp học</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => toggleTeacherStatus(teacher.id, teacher.is_active)}
                          className={`px-3 py-1 text-sm rounded-full ${
                            teacher.is_active
                              ? 'bg-green-100 text-green-800 hover:bg-green-200'
                              : 'bg-red-100 text-red-800 hover:bg-red-200'
                          }`}
                        >
                          {teacher.is_active ? (
                            <><CheckIcon className="w-4 h-4 inline mr-1" /> Đang hoạt động</>
                          ) : (
                            <><XIcon className="w-4 h-4 inline mr-1" /> Không hoạt động</>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'classrooms' && <div className="bg-white rounded-lg shadow-md p-6">Quản lý lớp học</div>}
        {activeTab === 'settings' && <div className="bg-white rounded-lg shadow-md p-6">Cài đặt hệ thống</div>}
      </div>

      {showAddTeacherModal && <AddTeacherModal />}
    </div>
  );
};

const AdminPosts: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const token = localStorage.getItem('token') || '';
  useEffect(() => { (async () => {
    const res = await fetch('/api/posts', { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) { const data = await res.json(); setItems(data.data || data); }
  })(); }, []);
  const remove = async (id: number) => {
    if (!confirm('Xóa bài đăng này?')) return;
    const res = await fetch(`/api/admin/posts/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
    if (res.ok || res.status === 204) setItems(items.filter(i => i.id !== id));
  };
  return (
    <div className="p-6 space-y-3">
      {items.map(p => (
        <div key={p.id} className="flex items-center justify-between border border-gray-200 rounded p-3">
          <div>
            <div className="font-medium text-gray-900">{p.title}</div>
            <div className="text-sm text-gray-500">{p.subject} • {p.category}</div>
          </div>
          <button onClick={() => remove(p.id)} className="text-red-600 hover:text-red-800 text-sm px-3 py-1 rounded-md bg-red-100 hover:bg-red-200">
            Xóa
          </button>
        </div>
      ))}
    </div>
  );
};

const AdminExams: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const token = localStorage.getItem('token') || '';
  useEffect(() => { (async () => {
    const res = await fetch('/api/exams?page=1&page_size=50', { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) { const data = await res.json(); setItems(data.data || []); }
  })(); }, []);
  const remove = async (id: number) => {
    if (!confirm('Xóa đề thi này?')) return;
    const res = await fetch(`/api/exams/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
    if (res.ok || res.status === 204) setItems(items.filter(i => i.id !== id));
  };
  return (
    <div className="p-6 space-y-3">
      {items.map(e => (
        <div key={e.id} className="flex items-center justify-between border border-gray-200 rounded p-3">
          <div>
            <div className="font-medium text-gray-900">{e.title}</div>
            <div className="text-sm text-gray-500">{e.author} • {e.subject}</div>
          </div>
          <button onClick={() => remove(e.id)} className="text-red-600 hover:text-red-800 text-sm px-3 py-1 rounded-md bg-red-100 hover:bg-red-200">
            Xóa
          </button>
        </div>
      ))}
    </div>
  );
};

export default AdminDashboard;
