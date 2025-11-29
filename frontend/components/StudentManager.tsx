import React, { useState, useEffect } from 'react';
import { UsersIcon, UserPlusIcon, TrashIcon, SearchIcon, FilterIcon, XIcon } from './icons';

interface Student {
  id: number;
  username: string;
  email: string;
  full_name: string;
  joined_at: string;
  is_active: boolean;
  classrooms?: Classroom[]; // Lớp học đang tham gia
}

interface Classroom {
  id: number;
  name: string;
  subject: string;
  grade_level: string;
}

interface StudentManagerProps {
  onClose: () => void;
  initialClassroomId?: number | null;
}

const StudentManager: React.FC<StudentManagerProps> = ({ onClose, initialClassroomId }) => {
  const [students, setStudents] = useState<Student[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [selectedClassroom, setSelectedClassroom] = useState<number | null>(initialClassroomId || null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');

  useEffect(() => {
    fetchClassrooms();
  }, []);

  useEffect(() => {
    if (initialClassroomId) {
      setSelectedClassroom(initialClassroomId);
    }
  }, [initialClassroomId]);

  useEffect(() => {
    if (selectedClassroom) {
      fetchStudents(selectedClassroom);
    }
  }, [selectedClassroom]);

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Demo mode if no token
      if (!token) {
        const mockClassrooms = [
          { id: 1, name: 'Lớp Toán 10A1', subject: 'Toán học', grade_level: '10' },
          { id: 2, name: 'Lớp Vật lý 11B2', subject: 'Vật lý', grade_level: '11' }
        ];
        setClassrooms(mockClassrooms);
        setSelectedClassroom(mockClassrooms[0].id);
        setLoading(false);
        return;
      }

      const response = await fetch('/api/teacher/classrooms', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setClassrooms(data);
        if (data.length > 0) {
          setSelectedClassroom(data[0].id);
        } else {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error('Error fetching classrooms:', error);
      setLoading(false);
    }
  };

  const fetchStudents = async (classroomId: number) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // Demo mode if no token
      if (!token) {
        const mockStudents = [
          {
            id: 1,
            username: 'student1',
            email: 'student1@example.com',
            full_name: 'Nguyễn Văn Anh Tuấn',
            joined_at: new Date().toISOString(),
            is_active: true,
            classrooms: [
              { id: 1, name: 'Lớp Toán 10A1', subject: 'Toán học', grade_level: '10' },
              { id: 2, name: 'Lớp Vật lý 11B2', subject: 'Vật lý', grade_level: '11' }
            ]
          },
          {
            id: 2,
            username: 'student2',
            email: 'student2.verylongemail@example.com',
            full_name: 'Trần Thị Bích Ngọc',
            joined_at: new Date().toISOString(),
            is_active: true,
            classrooms: [
              { id: 1, name: 'Lớp Toán 10A1', subject: 'Toán học', grade_level: '10' }
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
              { id: 2, name: 'Lớp Vật lý 11B2', subject: 'Vật lý', grade_level: '11' }
            ]
          }
        ];
        setStudents(mockStudents);
        setLoading(false);
        return;
      }

      const response = await fetch(`/api/teacher/classrooms/${classroomId}/students`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Thêm thông tin lớp học hiện tại vào mỗi học sinh
        const currentClassroomData = classrooms.find(c => c.id === classroomId);
        const studentsWithClassroom = (Array.isArray(data) ? data : []).map((student: Student) => ({
          ...student,
          classrooms: currentClassroomData ? [currentClassroomData] : []
        }));
        setStudents(studentsWithClassroom);
      } else {
        setStudents([]);
      }
    } catch (error) {
      console.error('Error fetching students:', error);
      setStudents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveStudent = async (studentId: number) => {
    if (!selectedClassroom) return;
    if (!confirm('Bạn có chắc chắn muốn xóa học sinh này khỏi lớp học?')) return;

    try {
      const response = await fetch(`/api/teacher/classrooms/${selectedClassroom}/students/${studentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        setStudents(students.filter(s => s.id !== studentId));
      }
    } catch (error) {
      console.error('Error removing student:', error);
    }
  };

  const handleToggleStudentStatus = async (studentId: number, currentStatus: boolean) => {
    if (!selectedClassroom) return;

    try {
      const response = await fetch(`/api/teacher/classrooms/${selectedClassroom}/students/${studentId}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        setStudents(students.map(s => 
          s.id === studentId ? { ...s, is_active: !currentStatus } : s
        ));
      }
    } catch (error) {
      console.error('Error toggling student status:', error);
    }
  };

  const handleAddStudent = async () => {
    if (!selectedClassroom) return;
    
    const email = prompt('Nhập email của học sinh:');
    if (!email) return;

    try {
      const response = await fetch(`/api/teacher/classrooms/${selectedClassroom}/students`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ email })
      });
      
      if (response.ok) {
        const newStudent = await response.json();
        setStudents([...students, newStudent]);
        alert('Đã thêm học sinh vào lớp học!');
      } else {
        const error = await response.json();
        alert(`Lỗi: ${error.detail || 'Không thể thêm học sinh'}`);
      }
    } catch (error) {
      console.error('Error adding student:', error);
      alert('Có lỗi xảy ra khi thêm học sinh');
    }
  };

  const filteredStudents = students.filter(student => {
    const matchesSearch = student.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         student.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         student.email.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterStatus === 'all' || 
                         (filterStatus === 'active' && student.is_active) ||
                         (filterStatus === 'inactive' && !student.is_active);
    
    return matchesSearch && matchesFilter;
  });

  const currentClassroom = classrooms.find(c => c.id === selectedClassroom);

  // Helper function to truncate text
  const truncateText = (text: string, maxLength: number = 25) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
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
          <h2 className="text-xl font-semibold text-gray-900">Quản lý học sinh</h2>
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
          {/* Classroom Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Chọn lớp học</label>
            {classrooms.length > 0 ? (
              <select
                value={selectedClassroom || ''}
                onChange={(e) => setSelectedClassroom(parseInt(e.target.value))}
                className="w-full md:w-64 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {classrooms.map((classroom) => (
                  <option key={classroom.id} value={classroom.id}>
                    {classroom.name} - {classroom.subject} {classroom.grade_level ? `(${classroom.grade_level})` : ''}
                  </option>
                ))}
              </select>
            ) : (
              <div className="text-center py-8 border border-gray-200 rounded-md bg-gray-50">
                <UsersIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có lớp học nào</h3>
                <p className="text-gray-500 mb-4">Hãy tạo lớp học trước khi quản lý học sinh</p>
              </div>
            )}
          </div>

          {selectedClassroom && (
            <>
              {/* Header with Add Student Button */}
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    Danh sách học sinh - {currentClassroom?.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {filteredStudents.length} học sinh trong lớp
                  </p>
                </div>
                <button
                  onClick={handleAddStudent}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  <UserPlusIcon className="w-4 h-4 mr-2" />
                  Thêm học sinh
                </button>
              </div>

              {/* Search and Filter */}
              <div className="flex flex-col md:flex-row gap-4 mb-6">
                <div className="relative flex-1">
                  <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Tìm kiếm học sinh..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="relative">
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value as 'all' | 'active' | 'inactive')}
                    className="appearance-none pl-10 pr-8 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Tất cả trạng thái</option>
                    <option value="active">Đang hoạt động</option>
                    <option value="inactive">Không hoạt động</option>
                  </select>
                  <FilterIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
                </div>
              </div>

              {/* Students List - Card Layout */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredStudents.map((student) => (
                  <div 
                    key={student.id} 
                    className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    {/* Student Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <h4 
                          className="text-base font-semibold text-gray-900 truncate" 
                          title={student.full_name}
                        >
                          {truncateText(student.full_name, 20)}
                        </h4>
                        <p 
                          className="text-xs text-gray-500 mt-1 truncate" 
                          title={student.email}
                        >
                          {truncateText(student.email, 30)}
                        </p>
                      </div>
                      <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full flex-shrink-0 ${
                        student.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {student.is_active ? 'Hoạt động' : 'Tạm khóa'}
                      </span>
                    </div>

                    {/* Classrooms List */}
                    <div className="mb-3">
                      <p className="text-xs font-medium text-gray-700 mb-2">Lớp học đang tham gia:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {student.classrooms && student.classrooms.length > 0 ? (
                          student.classrooms.map((classroom) => (
                            <span
                              key={classroom.id}
                              className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-blue-50 text-blue-700 border border-blue-200"
                              title={`${classroom.name} - ${classroom.subject}`}
                            >
                              {truncateText(classroom.name, 15)}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-gray-400 italic">Chưa có lớp học</span>
                        )}
                      </div>
                    </div>

                    {/* Student Info */}
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-3 pt-2 border-t border-gray-100">
                      <span>@{student.username}</span>
                      <span>{new Date(student.joined_at).toLocaleDateString('vi-VN')}</span>
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-2 pt-2 border-t border-gray-100">
                      <button
                        onClick={() => handleToggleStudentStatus(student.id, student.is_active)}
                        className={`flex-1 text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${
                          student.is_active 
                            ? 'text-yellow-700 bg-yellow-50 hover:bg-yellow-100 border border-yellow-200' 
                            : 'text-green-700 bg-green-50 hover:bg-green-100 border border-green-200'
                        }`}
                      >
                        {student.is_active ? 'Vô hiệu hóa' : 'Kích hoạt'}
                      </button>
                      <button
                        onClick={() => handleRemoveStudent(student.id)}
                        className="px-3 py-1.5 text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 rounded-md border border-red-200 transition-colors"
                        title="Xóa khỏi lớp học"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {filteredStudents.length === 0 && (
                <div className="text-center py-12">
                  <UsersIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {searchTerm || filterStatus !== 'all' ? 'Không tìm thấy học sinh' : 'Chưa có học sinh nào'}
                  </h3>
                  <p className="text-gray-500">
                    {searchTerm || filterStatus !== 'all' 
                      ? 'Thử thay đổi điều kiện tìm kiếm' 
                      : 'Hãy thêm học sinh vào lớp học'
                  }
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentManager;