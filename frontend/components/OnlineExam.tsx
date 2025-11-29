import React, { useState, useEffect, useRef } from 'react';
import { Post } from '../data/types';

// Helper function to sanitize filename
function sanitizeFilename(name: string): string {
  return name.replace(/[^a-zA-Z0-9._-]/g, '_').substring(0, 100);
}

// --- TYPE DEFINITIONS ---
interface Question {
  id: number;
  text: string;
  options: string[];
}

interface Passage {
    title: string;
    content: string[];
    source: string;
}

interface StudentInfo {
    name: string;
    subject: string;
    date: string;
}

interface ExamData {
    totalQuestions: number;
    initialTimeSeconds: number;
    studentInfo: StudentInfo;
    passage: Passage;
    questions: Question[];
}

interface OnlineExamProps {
  examInfo: Post;
  onClose: () => void;
  onLoginRequired?: () => void;
}

// --- SVG ICONS ---
const ClockIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const FullscreenIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M3 9V3h6v2H5v4H3zm12-6h6v6h-2V5h-4V3zM5 19H3v-6h2v4h4v2H5zm10 0v2h6v-6h-2v4h-4z" />
    </svg>
);

const ExitFullscreenIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M5 5v4H3V3h6v2H5zm14 0v4h2V3h-6v2h4zM5 15H3v6h6v-2H5v-4zm14 0h2v6h-6v-2h4v-4z" />
    </svg>
);

const FlagIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 21v-13.25l9-3.75l9 3.75V15M12 4.01V4M12 21v-9" />
    </svg>
);

const ZoomOutIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
  </svg>
);

const ZoomInIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
  </svg>
);

const SwapIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
  </svg>
);

const ViewControls = ({ onZoomIn, onZoomOut, onSwap }: { onZoomIn: () => void; onZoomOut: () => void; onSwap: () => void; }) => (
    <div className="flex space-x-1">
        <button onClick={onZoomOut} className="p-1.5 rounded bg-blue-500 text-white hover:bg-blue-600 flex items-center justify-center">
            <ZoomOutIcon />
        </button>
        <button onClick={onZoomIn} className="p-1.5 rounded bg-blue-500 text-white hover:bg-blue-600 flex items-center justify-center">
             <ZoomInIcon />
        </button>
        <button onClick={onSwap} className="p-1.5 rounded bg-gray-200 text-gray-700 hover:bg-gray-300 flex items-center justify-center">
            <SwapIcon />
        </button>
    </div>
);


// --- MAIN COMPONENT ---
interface ExamResult {
  exam_result_id: number;
  exam_id: number;
  exam_title: string;
  score: number;
  total_points: number;
  percentage: number;
  time_spent_seconds: number;
  submitted_at: string;
  answers: Array<{
    question_id: number;
    answer_text?: string;
    option_id?: number;
    is_correct: boolean;
    points_earned: number;
    total_points: number;
  }>;
}

