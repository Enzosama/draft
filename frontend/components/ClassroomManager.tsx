import React, { useState, useEffect } from 'react';
import { Classroom } from '../data/types';
import { PlusIcon, UsersIcon, TrashIcon, EditIcon, CopyIcon } from './icons';

interface ClassroomManagerProps {
  onClose: () => void;
}

const ClassroomManager: React.FC<ClassroomManagerProps> = ({ onClose }) => {
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingClassroom, setEditingClassroom] = useState<Classroom | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    subject: ''
  });

  useEffect(() => {
    fetchClassrooms();
  }, []);

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
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClassroom = async () => {
    try {
      const response = await fetch('/api/teacher/classrooms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const newClassroom = await response.json();
        setClassrooms([...classrooms, newClassroom]);
        setShowCreateModal(false);
        resetForm();
      }
    } catch (error) {
      console.error('Error creating classroom:', error);
    }
  };

  const handleUpdateClassroom = async () => {
    if (!editingClassroom) return;
    
    try {
      const response = await fetch(`/api/teacher/classrooms/${editingClassroom.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const updated = await response.json();
        setClassrooms(classrooms.map(c => c.id === updated.id ? updated : c));
        setEditingClassroom(null);
        resetForm();
      }
    } catch (error) {
      console.error('Error updating classroom:', error);
    }
  };

  const handleDeleteClassroom = async (id: number) => {
    if (!confirm('Bạn có chắc chắn muốn xóa lớp học này?')) return;
    
    try {
      const response = await fetch(`/api/teacher/classrooms/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        setClassrooms(classrooms.filter(c => c.id !== id));
      }
    } catch (error) {
      console.error('Error deleting classroom:', error);
    }
  };

  const copyJoinCode = (code: string) => {
    navigator.clipboard.writeText(code);
    alert('Mã tham gia đã được sao chép!');
  };

  const resetForm = () => {
    setFormData({ name: '', description: '', subject: '' });
  };

  const openEditModal = (classroom: Classroom) => {
    setEditingClassroom(classroom);
    setFormData({
      name: classroom.name,
      description: classroom.description || '',
      subject: classroom.subject || ''
    });
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
        className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Quản lý lớp học</h2>
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
            <h3 className="text-lg font-medium text-gray-900">Danh sách lớp học</h3>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Tạo lớp học mới
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classrooms.map((classroom) => (
              <div key={classroom.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <h4 className="text-lg font-medium text-gray-900">{classroom.name}</h4>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => copyJoinCode(classroom.code)}
                      className="text-blue-600 hover:text-blue-800"
                      title="Sao chép mã tham gia"
                    >
                      <CopyIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => openEditModal(classroom)}
                      className="text-gray-600 hover:text-gray-800"
                      title="Chỉnh sửa"
                    >
                      <EditIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteClassroom(classroom.id)}
                      className="text-red-600 hover:text-red-800"
                      title="Xóa"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <p className="text-gray-600 text-sm mb-2">{classroom.description}</p>
                {classroom.subject && (
                  <div className="flex items-center text-sm text-gray-500 mb-2">
                    <span className="font-medium">Môn:</span>
                    <span className="ml-1">{classroom.subject}</span>
                  </div>
                )}
                <div className="flex items-center text-sm text-gray-500 mb-3">
                  <span className="font-medium">Mã tham gia:</span>
                  <span className="ml-1 font-mono bg-gray-100 px-2 py-1 rounded">{classroom.code}</span>
                </div>
                
                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                  <div className="flex items-center text-sm text-gray-500">
                    <UsersIcon className="w-4 h-4 mr-1" />
                    <span>{classroom.student_count || 0} học sinh</span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    classroom.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {classroom.is_active ? 'Đang hoạt động' : 'Không hoạt động'}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {classrooms.length === 0 && (
            <div className="text-center py-12">
              <UsersIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có lớp học nào</h3>
              <p className="text-gray-500">Hãy tạo lớp học đầu tiên của bạn</p>
            </div>
          )}
        </div>

        {/* Create/Edit Modal */}
        {(showCreateModal || editingClassroom) && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60 p-4"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setShowCreateModal(false);
                setEditingClassroom(null);
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
                  {editingClassroom ? 'Chỉnh sửa lớp học' : 'Tạo lớp học mới'}
                </h3>
              </div>
              
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tên lớp học <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="VD: Lớp Toán 10A1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mô tả
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    rows={3}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Mô tả về lớp học"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Môn học <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.subject}
                    onChange={(e) => setFormData({...formData, subject: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Chọn môn học</option>
                    <option value="Toán học">Toán học</option>
                    <option value="Vật lý">Vật lý</option>
                    <option value="Hóa học">Hóa học</option>
                    <option value="Sinh học">Sinh học</option>
                    <option value="Ngữ văn">Ngữ văn</option>
                    <option value="Lịch sử">Lịch sử</option>
                    <option value="Địa lý">Địa lý</option>
                    <option value="Tiếng Anh">Tiếng Anh</option>
                  </select>
                </div>
                
              </div>
              
              <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingClassroom(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Hủy
                </button>
                <button
                  onClick={editingClassroom ? handleUpdateClassroom : handleCreateClassroom}
                  disabled={!formData.name}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {editingClassroom ? 'Cập nhật' : 'Tạo lớp học'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClassroomManager;