import React, { useState, useEffect } from 'react';
import { TeacherPost } from '../data/types';
import { XIcon, SaveIcon, UploadIcon } from './icons';

interface PostEditorProps {
  post?: TeacherPost;
  onSave: (post: Partial<TeacherPost>) => void;
  onClose: () => void;
}

const PostEditor: React.FC<PostEditorProps> = ({ post, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    title: post?.title || '',
    author: post?.author || '',
    subject: post?.subject || '',
    category: post?.category || 'Tài Liệu',
    description: post?.description || '',
    date: post?.date || new Date().toISOString().split('T')[0],
    fileUrl: post?.fileUrl || '',
    classroom_id: post?.classroom_id || null as number | null
  });
  const [loading, setLoading] = useState(false);
  const [classrooms, setClassrooms] = useState<any[]>([]);

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
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const endpoint = post ? `/api/teacher/posts/${post.id}` : '/api/teacher/posts';
      const method = post ? 'PUT' : 'POST';
      
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const savedPost = await response.json();
        onSave(savedPost);
        onClose();
      } else {
        const error = await response.json();
        alert(`Lỗi: ${error.detail || 'Không thể lưu bài đăng'}`);
      }
    } catch (error) {
      console.error('Error saving post:', error);
      alert('Có lỗi xảy ra khi lưu bài đăng');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // In a real app, you would upload to R2 storage here
      const fileUrl = URL.createObjectURL(file);
      setFormData({...formData, fileUrl});
    }
  };

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
        className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {post ? 'Chỉnh sửa bài đăng' : 'Tạo bài đăng mới'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <XIcon className="w-6 h-6" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tiêu đề <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                placeholder="Nhập tiêu đề bài đăng"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tác giả <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => setFormData({...formData, author: e.target.value})}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                placeholder="Tên tác giả"
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
                required
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Thể loại <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="Tài Liệu">Tài Liệu</option>
                <option value="Đề Thi">Đề Thi</option>
                <option value="Bài Giảng">Bài Giảng</option>
                <option value="Bài Tập">Bài Tập</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ngày đăng
              </label>
              <input
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({...formData, date: e.target.value})}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Lớp học (tùy chọn)
              </label>
              <select
                value={formData.classroom_id || ''}
                onChange={(e) => setFormData({...formData, classroom_id: e.target.value ? parseInt(e.target.value) : null})}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Không chọn lớp</option>
                {classrooms.map((classroom) => (
                  <option key={classroom.id} value={classroom.id}>
                    {classroom.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mô tả <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              rows={4}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              placeholder="Mô tả chi tiết về bài đăng"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              File đính kèm
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
                accept=".pdf,.doc,.docx,.ppt,.pptx,.txt"
              />
              <label
                htmlFor="file-upload"
                className="flex items-center px-4 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50"
              >
                <UploadIcon className="w-4 h-4 mr-2" />
                Chọn file
              </label>
              {formData.fileUrl && (
                <span className="text-sm text-gray-600 truncate max-w-xs">
                  {formData.fileUrl.split('/').pop()}
                </span>
              )}
            </div>
            {formData.fileUrl && (
              <div className="mt-2">
                <a
                  href={formData.fileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Xem file hiện tại
                </a>
              </div>
            )}
          </div>
        </form>

        <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Đang lưu...
              </>
            ) : (
              <>
                <SaveIcon className="w-4 h-4 mr-2" />
                Lưu bài đăng
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PostEditor;