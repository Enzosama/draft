import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white mt-12">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-gray-600">
        <p>&copy; {new Date().getFullYear()} NeuraViet. All rights reserved.</p>
        <p className="text-sm mt-1">Phát triển bởi Cộng đồng Giáo dục Việt Nam</p>
      </div>
    </footer>
  );
};

export default Footer;