const OnlineExam: React.FC<OnlineExamProps> = ({ examInfo, onClose, onLoginRequired }) => {
  const [examData, setExamData] = useState<ExamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [timeLeft, setTimeLeft] = useState(0);
  const [initialTime, setInitialTime] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [panelWidth, setPanelWidth] = useState(50); // Initial width as a percentage
  const mainContentRef = useRef<HTMLDivElement>(null);
  const [currentQuestion, setCurrentQuestion] = useState(1);
  const [examResult, setExamResult] = useState<ExamResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentExamId, setCurrentExamId] = useState<number | null>(null);
  const [questionOptionMap, setQuestionOptionMap] = useState<Record<number, any[]>>({});
  const [fontSize, setFontSize] = useState(14); // Base font size in pixels
  const [isSwapped, setIsSwapped] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const questionsContainerRef = useRef<HTMLDivElement>(null);
  const questionRefs = useRef<Record<number, HTMLDivElement | null>>({});
  
  useEffect(() => {
    const fetchExamData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('OnlineExam - Fetching exam for:', examInfo);
        
        // For MOCK_TEST posts, we need to find the exam by title and subject
        let examApiData = null;
        
        // Strategy 1: Try using post.id as exam.id (in case they're linked)
        console.log('OnlineExam - Strategy 1: Trying post.id as exam.id:', examInfo.id);
        try {
          const directResponse = await fetch(`/api/exams/${examInfo.id}`);
          if (directResponse.ok) {
            examApiData = await directResponse.json();
            console.log('OnlineExam - Found exam by ID:', examApiData);
          } else {
            console.log('OnlineExam - Direct fetch failed:', directResponse.status);
          }
        } catch (e) {
          console.log('OnlineExam - Direct fetch error:', e);
        }
        
        // Strategy 2: Try to find exam by searching title and subject
        if (!examApiData) {
          console.log('OnlineExam - Strategy 2: Searching by title and subject');
          try {
            const searchResponse = await fetch(
              `/api/exams/?page=1&page_size=50&search=${encodeURIComponent(examInfo.title)}&subject=${encodeURIComponent(examInfo.subject)}`
            );
            
            if (searchResponse.ok) {
              const searchData = await searchResponse.json();
              const exams = searchData.data || [];
              console.log('OnlineExam - Search results:', exams.length, 'exams found');
              
              // Find exact match by title (case-insensitive)
              const matchedExam = exams.find((exam: any) => 
                exam.title?.toLowerCase() === examInfo.title?.toLowerCase() && 
                exam.subject === examInfo.subject
              );
              
              if (matchedExam) {
                console.log('OnlineExam - Found matching exam:', matchedExam.id);
                // Fetch full exam data with questions
                const examResponse = await fetch(`/api/exams/${matchedExam.id}`);
                if (examResponse.ok) {
                  examApiData = await examResponse.json();
                  console.log('OnlineExam - Loaded exam with questions:', examApiData.questions?.length || 0);
                }
              } else {
                console.log('OnlineExam - No exact match found, trying first result');
                // If no exact match, try first result
                if (exams.length > 0) {
                  const examResponse = await fetch(`/api/exams/${exams[0].id}`);
                  if (examResponse.ok) {
                    examApiData = await examResponse.json();
                    console.log('OnlineExam - Using first search result');
                  }
                }
              }
            } else {
              console.warn('OnlineExam - Search failed:', searchResponse.status);
            }
          } catch (e) {
            console.error('OnlineExam - Search error:', e);
          }
        }
        
        if (!examApiData) {
          console.error('OnlineExam - Could not find exam');
          throw new Error('Không tìm thấy đề thi tương ứng. Vui lòng kiểm tra lại hoặc liên hệ quản trị viên.');
        }
        
        // Transform API data to ExamData format
        const questions: Question[] = [];
        const optionMap: Record<number, any[]> = {};
        
        (examApiData.questions || []).forEach((q: any, index: number) => {
          // Handle options - could be array of objects or array of strings
          let options: string[] = [];
          let optionObjects: any[] = [];
          
          if (q.options && Array.isArray(q.options)) {
            options = q.options.map((opt: any) => {
              if (typeof opt === 'string') {
                optionObjects.push({ option_id: null, option_text: opt });
                return opt;
              }
              const optObj = {
                option_id: opt.option_id || null,
                option_text: opt.option_text || opt.text || String(opt)
              };
              optionObjects.push(optObj);
              return optObj.option_text;
            });
          }
          
          const questionId = q.question_id || index + 1;
          optionMap[questionId] = optionObjects;
          
          questions.push({
            id: questionId,
            text: q.question_text || '',
            options: options
          });
        });
        
        setQuestionOptionMap(optionMap);
        
        // If exam has file_url, try to load it as passage
        let passageSource = examApiData.file_url || examInfo.fileUrl || '';
        
        // Helper to extract Google Drive ID
        const extractDriveId = (url: string): string | null => {
          try {
            const u = new URL(url);
            if (!u.hostname.includes('drive.google.com') && !u.hostname.includes('docs.google.com')) return null;
            const idParam = u.searchParams.get('id');
            if (idParam) return idParam;
            const pathMatch = url.match(/\/file\/d\/([a-zA-Z0-9_-]+)/);
            if (pathMatch) return pathMatch[1];
            return null;
          } catch {
            return null;
          }
        };
        
        // For Google Drive URLs, convert to preview URL for direct embedding
        if (passageSource) {
          const driveId = extractDriveId(passageSource);
          if (driveId) {
            // Use Google Drive preview URL - works well in iframe
            passageSource = `https://drive.google.com/file/d/${driveId}/preview`;
            console.log('OnlineExam - Using Google Drive preview URL:', passageSource);
          }
        }
        
        let passage: Passage = {
          title: examApiData.title || examInfo.title,
          content: [],
          source: passageSource
        };
        
        // Create ExamData
        const transformedData: ExamData = {
          totalQuestions: questions.length || 0,
          initialTimeSeconds: 3600, // Default 1 hour, can be extended later
          studentInfo: {
            name: examApiData.fullname || examInfo.author,
            subject: examApiData.subject || examInfo.subject,
            date: examApiData.created_at || examInfo.date
          },
          passage: passage,
          questions: questions
        };
        
        if (transformedData.totalQuestions === 0) {
          throw new Error('Đề thi này chưa có câu hỏi nào. Vui lòng liên hệ quản trị viên.');
        }
        
        setExamData(transformedData);
        setTimeLeft(transformedData.initialTimeSeconds);
        setInitialTime(transformedData.initialTimeSeconds);
        // Extract exam ID from API response
        if (examApiData.id) {
          setCurrentExamId(examApiData.id);
        }
        setLoading(false);
      } catch (err: any) {
        console.error("Failed to fetch exam:", err);
        setError(err.message || "Không thể tải đề thi. Vui lòng thử lại sau.");
        setLoading(false);
      }
    };
    
    if (examInfo?.id) {
      fetchExamData();
    } else {
      setError("Thông tin đề thi không hợp lệ");
      setLoading(false);
    }
  }, [examInfo]);

  useEffect(() => {
    if (timeLeft > 0) {
        const timer = setInterval(() => {
            setTimeLeft(prevTime => (prevTime > 0 ? prevTime - 1 : 0));
        }, 1000);
        return () => clearInterval(timer);
    }
  }, [timeLeft]);
  
  useEffect(() => {
    const handleFullscreenChange = () => {
        setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  const handleSelectAnswer = (questionId: number, optionIndex: number) => {
    setAnswers(prev => {
      const newAnswers = {...prev, [questionId]: optionIndex};
      // Auto-save to localStorage
      if (currentExamId) {
        const saveKey = `exam_${currentExamId}_answers`;
        localStorage.setItem(saveKey, JSON.stringify(newAnswers));
      }
      return newAnswers;
    });
  }
  
  // Helper to get question by number (1-based index)
  const getQuestionByNumber = (questionNumber: number) => {
    if (!examData) return null;
    const index = questionNumber - 1;
    if (index >= 0 && index < examData.questions.length) {
      return examData.questions[index];
    }
    return null;
  }
  
  // Load saved answers from localStorage
  useEffect(() => {
    if (currentExamId && examData) {
      const saveKey = `exam_${currentExamId}_answers`;
      const saved = localStorage.getItem(saveKey);
      if (saved) {
        try {
          const savedAnswers = JSON.parse(saved);
          setAnswers(savedAnswers);
          console.log('OnlineExam - Loaded saved answers:', savedAnswers);
        } catch (e) {
          console.error('OnlineExam - Error loading saved answers:', e);
        }
      }
    }
  }, [currentExamId, examData]);
  
  // Scroll to current question when it changes
  useEffect(() => {
    if (currentQuestion && questionRefs.current[currentQuestion] && questionsContainerRef.current) {
      const questionElement = questionRefs.current[currentQuestion];
      if (questionElement) {
        questionElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [currentQuestion]);
  
  const handlePrevQuestion = () => {
    if (currentQuestion > 1) {
      setCurrentQuestion(prev => prev - 1);
    }
  };
  
  const handleNextQuestion = () => {
    if (examData && currentQuestion < examData.totalQuestions) {
      setCurrentQuestion(prev => prev + 1);
    }
  };
  
  const handleSave = () => {
    if (!currentExamId) {
      alert('Không thể lưu. Vui lòng thử lại.');
      return;
    }
    
    const saveKey = `exam_${currentExamId}_answers`;
    localStorage.setItem(saveKey, JSON.stringify(answers));
    
    // Show temporary success message
    const saveButton = document.querySelector('[data-save-button]') as HTMLElement;
    if (saveButton) {
      const originalText = saveButton.textContent;
      saveButton.textContent = 'Đã lưu!';
      saveButton.classList.add('bg-green-500');
      saveButton.classList.remove('bg-blue-500');
      setTimeout(() => {
        saveButton.textContent = originalText;
        saveButton.classList.remove('bg-green-500');
        saveButton.classList.add('bg-blue-500');
      }, 2000);
    }
  };
  
  const handleSubmitExam = async () => {
    if (!examData || !currentExamId) {
      alert('Không thể nộp bài. Vui lòng thử lại.');
      return;
    }
    
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (!token) {
      const shouldLogin = window.confirm('Bạn cần đăng nhập để nộp bài. Bạn có muốn đăng nhập ngay không?');
      if (shouldLogin && onLoginRequired) {
        onLoginRequired();
      }
      return;
    }
    
    if (Object.keys(answers).length === 0) {
      const confirmSubmit = window.confirm('Bạn chưa trả lời câu hỏi nào. Bạn có chắc muốn nộp bài không?');
      if (!confirmSubmit) return;
    }
    
    setIsSubmitting(true);
    try {
      const timeSpent = initialTime - timeLeft;
      const submission = {
        exam_id: currentExamId,
        answers: examData.questions.map((q) => {
          const answerIndex = answers[q.id];
          let optionId = null;
          
          // Get option_id from question options if available
          if (answerIndex !== undefined) {
            if (questionOptionMap[q.id] && questionOptionMap[q.id][answerIndex]) {
              optionId = questionOptionMap[q.id][answerIndex].option_id;
            }
            // If option_id is still null but we have an answer, try to fetch from API
            // For now, we'll submit with the index (will need backend to handle this)
            // Note: Backend expects option_id to match question_options.option_id
          }
          
          return {
            question_id: q.id,
            option_id: optionId, // May be null if options don't have option_id
            answer_text: null
          };
        }),
        time_spent_seconds: timeSpent
      };
      
      const response = await fetch(`/api/exams/${currentExamId}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(submission)
      });
      
      if (response.ok) {
        const result = await response.json();
        // Clear saved answers from localStorage after successful submission
        if (currentExamId) {
          const saveKey = `exam_${currentExamId}_answers`;
          localStorage.removeItem(saveKey);
        }
        setExamResult(result);
      } else {
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('token'); // Clear invalid token
          const shouldLogin = window.confirm('Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Bạn có muốn đăng nhập lại không?');
          if (shouldLogin && onLoginRequired) {
            onLoginRequired();
          }
          return;
        }
        
        // Handle other errors
        let errorMessage = 'Không thể nộp bài. Vui lòng thử lại.';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          // If JSON parsing fails, use default message
        }
        throw new Error(errorMessage);
      }
    } catch (err: any) {
      console.error('Error submitting exam:', err);
      // Don't show alert if user chose to login (already handled above)
      if (!err.message?.includes('đăng nhập')) {
        alert(err.message || 'Không thể nộp bài. Vui lòng thử lại.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Count answered questions correctly
  const answeredCount = examData ? examData.questions.filter(q => answers[q.id] !== undefined).length : 0;

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const parent = mainContentRef.current;
    if (!parent) return;

    const startWidth = parent.children[0].clientWidth;
    const mainWidth = parent.clientWidth;

    const handleMouseMove = (moveEvent: MouseEvent) => {
        const dx = isSwapped ? startX - moveEvent.clientX : moveEvent.clientX - startX;
        const newWidthPercent = ((startWidth + dx) / mainWidth) * 100;
        
        if (newWidthPercent > 25 && newWidthPercent < 75) {
            setPanelWidth(newWidthPercent);
        }
    };

    const handleMouseUp = () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };
  
  const handleZoomIn = () => setFontSize(prev => Math.min(22, prev + 1));
  const handleZoomOut = () => setFontSize(prev => Math.max(10, prev - 1));
  const handleSwapPanels = () => setIsSwapped(prev => !prev);

  const handleToggleFullscreen = () => {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Đang tải đề thi...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center p-6 max-w-md">
          <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Không thể tải đề thi</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={onClose}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Quay lại danh sách
          </button>
        </div>
      </div>
    );
  }
  
  if (!examData) {
    return <div className="flex items-center justify-center min-h-screen">Could not load exam data.</div>;
  }

  // Show result screen if exam is submitted
  if (examResult) {
    const correctCount = examResult.answers.filter(a => a.is_correct).length;
    const totalCount = examResult.answers.length;
    const timeSpentMinutes = Math.floor(examResult.time_spent_seconds / 60);
    const timeSpentSeconds = examResult.time_spent_seconds % 60;
    
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="text-center mb-6">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Kết quả thi</h2>
              <p className="text-gray-600">{examResult.exam_title}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <p className="text-sm text-gray-600 mb-1">Điểm số</p>
                <p className="text-3xl font-bold text-blue-600">{examResult.score.toFixed(1)} / {examResult.total_points.toFixed(1)}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <p className="text-sm text-gray-600 mb-1">Tỷ lệ đúng</p>
                <p className="text-3xl font-bold text-green-600">{examResult.percentage.toFixed(1)}%</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4 text-center">
                <p className="text-sm text-gray-600 mb-1">Thời gian làm bài</p>
                <p className="text-3xl font-bold text-purple-600">{timeSpentMinutes}:{timeSpentSeconds.toString().padStart(2, '0')}</p>
              </div>
            </div>
            
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Chi tiết câu trả lời</h3>
              <div className="space-y-3">
                {examResult.answers.map((answer, index) => {
                  const question = examData.questions.find(q => q.id === answer.question_id);
                  return (
                    <div 
                      key={answer.question_id} 
                      className={`border rounded-lg p-4 ${answer.is_correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <p className="font-semibold text-gray-900">
                          Câu {index + 1}: {question?.text || `Câu hỏi ${answer.question_id}`}
                        </p>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          answer.is_correct ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'
                        }`}>
                          {answer.is_correct ? 'Đúng' : 'Sai'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">
                        Điểm: {answer.points_earned.toFixed(1)} / {answer.total_points.toFixed(1)}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
            
            <div className="flex justify-center space-x-4">
              <button
                onClick={onClose}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                Quay lại danh sách
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white min-h-screen">
      <div className="flex flex-col h-screen">

        {/* --- Student Info & Controls Header --- */}
        <div className="bg-[#002e6e] text-white flex justify-between items-center px-4 py-2">
            <div>
                <p className="font-bold">{examData.studentInfo.name}</p>
                <p className="text-sm">Môn thi: {examInfo.subject.toUpperCase()} | Ngày thi: {examData.studentInfo.date}</p>
            </div>
            <div className="flex items-center space-x-4">
                <div className="flex items-center">
                    <ClockIcon />
                    <span className="font-bold text-lg">{formatTime(timeLeft)}</span>
                </div>
                <div className="flex items-center">
                    <span className="h-3 w-3 bg-green-500 rounded-full mr-2"></span>
                    <span>Đang kết nối</span>
                </div>
                <button 
                  onClick={handleSubmitExam} 
                  disabled={isSubmitting}
                  className="bg-white text-blue-800 font-semibold py-1 px-4 rounded border border-gray-300 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Đang nộp...' : 'NỘP BÀI'}
                </button>
                <button onClick={handleToggleFullscreen} className="text-white">
                    {isFullscreen ? <ExitFullscreenIcon /> : <FullscreenIcon />}
                </button>
            </div>
        </div>
        
        {/* --- Question Navigation Bar --- */}
        <div className="px-4 py-2 border-b border-gray-200 grid grid-cols-3 items-center">
            <div></div> {/* Left placeholder for alignment */}
            <div className="flex justify-center space-x-2">
                <button 
                  onClick={handlePrevQuestion}
                  disabled={currentQuestion === 1}
                  className="bg-white border border-gray-300 text-gray-700 px-4 py-1.5 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Quay lại
                </button>
                <button 
                  onClick={handleNextQuestion}
                  disabled={currentQuestion >= examData.totalQuestions}
                  className="bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Tiếp theo
                </button>
            </div>
            <div className="flex items-center space-x-3 justify-end">
                <p className="text-sm text-black">Số câu đã trả lời: <span className="font-bold">{answeredCount} / {examData.totalQuestions}</span></p>
                <button 
                  onClick={handleSave}
                  data-save-button
                  className="bg-blue-500 text-white px-4 py-1 rounded text-sm hover:bg-blue-600 transition-colors"
                >
                  Lưu
                </button>
                <ViewControls onZoomIn={handleZoomIn} onZoomOut={handleZoomOut} onSwap={handleSwapPanels} />
            </div>
        </div>

        {/* --- Main Content --- */}
        <main ref={mainContentRef} className={`flex-1 flex overflow-hidden ${isSwapped ? 'flex-row-reverse' : 'flex-row'}`}>
          
          {/* Left Panel: Passage */}
          <div className="overflow-y-auto p-4" style={{ width: `${panelWidth}%`, fontSize: `${fontSize}px` }}>
            <p className="font-semibold mb-4">{examData.passage.title}</p>
            {examData.passage.source ? (() => {
              // Helper to extract Google Drive ID
              const extractDriveId = (url: string): string | null => {
                try {
                  const u = new URL(url);
                  if (!u.hostname.includes('drive.google.com') && !u.hostname.includes('docs.google.com')) return null;
                  const idParam = u.searchParams.get('id');
                  if (idParam) return idParam;
                  const pathMatch = url.match(/\/file\/d\/([a-zA-Z0-9_-]+)/);
                  if (pathMatch) return pathMatch[1];
                  return null;
                } catch {
                  return null;
                }
              };
              
              // Check if it's a Google Drive URL
              const driveId = extractDriveId(examData.passage.source);
              
              let iframeSrc = '';
              
              if (driveId) {
                // Use Google Drive preview URL directly
                iframeSrc = `https://drive.google.com/file/d/${driveId}/preview`;
              } else if (examData.passage.source.startsWith('/')) {
                // Relative URL (cached file)
                iframeSrc = examData.passage.source;
              } else if (examData.passage.source.startsWith('http://') || examData.passage.source.startsWith('https://')) {
                // Try to cache and use cached version, or use proxy
                iframeSrc = `/api/files/proxy?url=${encodeURIComponent(examData.passage.source)}`;
              } else {
                iframeSrc = examData.passage.source;
              }
              
              return (
                <div className="w-full h-full border-2 border-gray-200 rounded-md overflow-hidden bg-gray-100">
                  <iframe
                    src={iframeSrc}
                    title={examData.passage.title}
                    width="100%"
                    height="100%"
                    style={{ border: 'none', minHeight: '600px' }}
                    allow="fullscreen"
                    onError={(e) => {
                      console.error('OnlineExam - Iframe error:', e);
                    }}
                  />
                </div>
              );
            })() : (
            <div className="space-y-4 text-gray-800 leading-relaxed">
                {examData.passage.content && examData.passage.content.length > 0 ? (
                  examData.passage.content.map((paragraph, index) => (
                <p key={index} dangerouslySetInnerHTML={{ __html: paragraph }} />
                  ))
                ) : (
                  <p className="text-gray-500 italic">Đề thi này không có tài liệu đọc kèm.</p>
                )}
            </div>
            )}
          </div>

          {/* Draggable Divider */}
          <div 
            className="w-1.5 cursor-col-resize bg-gray-200 hover:bg-blue-300 transition-colors"
            onMouseDown={handleMouseDown}
            role="separator"
            aria-orientation="vertical"
          ></div>

          {/* Right Panel: Questions */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div ref={questionsContainerRef} className="flex-1 overflow-y-auto p-4 bg-gray-50" style={{ fontSize: `${fontSize}px` }}>
                <div className="space-y-6">
                    {examData.questions.map((q, questionIndex) => {
                      // Use 1-based index for display and navigation
                      const questionNumber = questionIndex + 1;
                      const isCurrentQuestion = currentQuestion === questionNumber;
                      return (
                        <div 
                          key={q.id} 
                          ref={(el) => { questionRefs.current[questionNumber] = el; }}
                          className={`bg-white p-4 border-2 rounded-md transition-all ${
                            isCurrentQuestion 
                              ? 'border-blue-500 shadow-lg ring-2 ring-blue-200' 
                              : 'border-gray-200'
                          }`}
                        >
                            <div className="flex justify-between items-start">
                                <p className="mb-3 text-gray-800">
                                    <strong className="font-semibold">Câu {questionNumber}.</strong> <span dangerouslySetInnerHTML={{ __html: q.text }} />
                                </p>
                                <button className="opacity-50 hover:opacity-100 transition-opacity"><FlagIcon /></button>
                            </div>
                            <div className="space-y-2">
                                {q.options.map((option, index) => (
                                    <label key={index} className="flex items-center cursor-pointer p-2 rounded hover:bg-blue-50 transition-colors">
                                        <input 
                                            type="radio" 
                                            name={`question-${q.id}`} 
                                            className="form-radio h-4 w-4 text-blue-600"
                                            checked={answers[q.id] === index}
                                            onChange={() => handleSelectAnswer(q.id, index)}
                                        />
                                        <span className="ml-3 text-gray-700">{String.fromCharCode(65 + index)}. {option}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                      );
                    })}
                     <div className="h-16"></div>
                </div>
            </div>
          </div>
        </main>

        {/* --- Footer: Question Navigator --- */}
        <footer className="border-t border-gray-200 p-3 bg-white">
          <div className="flex flex-wrap gap-2 justify-center">
            {Array.from({ length: examData.totalQuestions }, (_, i) => {
              const questionNumber = i + 1;
              // Get the actual question at this index
              const question = examData.questions[i];
              // Check if this question is answered (using question.id as key)
              const isAnswered = question ? answers[question.id] !== undefined : false;

              let buttonClass = '';
              if (isAnswered) {
                buttonClass = 'bg-green-500 text-white border-green-600';
              } else {
                buttonClass = 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-100';
              }

              const isCurrent = currentQuestion === questionNumber;
              return (
                <button
                  key={questionNumber}
                  onClick={() => setCurrentQuestion(questionNumber)}
                  className={`h-8 w-8 rounded-full flex items-center justify-center font-semibold text-sm transition-colors ${
                    isCurrent ? 'ring-2 ring-blue-500 ring-offset-2' : ''
                  } ${buttonClass}`}
                  title={`Câu ${questionNumber}`}
                >
                  {questionNumber}
                </button>
              );
            })}
          </div>
        </footer>
      </div>
    </div>
  );
}

export default OnlineExam;