import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import json
import logging

# Cấu hình logging để ghi vào file thay vì console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('question_analyzer.log'),
    ]
)

logger = logging.getLogger(__name__)

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"

class DifficultyLevel(str, Enum):
    """Mức độ khó của câu hỏi"""
    EASY = "easy"           # p ≥ 0.85
    MODERATE = "moderate"   # 0.51 ≤ p ≤ 0.84
    HARD = "hard"           # p ≤ 0.50

class DiscriminationLevel(str, Enum):
    """Mức độ phân biệt của câu hỏi"""
    GOOD = "good"   # D ≥ 0.30
    FAIR = "fair"   # 0.10 ≤ D < 0.30
    POOR = "poor"   # D < 0.10

@dataclass
class QuestionMetrics:
    """Các chỉ số thống kê của câu hỏi"""
    question_id: str
    question_type: str
    
    # Dữ liệu thô
    total_attempts: int
    correct_attempts: int
    
    # Chỉ số tính toán
    p_value: float
    difficulty_score: float
    discrimination_index: float
    
    # Phân loại
    difficulty_level: str
    discrimination_level: str
    
    # Đánh giá chất lượng
    quality_score: float
    is_qualified: bool
    
    # Metadata
    last_analyzed: datetime
    recommendations: List[str]
    
    def to_dict(self):
        """Convert to dictionary"""
        data = asdict(self)
        data['last_analyzed'] = self.last_analyzed.isoformat()
        return data


# ==================== QUESTION ANALYZER ====================

