import React, { useEffect, useState } from 'react';
import { SaveIcon, TrashIcon, PlusIcon, UploadIcon, XIcon } from './icons';

interface ExamItem {
  id: number;
  title: string;
  author: string;
  subject: string;
  file_url?: string;
  answer_file_url?: string;
  created_at: string;
}

interface TeacherExamManagerProps {
  onClose: () => void;
}

const TeacherExamManager: React.FC<TeacherExamManagerProps> = ({ onClose }) => {
  const [exams, setExams] = useState<ExamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: '', author: '', subject: '' });
  const token = localStorage.getItem('token') || '';

  useEffect(() => { fetchExams(); }, []);

  const fetchExams = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/teacher/exams?page=1&page_size=50', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setExams(data.data || []);
      }
    } finally { setLoading(false); }
  };

  const createExam = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('/api/teacher/exams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ ...form })
    });
    if (res.ok) { setShowCreate(false); setForm({ title: '', author: '', subject: '' }); fetchExams(); }
  };

  const deleteExamAdmin = async (id: number) => {
    if (!confirm('Xóa đề thi này?')) return;
    const res = await fetch(`/api/teacher/exams/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
    if (res.status === 204 || res.ok) { setExams(exams.filter(e => e.id !== id)); }
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
        className="bg-white rounded-lg w-full max-w-5xl max-h-[90vh] overflow-hidden relative"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Quản lý đề thi</h2>
          <button 
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onClose();
            }} 
            className="text-gray-400 hover:text-gray-600 transition-colors p-2 hover:bg-gray-100 rounded-md"
            type="button"
            aria-label="Đóng"
          >
            <XIcon className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium text-gray-900">Danh sách đề thi</h3>
            <button onClick={() => setShowCreate(true)} className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              <PlusIcon className="w-4 h-4 mr-2" /> Tạo đề thi
            </button>
          </div>

          <div className="space-y-4">
            {exams.map((exam) => (
              <div key={exam.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900">{exam.title}</h4>
                    <p className="text-sm text-gray-500">{exam.author} • {exam.subject}</p>
                    <p className="text-xs text-gray-400">{new Date(exam.created_at).toLocaleDateString('vi-VN')}</p>
                  </div>
                  <div className="flex space-x-2">
                    <button onClick={() => deleteExamAdmin(exam.id)} className="text-red-600 hover:text-red-800 text-sm px-3 py-1 rounded-md bg-red-100 hover:bg-red-200">
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {showCreate && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60 p-4"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setShowCreate(false);
              }
            }}
          >
            <div 
              className="bg-white rounded-lg w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Tạo đề thi mới</h3>
              </div>
              <form onSubmit={createExam} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tiêu đề</label>
                  <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="w-full border border-gray-300 rounded-md px-3 py-2" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tác giả</label>
                  <input type="text" value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} className="w-full border border-gray-300 rounded-md px-3 py-2" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Môn học</label>
                  <input type="text" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className="w-full border border-gray-300 rounded-md px-3 py-2" required />
                </div>
                <div className="flex justify-end space-x-3 p-2">
                  <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">Hủy</button>
                  <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"><SaveIcon className="w-4 h-4 mr-2"/> Tạo</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeacherExamManager;
