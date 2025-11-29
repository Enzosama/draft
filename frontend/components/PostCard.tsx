import React from 'react';
import { Post, Category } from '../data/types';
import { EyeIcon, DownloadIcon, ChatAltIcon } from './icons';

interface PostCardProps {
  post: Post;
  onAction: (post: Post) => void;
}

const categoryStyles = {
  [Category.EXAM]: {
    borderColor: 'border-blue-500',
    tagBg: 'bg-blue-100',
    tagText: 'text-blue-800',
    buttonText: 'Xem đề',
  },
  [Category.MATERIAL]: {
    borderColor: 'border-green-500',
    tagBg: 'bg-green-100',
    tagText: 'text-green-800',
    buttonText: 'Xem tài liệu',
  },
  [Category.MOCK_TEST]: {
    borderColor: 'border-purple-500',
    tagBg: 'bg-purple-100',
    tagText: 'text-purple-800',
    buttonText: 'Làm bài',
  },
};

const PostCard: React.FC<PostCardProps> = ({ post, onAction }) => {
  const styles = categoryStyles[post.category];
  
  const handleAction = () => {
    onAction(post);
  };

  return (
    <div className={`bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden border-l-4 ${styles.borderColor}`}>
      <div className="p-6">
        <div className="flex justify-between items-start">
          <span className={`inline-block px-3 py-1 text-xs font-semibold rounded-full ${styles.tagBg} ${styles.tagText}`}>
            {post.subject}
          </span>
          <span className="text-xs text-gray-500">{post.date}</span>
        </div>
        <h3 
          className="mt-4 text-lg font-bold text-gray-800 hover:text-[#1e40af] transition-colors cursor-pointer"
          onClick={handleAction}
        >
          {post.title}
        </h3>
        <p className="mt-2 text-sm text-gray-600 line-clamp-2">{post.description}</p>
        <p className="mt-4 text-xs text-gray-500">Đăng bởi: <span className="font-medium text-gray-700">{post.author}</span></p>
      </div>
      <div className="bg-gray-50 px-6 py-3 flex justify-between items-center">
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center">
            <EyeIcon className="mr-1.5" />
            <span>{post.views.toLocaleString('vi-VN')}</span>
          </div>
          <div className="flex items-center">
            <DownloadIcon className="mr-1.5" />
            <span>{post.downloads.toLocaleString('vi-VN')}</span>
          </div>
          <div className="flex items-center">
            <ChatAltIcon className="mr-1.5" />
            <span>{post.comments.toLocaleString('vi-VN')}</span>
          </div>
        </div>
        <button 
          onClick={handleAction}
          disabled={post.category !== Category.MOCK_TEST && !post.fileUrl}
          className="bg-[#1e40af] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-900 transition-colors duration-300 disabled:bg-gray-400 disabled:cursor-not-allowed">
          {styles.buttonText}
        </button>
      </div>
    </div>
  );
};

export default PostCard;