class QuestionAnalyzer:
    """Lớp phân tích câu hỏi"""
    
    def __init__(self, top_percent: float = 0.27, bottom_percent: float = 0.27):
        """
        Args:
            top_percent: Tỷ lệ học sinh nhóm điểm cao
            bottom_percent: Tỷ lệ học sinh nhóm điểm thấp
        """
        self.TOP_PERCENT = top_percent
        self.BOTTOM_PERCENT = bottom_percent
        self.MIN_ATTEMPTS = 10
        self.MIN_DISCRIMINATION = 0.10
        
        logger.info(f"QuestionAnalyzer initialized with top={top_percent}, bottom={bottom_percent}")
    
    
    def calculate_p_value(self, total_attempts: int, correct_attempts: int) -> float:
        """
        Tính p-value (tỷ lệ trả lời đúng)
        p = Số học sinh trả lời đúng / Tổng số học sinh làm câu hỏi
        """
        if total_attempts == 0:
            return 0.0
        return correct_attempts / total_attempts
    
    
    def calculate_difficulty(self, question_type: str, p_value: float) -> float:
        """
        Tính độ khó dựa trên loại câu hỏi
        - Multiple Choice: độ khó = p
        - True/False: độ khó = 1 - p
        """
        if question_type == QuestionType.TRUE_FALSE.value:
            return 1 - p_value
        else:
            return p_value
    
    
    def classify_difficulty(self, p_value: float) -> str:
        """
        Phân loại mức độ khó
        - EASY: p ≥ 0.85
        - MODERATE: 0.51 ≤ p ≤ 0.84
        - HARD: p ≤ 0.50
        """
        if p_value >= 0.85:
            return DifficultyLevel.EASY.value
        elif p_value >= 0.51:
            return DifficultyLevel.MODERATE.value
        else:
            return DifficultyLevel.HARD.value
    
    
    def calculate_discrimination_index(
        self,
        question_id: str,
        student_answers: List[Dict],
        exam_results: List[Dict]
    ) -> float:
        """
        Tính chỉ số phân biệt D
        D = (Số HS nhóm cao đúng / Số HS nhóm cao) - (Số HS nhóm thấp đúng / Số HS nhóm thấp)
        """
        sorted_results = sorted(
            exam_results,
            key=lambda x: x['total_score'],
            reverse=True
        )
        
        n_students = len(sorted_results)
        if n_students < 10:
            return 0.0
        
        top_n = max(1, int(n_students * self.TOP_PERCENT))
        bottom_n = max(1, int(n_students * self.BOTTOM_PERCENT))
        
        top_students = {r['student_id'] for r in sorted_results[:top_n]}
        bottom_students = {r['student_id'] for r in sorted_results[-bottom_n:]}
        
        top_correct = sum(
            1 for ans in student_answers
            if ans['question_id'] == question_id
            and ans['student_id'] in top_students
            and ans['is_correct']
        )
        
        bottom_correct = sum(
            1 for ans in student_answers
            if ans['question_id'] == question_id
            and ans['student_id'] in bottom_students
            and ans['is_correct']
        )
        
        D = (top_correct / top_n) - (bottom_correct / bottom_n)
        
        return round(D, 4)
    
    
    def classify_discrimination(self, D: float) -> str:
        """
        Phân loại chỉ số phân biệt
        - GOOD: D ≥ 0.30
        - FAIR: 0.10 ≤ D < 0.30
        - POOR: D < 0.10
        """
        if D >= 0.30:
            return DiscriminationLevel.GOOD.value
        elif D >= 0.10:
            return DiscriminationLevel.FAIR.value
        else:
            return DiscriminationLevel.POOR.value
    
    
    def calculate_quality_score(
        self,
        p_value: float,
        discrimination_index: float,
        total_attempts: int
    ) -> float:
        """
        Tính điểm chất lượng câu hỏi (0-100)
        - Độ khó phù hợp: 40 điểm
        - Chỉ số phân biệt: 40 điểm
        - Số lượng dữ liệu: 20 điểm
        """
        score = 0.0
        
        # Điểm cho độ khó
        if 0.30 <= p_value <= 0.85:
            if 0.45 <= p_value <= 0.70:
                score += 40
            else:
                score += 30
        elif 0.20 <= p_value < 0.30 or 0.85 < p_value <= 0.90:
            score += 20
        else:
            score += 10
        
        # Điểm cho chỉ số phân biệt
        if discrimination_index >= 0.40:
            score += 40
        elif discrimination_index >= 0.30:
            score += 35
        elif discrimination_index >= 0.20:
            score += 25
        elif discrimination_index >= 0.10:
            score += 15
        else:
            score += 5
        
        # Điểm cho số lượng dữ liệu
        if total_attempts >= 100:
            score += 20
        elif total_attempts >= 50:
            score += 15
        elif total_attempts >= 30:
            score += 10
        elif total_attempts >= 10:
            score += 5
        
        return round(score, 2)
    
    
    def generate_recommendations(
        self,
        p_value: float,
        discrimination_index: float,
        total_attempts: int
    ) -> List[str]:
        """Tạo các gợi ý cải thiện câu hỏi"""
        recommendations = []
        
        if p_value >= 0.90:
            recommendations.append("Câu hỏi quá dễ - Tăng độ phức tạp")
        elif p_value <= 0.20:
            recommendations.append("Câu hỏi quá khó - Cân nhắc đơn giản hóa")
        
        if discrimination_index < 0.10:
            recommendations.append("Chỉ số phân biệt rất thấp - Nên sửa đổi hoặc loại bỏ")
        elif discrimination_index < 0.20:
            recommendations.append("Chỉ số phân biệt thấp - Cân nhắc sửa đổi")
        elif discrimination_index < 0.30:
            recommendations.append("Chỉ số phân biệt trung bình - Có thể cải thiện")
        else:
            recommendations.append("Chỉ số phân biệt tốt")
        
        if total_attempts < 10:
            recommendations.append(f"Số lượt làm quá ít ({total_attempts}) - Cần thêm dữ liệu")
        elif total_attempts < 30:
            recommendations.append(f"Số lượt làm ít ({total_attempts}) - Nên có thêm dữ liệu")
        
        if not recommendations:
            recommendations.append("Câu hỏi đạt chất lượng tốt")
        
        return recommendations
    
    
    def analyze_question(
        self,
        question_id: str,
        question_type: str,
        student_answers: List[Dict],
        exam_results: List[Dict]
    ) -> QuestionMetrics:
        """Phân tích đầy đủ một câu hỏi"""
        
        question_answers = [
            ans for ans in student_answers
            if ans['question_id'] == question_id
        ]
        
        total_attempts = len(question_answers)
        correct_attempts = sum(1 for ans in question_answers if ans['is_correct'])
        
        p_value = self.calculate_p_value(total_attempts, correct_attempts)
        difficulty_score = self.calculate_difficulty(question_type, p_value)
        difficulty_level = self.classify_difficulty(p_value)
        
        discrimination_index = self.calculate_discrimination_index(
            question_id, student_answers, exam_results
        )
        
        discrimination_level = self.classify_discrimination(discrimination_index)
        
        quality_score = self.calculate_quality_score(
            p_value, discrimination_index, total_attempts
        )
        
        is_qualified = (
            total_attempts >= self.MIN_ATTEMPTS and
            discrimination_index >= self.MIN_DISCRIMINATION
        )
        
        recommendations = self.generate_recommendations(
            p_value, discrimination_index, total_attempts
        )
        
        logger.info(f"Analyzed question {question_id}: p={p_value:.4f}, D={discrimination_index:.4f}, quality={quality_score}")
        
        return QuestionMetrics(
            question_id=question_id,
            question_type=question_type,
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            p_value=round(p_value, 4),
            difficulty_score=round(difficulty_score, 4),
            discrimination_index=discrimination_index,
            difficulty_level=difficulty_level,
            discrimination_level=discrimination_level,
            quality_score=quality_score,
            is_qualified=is_qualified,
            last_analyzed=datetime.now(),
            recommendations=recommendations
        )


