import React from 'react';
import { Post } from '../data/types';
import PostCard from './PostCard';

interface PostListProps {
  posts: Post[];
  onAction: (post: Post) => void;
}

const PostList: React.FC<PostListProps> = ({ posts, onAction }) => {
  if (posts.length === 0) {
    return (
      <div className="text-center py-16">
        <h3 className="text-xl font-semibold text-gray-700">Không tìm thấy kết quả</h3>
        <p className="text-gray-500 mt-2">Vui lòng thử lại với bộ lọc hoặc từ khóa khác.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} onAction={onAction} />
      ))}
    </div>
  );
};

export default PostList;