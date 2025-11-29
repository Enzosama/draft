import React, { useEffect, useState } from 'react';
import { CyberTopic } from '../data/types';

interface SidebarProps {
  selectedTopic: string | null;
  setSelectedTopic: (topicSlug: string | null) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ selectedTopic, setSelectedTopic }) => {
  const [topics, setTopics] = useState<CyberTopic[]>([]);

  useEffect(() => {
    const loadTopics = async () => {
      try {
        const res = await fetch('/api/cyber/topics');
        if (res.ok) {
          const data = await res.json();
          setTopics(data);
        }
      } catch (error) {
        console.error('Failed to load cyber topics:', error);
      }
    };
    loadTopics();
  }, []);

  return (
    <aside className="w-full lg:w-64 bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Môn học</h3>
      <ul>
        <li className="mb-2">
          <button
            onClick={() => setSelectedTopic(null)}
            className={`w-full text-left px-4 py-2 rounded-md text-gray-700 transition-colors duration-200 ${selectedTopic === null ? 'bg-[#1e40af] text-white' : 'hover:bg-sky-100'
              }`}
          >
            Tất cả
          </button>
        </li>
        {topics.map((topic) => (
          <li key={topic.slug} className="mb-2">
            <button
              onClick={() => setSelectedTopic(topic.slug)}
              className={`w-full text-left px-4 py-2 rounded-md text-gray-700 transition-colors duration-200 ${selectedTopic === topic.slug ? 'bg-[#1e40af] text-white' : 'hover:bg-sky-100'
                }`}
            >
              {topic.name}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
};

export default Sidebar;