# ==================== DATABASE MANAGER ====================

class QuestionDatabase:
    """Quản lý database cho câu hỏi"""
    
    def __init__(self, host: str, user: str, password: str, database: str):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'autocommit': False
        }
        self.connection = None
    
    
    def connect(self):
        """Kết nối database"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("Database connected successfully")
            return True
        except Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    
    def close(self):
        """Đóng kết nối"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
    
    
    def get_question(self, question_id: str) -> Optional[Dict]:
        """Lấy thông tin câu hỏi"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM questions WHERE id = %s",
                (question_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            logger.error(f"Error getting question {question_id}: {e}")
            return None
    
    
    def get_answers_by_question(self, question_id: str, exam_id: str = None) -> List[Dict]:
        """Lấy tất cả câu trả lời cho một câu hỏi"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if exam_id:
                query = """
                    SELECT * FROM student_answers
                    WHERE question_id = %s AND exam_id = %s
                """
                cursor.execute(query, (question_id, exam_id))
            else:
                query = "SELECT * FROM student_answers WHERE question_id = %s"
                cursor.execute(query, (question_id,))
            
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"Error getting answers for question {question_id}: {e}")
            return []
    
    
    def get_exam_results(self, exam_id: str) -> List[Dict]:
        """Lấy kết quả thi của tất cả học sinh"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM exam_results WHERE exam_id = %s",
                (exam_id,)
            )
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"Error getting exam results for {exam_id}: {e}")
            return []
    
    
    def update_question_metrics(self, metrics: QuestionMetrics) -> bool:
        """Cập nhật metrics cho câu hỏi"""
        try:
            cursor = self.connection.cursor()
            
            query = """
                UPDATE questions SET
                    total_attempts = %s,
                    correct_attempts = %s,
                    p_value = %s,
                    difficulty_score = %s,
                    difficulty_level = %s,
                    discrimination_index = %s,
                    discrimination_level = %s,
                    quality_score = %s,
                    is_qualified = %s,
                    recommendations = %s,
                    last_analyzed = %s
                WHERE id = %s
            """
            
            cursor.execute(query, (
                metrics.total_attempts,
                metrics.correct_attempts,
                metrics.p_value,
                metrics.difficulty_score,
                metrics.difficulty_level,
                metrics.discrimination_index,
                metrics.discrimination_level,
                metrics.quality_score,
                metrics.is_qualified,
                json.dumps(metrics.recommendations, ensure_ascii=False),
                metrics.last_analyzed,
                metrics.question_id
            ))
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Updated metrics for question {metrics.question_id}")
            return True
            
        except Error as e:
            logger.error(f"Error updating question {metrics.question_id}: {e}")
            self.connection.rollback()
            return False
    
    
    def get_exam_questions(self, exam_id: str) -> List[Dict]:
        """Lấy danh sách câu hỏi trong đề thi"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT q.* FROM questions q
                INNER JOIN exam_questions eq ON q.id = eq.question_id
                WHERE eq.exam_id = %s
                ORDER BY eq.question_order
            """, (exam_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"Error getting questions for exam {exam_id}: {e}")
            return []
    
    
    def get_all_answers_by_exam(self, exam_id: str) -> List[Dict]:
        """Lấy tất cả câu trả lời trong đề thi"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM student_answers WHERE exam_id = %s
            """, (exam_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"Error getting all answers for exam {exam_id}: {e}")
            return []
    
    
    def batch_update_questions(self, metrics_list: List[QuestionMetrics]) -> int:
        """Cập nhật hàng loạt câu hỏi"""
        success_count = 0
        
        for metrics in metrics_list:
            if self.update_question_metrics(metrics):
                success_count += 1
        
        logger.info(f"Batch update completed: {success_count}/{len(metrics_list)} questions updated")
        return success_count
    
    
    def get_question_with_stats(self, question_id: str) -> Optional[Dict]:
        """Lấy câu hỏi với đầy đủ thống kê"""
        return self.get_question(question_id)


# ==================== QUESTION SERVICE ====================

class QuestionAnalysisService:
    """Service phân tích câu hỏi"""
    
    def __init__(self, db: QuestionDatabase, analyzer: QuestionAnalyzer):
        self.db = db
        self.analyzer = analyzer
        logger.info("QuestionAnalysisService initialized")
    
    
    def analyze_single_question(
        self,
        question_id: str,
        exam_id: str,
        update_db: bool = True
    ) -> Optional[QuestionMetrics]:
        """
        Phân tích một câu hỏi
        
        Args:
            question_id: ID câu hỏi
            exam_id: ID đề thi
            update_db: Có cập nhật database không
            
        Returns:
            QuestionMetrics hoặc None nếu có lỗi
        """
        try:
            question = self.db.get_question(question_id)
            if not question:
                logger.error(f"Question {question_id} not found")
                return None
            
            student_answers = self.db.get_answers_by_question(question_id, exam_id)
            exam_results = self.db.get_exam_results(exam_id)
            
            if not student_answers:
                logger.warning(f"No answers found for question {question_id}")
                return None
            
            if not exam_results:
                logger.warning(f"No exam results found for exam {exam_id}")
                return None
            
            metrics = self.analyzer.analyze_question(
                question_id=question_id,
                question_type=question['question_type'],
                student_answers=student_answers,
                exam_results=exam_results
            )
            
            if update_db:
                self.db.update_question_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing question {question_id}: {e}")
            return None
    
    
    def analyze_exam_questions(
        self,
        exam_id: str,
        update_db: bool = True
    ) -> List[QuestionMetrics]:
        """
        Phân tích tất cả câu hỏi trong đề thi
        
        Args:
            exam_id: ID đề thi
            update_db: Có cập nhật database không
            
        Returns:
            Danh sách QuestionMetrics
        """
        try:
            logger.info(f"Starting analysis for exam {exam_id}")
            
            questions = self.db.get_exam_questions(exam_id)
            if not questions:
                logger.error(f"No questions found for exam {exam_id}")
                return []
            
            exam_results = self.db.get_exam_results(exam_id)
            if not exam_results:
                logger.error(f"No exam results found for exam {exam_id}")
                return []
            
            all_answers = self.db.get_all_answers_by_exam(exam_id)
            if not all_answers:
                logger.error(f"No answers found for exam {exam_id}")
                return []
            
            metrics_list = []
            
            for question in questions:
                try:
                    question_answers = [
                        ans for ans in all_answers
                        if ans['question_id'] == question['id']
                    ]
                    
                    if not question_answers:
                        logger.warning(f"No answers for question {question['id']}, skipping")
                        continue
                    
                    metrics = self.analyzer.analyze_question(
                        question_id=question['id'],
                        question_type=question['question_type'],
                        student_answers=question_answers,
                        exam_results=exam_results
                    )
                    
                    metrics_list.append(metrics)
                    
                except Exception as e:
                    logger.error(f"Error analyzing question {question['id']}: {e}")
                    continue
            
            if update_db and metrics_list:
                self.db.batch_update_questions(metrics_list)
            
            logger.info(f"Completed analysis for exam {exam_id}: {len(metrics_list)} questions analyzed")
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Error analyzing exam {exam_id}: {e}")
            return []
    
    
    def get_question_report(self, question_id: str) -> Optional[Dict]:
        """
        Lấy báo cáo chi tiết câu hỏi
        
        Args:
            question_id: ID câu hỏi
            
        Returns:
            Dict chứa thông tin báo cáo hoặc None
        """
        try:
            question = self.db.get_question_with_stats(question_id)
            if not question:
                logger.error(f"Question {question_id} not found")
                return None
            
            recommendations = []
            if question.get('recommendations'):
                try:
                    recommendations = json.loads(question['recommendations'])
                except:
                    recommendations = []
            
            return {
                'question_id': question_id,
                'content': question.get('content', ''),
                'type': question.get('question_type', ''),
                'metrics': {
                    'total_attempts': question.get('total_attempts', 0),
                    'correct_attempts': question.get('correct_attempts', 0),
                    'p_value': question.get('p_value', 0),
                    'difficulty_level': question.get('difficulty_level', ''),
                    'discrimination_index': question.get('discrimination_index', 0),
                    'discrimination_level': question.get('discrimination_level', ''),
                    'quality_score': question.get('quality_score', 0),
                    'is_qualified': question.get('is_qualified', False)
                },
                'recommendations': recommendations,
                'last_analyzed': question.get('last_analyzed')
            }
            
        except Exception as e:
            logger.error(f"Error getting report for question {question_id}: {e}")
            return None
    
    
    def get_statistics(self, metrics_list: List[QuestionMetrics]) -> Dict:
        """
        Tính toán thống kê tổng quan
        
        Args:
            metrics_list: Danh sách QuestionMetrics
            
        Returns:
            Dict chứa thống kê
        """
        if not metrics_list:
            return {}
        
        total = len(metrics_list)
        
        easy_count = sum(1 for m in metrics_list if m.difficulty_level == DifficultyLevel.EASY.value)
        moderate_count = sum(1 for m in metrics_list if m.difficulty_level == DifficultyLevel.MODERATE.value)
        hard_count = sum(1 for m in metrics_list if m.difficulty_level == DifficultyLevel.HARD.value)
        
        good_count = sum(1 for m in metrics_list if m.discrimination_level == DiscriminationLevel.GOOD.value)
        fair_count = sum(1 for m in metrics_list if m.discrimination_level == DiscriminationLevel.FAIR.value)
        poor_count = sum(1 for m in metrics_list if m.discrimination_level == DiscriminationLevel.POOR.value)
        
        qualified_count = sum(1 for m in metrics_list if m.is_qualified)
        
        avg_quality = sum(m.quality_score for m in metrics_list) / total
        avg_p_value = sum(m.p_value for m in metrics_list) / total
        avg_discrimination = sum(m.discrimination_index for m in metrics_list) / total
        
        stats = {
            'total_questions': total,
            'difficulty_distribution': {
                'easy': {'count': easy_count, 'percentage': round(easy_count/total*100, 2)},
                'moderate': {'count': moderate_count, 'percentage': round(moderate_count/total*100, 2)},
                'hard': {'count': hard_count, 'percentage': round(hard_count/total*100, 2)}
            },
            'discrimination_distribution': {
                'good': {'count': good_count, 'percentage': round(good_count/total*100, 2)},
                'fair': {'count': fair_count, 'percentage': round(fair_count/total*100, 2)},
                'poor': {'count': poor_count, 'percentage': round(poor_count/total*100, 2)}
            },
            'quality': {
                'qualified_count': qualified_count,
                'qualified_percentage': round(qualified_count/total*100, 2),
                'average_quality_score': round(avg_quality, 2),
                'average_p_value': round(avg_p_value, 4),
                'average_discrimination': round(avg_discrimination, 4)
            }
        }
        
        logger.info(f"Statistics calculated for {total} questions")
        
        return stats

#  PUBLIC API 
def analyze_question(
    question_id: str,
    exam_id: str,
    db_config: Dict,
    update_db: bool = True
) -> Optional[QuestionMetrics]:
    """
    API công khai để phân tích một câu hỏi
    
    Args:
        question_id: ID câu hỏi
        exam_id: ID đề thi
        db_config: Cấu hình database {'host', 'user', 'password', 'database'}
        update_db: Có cập nhật database không
        
    Returns:
        QuestionMetrics hoặc None
    """
    db = None
    try:
        db = QuestionDatabase(**db_config)
        db.connect()
        
        analyzer = QuestionAnalyzer()
        service = QuestionAnalysisService(db, analyzer)
        
        result = service.analyze_single_question(question_id, exam_id, update_db)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_question: {e}")
        return None
    finally:
        if db:
            db.close()


def analyze_exam(
    exam_id: str,
    db_config: Dict,
    update_db: bool = True
) -> List[QuestionMetrics]:
    """
    API công khai để phân tích toàn bộ đề thi
    
    Args:
        exam_id: ID đề thi
        db_config: Cấu hình database
        update_db: Có cập nhật database không
        
    Returns:
        List[QuestionMetrics]
    """
    db = None
    try:
        db = QuestionDatabase(**db_config)
        db.connect()
        
        analyzer = QuestionAnalyzer()
        service = QuestionAnalysisService(db, analyzer)
        
        results = service.analyze_exam_questions(exam_id, update_db)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in analyze_exam: {e}")
        return []
    finally:
        if db:
            db.close()


def get_question_statistics(
    exam_id: str,
    db_config: Dict
) -> Dict:
    """
    API công khai để lấy thống kê câu hỏi
    
    Args:
        exam_id: ID đề thi
        db_config: Cấu hình database
        
    Returns:
        Dict chứa thống kê
    """
    db = None
    try:
        db = QuestionDatabase(**db_config)
        db.connect()
        
        analyzer = QuestionAnalyzer()
        service = QuestionAnalysisService(db, analyzer)
        
        metrics_list = service.analyze_exam_questions(exam_id, update_db=False)
        stats = service.get_statistics(metrics_list)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error in get_question_statistics: {e}")
        return {}
    finally:
        if db:
            db.close()


# ==================== MAIN - CHỈ ĐỂ TEST ====================

if __name__ == "__main__":
    """
    Phần này chỉ dùng để test, không chạy trong production
    """
    
    # Cấu hình database
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'exam_user',
        'password': 'exam_password',
        'database': 'exam_system'
    }
    
    # Test phân tích đề thi
    logger.info("Starting exam analysis test")
    
    try:
        # Phân tích toàn bộ đề thi
        metrics_list = analyze_exam(
            exam_id="E001",
            db_config=DB_CONFIG,
            update_db=True
        )
        
        if metrics_list:
            logger.info(f"Analysis completed: {len(metrics_list)} questions processed")
        else:
            logger.warning("No questions analyzed")
        
        # Lấy thống kê
        stats = get_question_statistics(
            exam_id="E001",
            db_config=DB_CONFIG
        )
        
        if stats:
            logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")