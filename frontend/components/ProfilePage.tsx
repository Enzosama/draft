import React from 'react';
import { User } from '../data/types';

interface ProfilePageProps {
  user: User;
  onClose: () => void;
}

const ProfilePage: React.FC<ProfilePageProps> = ({ user, onClose }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6 border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-800">Tài khoản của tôi</h2>
        <button
          onClick={onClose}
          className="bg-[#1e40af] text-white px-5 py-2 rounded-md text-sm font-medium hover:bg-blue-900 transition-colors duration-300"
        >
          &larr; Quay lại trang chủ
        </button>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Left Panel: Avatar and Name */}
        <div className="flex-shrink-0 flex flex-col items-center md:items-start md:w-1/3">
          <div className="w-32 h-32 rounded-full bg-gray-200 mb-4 flex items-center justify-center">
            {/* Placeholder for avatar image */}
            <span className="text-5xl text-gray-500">{user.name.charAt(0)}</span>
          </div>
          <h3 className="text-xl font-bold text-gray-900">{user.name}</h3>
          <p className="text-gray-500">{user.email}</p>
        </div>

        {/* Right Panel: Information and Activity */}
        <div className="flex-1">
          <div className="mb-8">
            <h4 className="text-lg font-semibold text-gray-700 mb-3">Thông tin cá nhân</h4>
            <div className="bg-gray-50 p-4 rounded-md space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Họ và tên:</span>
                <span className="font-medium text-gray-800">{user.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Email:</span>
                <span className="font-medium text-gray-800">{user.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Ngày tham gia:</span>
                <span className="font-medium text-gray-800">{new Date().toLocaleDateString('vi-VN')}</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-lg font-semibold text-gray-700 mb-3">Lịch sử hoạt động</h4>
            <div className="bg-gray-50 p-6 rounded-md text-center">
              <p className="text-gray-500">Chưa có hoạt động nào.</p>
              <p className="text-sm text-gray-400 mt-1">Lịch sử làm bài và tài liệu đã tải sẽ được hiển thị ở đây.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;