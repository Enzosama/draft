import React, { useState, useEffect } from 'react';
import { Notification } from '../data/types';
import { PlusIcon, BellIcon, TrashIcon, EditIcon, SendIcon } from './icons';

interface NotificationManagerProps {
  onClose: () => void;
}

const NotificationManager: React.FC<NotificationManagerProps> = ({ onClose }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingNotification, setEditingNotification] = useState<Notification | null>(null);
  const [classrooms, setClassrooms] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    classroom_id: null as number | null,
    is_announcement: false
  });

  useEffect(() => {
    fetchNotifications();
    fetchClassrooms();
  }, []);

  const fetchNotifications = async () => {
    try {
      // Fetch all classrooms first
      const classroomsRes = await fetch('/api/teacher/classrooms', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const classrooms = classroomsRes.ok ? await classroomsRes.json() : [];
      
      // Fetch notifications from all classrooms
      const allNotifications: Notification[] = [];
      for (const classroom of classrooms) {
        try {
          const notifRes = await fetch(`/api/teacher/notifications/classroom/${classroom.id}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
          });
          if (notifRes.ok) {
            const notifs = await notifRes.json();
            allNotifications.push(...(Array.isArray(notifs) ? notifs : []));
          }
        } catch (e) {
          console.error('Error fetching notifications for classroom', classroom.id, e);
        }
      }
      setNotifications(allNotifications);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchClassrooms = async () => {
    try {
      const response = await fetch('/api/teacher/classrooms', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setClassrooms(data);
      }
    } catch (error) {
      console.error('Error fetching classrooms:', error);
    }
  };

  const handleCreateNotification = async () => {
    try {
      const response = await fetch('/api/teacher/notifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const newNotification = await response.json();
        setNotifications([newNotification, ...notifications]);
        setShowCreateModal(false);
        resetForm();
      }
    } catch (error) {
      console.error('Error creating notification:', error);
    }
  };

  const handleUpdateNotification = async () => {
    if (!editingNotification) return;
    
    try {
      const response = await fetch(`/api/teacher/notifications/${editingNotification.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const updated = await response.json();
        setNotifications(notifications.map(n => n.id === updated.id ? updated : n));
        setEditingNotification(null);
        resetForm();
      }
    } catch (error) {
      console.error('Error updating notification:', error);
    }
  };

  const handleDeleteNotification = async (id: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa thông báo này?')) return;
    
    try {
      const response = await fetch(`/api/teacher/notifications/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        setNotifications(notifications.filter(n => n.id !== id));
      }
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      classroom_id: null,
      is_announcement: false
    });
  };

  const openEditModal = (notification: Notification) => {
    setEditingNotification(notification);
    setFormData({
      title: notification.title,
      content: notification.content,
      classroom_id: notification.classroom_id,
      is_announcement: notification.is_announcement || false
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div 
        className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Quản lý thông báo</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-gray-900">Danh sách thông báo</h3>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Tạo thông báo mới
            </button>
          </div>

          <div className="space-y-4">
            {notifications.map((notification) => {
              const classroom = classrooms.find(c => c.id === notification.classroom_id);
              return (
                <div key={notification.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="text-lg font-medium text-gray-900">{notification.title}</h4>
                        {notification.is_announcement && (
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                            Thông báo
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 mb-3">{notification.content}</p>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        {classroom && (
                          <span><span className="font-medium">Lớp:</span> {classroom.name}</span>
                        )}
                        <span><span className="font-medium">Ngày tạo:</span> {formatDate(notification.created_at)}</span>
                        {notification.unread_count !== undefined && notification.unread_count > 0 && (
                          <span className="text-red-600 font-medium">
                            {notification.unread_count} chưa đọc
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <button
                        onClick={() => openEditModal(notification)}
                        className="text-blue-600 hover:text-blue-700 p-2 hover:bg-blue-50 rounded"
                        title="Chỉnh sửa"
                      >
                        <EditIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteNotification(notification.id)}
                        className="text-red-600 hover:text-red-700 p-2 hover:bg-red-50 rounded"
                        title="Xóa"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {notifications.length === 0 && (
            <div className="text-center py-12">
              <BellIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có thông báo nào</h3>
              <p className="text-gray-500">Hãy tạo thông báo đầu tiên của bạn</p>
            </div>
          )}
        </div>

        {/* Create/Edit Modal */}
        {(showCreateModal || editingNotification) && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60 p-4"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setShowCreateModal(false);
                setEditingNotification(null);
                resetForm();
              }
            }}
          >
            <div 
              className="bg-white rounded-lg w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  {editingNotification ? 'Chỉnh sửa thông báo' : 'Tạo thông báo mới'}
                </h3>
              </div>
              
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tiêu đề <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập tiêu đề thông báo"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nội dung <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={formData.content}
                    onChange={(e) => setFormData({...formData, content: e.target.value})}
                    rows={4}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nhập nội dung thông báo"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Gửi đến lớp học <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.classroom_id || ''}
                    onChange={(e) => setFormData({...formData, classroom_id: e.target.value ? parseInt(e.target.value) : null})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Chọn lớp học</option>
                    {classrooms.map((classroom) => (
                      <option key={classroom.id} value={classroom.id}>
                        {classroom.name} {classroom.subject ? `(${classroom.subject})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_announcement"
                    checked={formData.is_announcement}
                    onChange={(e) => setFormData({...formData, is_announcement: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_announcement" className="ml-2 block text-sm text-gray-700">
                    Đánh dấu là thông báo quan trọng
                  </label>
                </div>
              </div>
              
              <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingNotification(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Hủy
                </button>
                <button
                  onClick={editingNotification ? handleUpdateNotification : handleCreateNotification}
                  disabled={!formData.title || !formData.content || !formData.classroom_id}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <SendIcon className="w-4 h-4 mr-2" />
                  {editingNotification ? 'Cập nhật' : 'Gửi thông báo'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationManager;