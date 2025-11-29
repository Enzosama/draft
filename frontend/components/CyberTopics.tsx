import React, { useEffect, useState } from 'react';
import { CyberTopic, CyberResource } from '../data/types';
import { ChevronDown, ChevronUp, ExternalLink, BookOpen, ShieldCheck, ShieldAlert, FileText } from 'lucide-react';

interface CyberTopicsProps {
    selectedTopicSlug?: string | null;
}

const CyberTopics: React.FC<CyberTopicsProps> = ({ selectedTopicSlug = null }) => {
    const [topics, setTopics] = useState<CyberTopic[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

    useEffect(() => {
        const fetchTopics = async () => {
            try {
                const response = await fetch('/api/cyber/topics');
                if (response.ok) {
                    const data = await response.json();
                    setTopics(data);
                    // Expand the first topic by default if available
                    if (data.length > 0) {
                        setExpandedTopic(data[0].slug);
                    }
                } else {
                    console.error('Failed to fetch cyber topics');
                }
            } catch (error) {
                console.error('Error fetching cyber topics:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchTopics();
    }, []);

    const toggleTopic = (slug: string) => {
        setExpandedTopic(expandedTopic === slug ? null : slug);
    };

    const getTopicIcon = (type: string) => {
        switch (type) {
            case 'attack':
                return <ShieldAlert className="w-6 h-6 text-red-500" />;
            case 'defense':
                return <ShieldCheck className="w-6 h-6 text-blue-500" />;
            default:
                return <BookOpen className="w-6 h-6 text-purple-500" />;
        }
    };

    const getDifficultyColor = (diff?: string) => {
        switch (diff) {
            case 'beginner': return 'bg-green-100 text-green-800';
            case 'intermediate': return 'bg-yellow-100 text-yellow-800';
            case 'advanced': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    const filteredTopics = selectedTopicSlug
        ? topics.filter(t => t.slug === selectedTopicSlug)
        : topics;

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-100">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Chương trình An Ninh Mạng</h2>
                <p className="text-gray-600">
                    Khám phá các chủ đề từ cơ bản đến nâng cao về bảo mật web, mạng, và phân tích mã độc.
                </p>
            </div>

            <div className="grid gap-4">
                {filteredTopics.map((topic) => (
                    <div key={topic.slug} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                        <button
                            onClick={() => toggleTopic(topic.slug)}
                            className="w-full px-6 py-4 flex items-center justify-between bg-white hover:bg-gray-50 transition-colors"
                        >
                            <div className="flex items-center space-x-4">
                                <div className="p-2 bg-gray-50 rounded-lg">
                                    {getTopicIcon(topic.topic_type)}
                                </div>
                                <div className="text-left">
                                    <h3 className="text-lg font-semibold text-gray-900">{topic.name}</h3>
                                    <p className="text-sm text-gray-500">{topic.description}</p>
                                </div>
                            </div>
                            {expandedTopic === topic.slug ? (
                                <ChevronUp className="w-5 h-5 text-gray-400" />
                            ) : (
                                <ChevronDown className="w-5 h-5 text-gray-400" />
                            )}
                        </button>

                        {expandedTopic === topic.slug && (
                            <div className="px-6 pb-6 pt-2 border-t border-gray-100 bg-gray-50/50">
                                <div className="space-y-4">
                                    {topic.resources && topic.resources.length > 0 ? (
                                        topic.resources.map((resource, idx) => (
                                            <div key={idx} className="bg-white p-4 rounded-md border border-gray-200 hover:shadow-md transition-shadow">
                                                <div className="flex justify-between items-start">
                                                    <div className="flex-1">
                                                        <h4 className="font-medium text-gray-900 flex items-center flex-wrap gap-2">
                                                            {resource.title}
                                                            {resource.difficulty && (
                                                                <span className={`px-2 py-0.5 text-xs rounded-full ${getDifficultyColor(resource.difficulty)}`}>
                                                                    {resource.difficulty}
                                                                </span>
                                                            )}
                                                            <span className="px-2 py-0.5 text-xs rounded-full bg-blue-50 text-blue-700 border border-blue-100">
                                                                {resource.resource_type}
                                                            </span>
                                                        </h4>
                                                        <p className="text-sm text-gray-600 mt-1">{resource.summary}</p>
                                                        {resource.tags && (
                                                            <div className="flex flex-wrap gap-2 mt-2">
                                                                {resource.tags.split(',').map(tag => (
                                                                    <span key={tag} className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                                                        #{tag.trim()}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="flex gap-2 ml-4">
                                                        {resource.file_url && (
                                                            <a
                                                                href={resource.file_url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="p-2 text-green-600 hover:bg-green-50 rounded-full transition-colors"
                                                                title="Xem PDF"
                                                            >
                                                                <FileText className="w-5 h-5" />
                                                            </a>
                                                        )}
                                                        {resource.source && (
                                                            <a
                                                                href={resource.source}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                                                                title="Mở liên kết"
                                                            >
                                                                <ExternalLink className="w-5 h-5" />
                                                            </a>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <p className="text-gray-500 italic text-center py-4">Chưa có tài liệu nào cho chủ đề này.</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CyberTopics;
