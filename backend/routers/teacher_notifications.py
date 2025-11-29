from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.database import db
from backend.middleware.auth import require_teacher, get_current_user

router = APIRouter(prefix="/api/teacher/notifications", tags=["teacher-notifications"])

class NotificationCreate(BaseModel):
    classroom_id: int
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=2000)
    is_announcement: bool = False

class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    is_announcement: Optional[bool] = None

class NotificationResponse(BaseModel):
    id: int
    classroom_id: int
    title: str
    content: str
    is_announcement: bool
    created_by: int
    created_at: str
    unread_count: int

class StudentNotificationResponse(BaseModel):
    id: int
    classroom_id: int
    title: str
    content: str
    is_announcement: bool
    created_at: str
    is_read: bool
    read_at: Optional[str] = None

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(payload: NotificationCreate, current_user: dict = Depends(require_teacher)):
    """Create a notification for a classroom"""
    # Verify classroom belongs to teacher
    classroom = await db.fetch_one("SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?", 
                                   [payload.classroom_id, current_user["id"]])
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    # Create notification and get the ID
    notification_id = await db.insert(
        "INSERT INTO notifications (classroom_id, title, content, is_announcement, created_by) VALUES (?, ?, ?, ?, ?)",
        [payload.classroom_id, payload.title, payload.content, payload.is_announcement, current_user["id"]]
    )
    
    if not notification_id:
        raise HTTPException(status_code=500, detail="Failed to create notification")
    
    # Get notification with unread count (use LEFT JOIN to handle classrooms with no students)
    notification = await db.fetch_one(
        """SELECT n.id, n.classroom_id, n.title, n.content, n.is_announcement, n.created_by, n.created_at,
                  COUNT(DISTINCT cs.student_id) as unread_count
           FROM notifications n
           LEFT JOIN classroom_students cs ON n.classroom_id = cs.classroom_id
           WHERE n.id = ?
           GROUP BY n.id""",
        [notification_id]
    )
    
    return notification

@router.get("/classroom/{classroom_id}", response_model=List[NotificationResponse])
async def list_classroom_notifications(classroom_id: int, current_user: dict = Depends(require_teacher)):
    """List all notifications for a classroom"""
    # Verify classroom belongs to teacher
    classroom = await db.fetch_one("SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?", 
                                   [classroom_id, current_user["id"]])
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    notifications = await db.fetch_all(
        """SELECT n.id, n.classroom_id, n.title, n.content, n.is_announcement, n.created_by, n.created_at,
                  COUNT(DISTINCT cs.student_id) - COUNT(DISTINCT nr.student_id) as unread_count
           FROM notifications n
           JOIN classroom_students cs ON n.classroom_id = cs.classroom_id
           LEFT JOIN notification_reads nr ON n.id = nr.notification_id
           WHERE n.classroom_id = ?
           GROUP BY n.id
           ORDER BY n.created_at DESC""",
        [classroom_id]
    )
    
    return notifications

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(notification_id: int, payload: NotificationUpdate, current_user: dict = Depends(require_teacher)):
    """Update a notification"""
    # Verify notification belongs to teacher's classroom
    notification = await db.fetch_one(
        """SELECT n.id FROM notifications n
           JOIN classrooms c ON n.classroom_id = c.id
           WHERE n.id = ? AND c.teacher_id = ?""",
        [notification_id, current_user["id"]]
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")
    
    # Build update query
    update_fields = []
    params = []
    
    if payload.title is not None:
        update_fields.append("title = ?")
        params.append(payload.title)
    
    if payload.content is not None:
        update_fields.append("content = ?")
        params.append(payload.content)
    
    if payload.is_announcement is not None:
        update_fields.append("is_announcement = ?")
        params.append(payload.is_announcement)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    params.append(notification_id)
    
    await db.execute(
        f"UPDATE notifications SET {', '.join(update_fields)} WHERE id = ?",
        params
    )
    
    # Return updated notification
    notification = await db.fetch_one(
        """SELECT n.id, n.classroom_id, n.title, n.content, n.is_announcement, n.created_by, n.created_at,
                  COUNT(DISTINCT cs.student_id) - COUNT(DISTINCT nr.student_id) as unread_count
           FROM notifications n
           JOIN classroom_students cs ON n.classroom_id = cs.classroom_id
           LEFT JOIN notification_reads nr ON n.id = nr.notification_id
           WHERE n.id = ?
           GROUP BY n.id""",
        [notification_id]
    )
    
    return notification

@router.delete("/{notification_id}")
async def delete_notification(notification_id: int, current_user: dict = Depends(require_teacher)):
    """Delete a notification"""
    # Verify notification belongs to teacher's classroom
    notification = await db.fetch_one(
        """SELECT n.id FROM notifications n
           JOIN classrooms c ON n.classroom_id = c.id
           WHERE n.id = ? AND c.teacher_id = ?""",
        [notification_id, current_user["id"]]
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")
    
    await db.execute("DELETE FROM notifications WHERE id = ?", [notification_id])
    
    return {"message": "Notification deleted successfully"}

# Student notification endpoints
@router.get("/student/my-notifications", response_model=List[StudentNotificationResponse])
async def get_student_notifications(current_user: dict = Depends(get_current_user)):
    """Get notifications for the current student"""
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can view notifications")
    
    notifications = await db.fetch_all(
        """SELECT n.id, n.classroom_id, n.title, n.content, n.is_announcement, n.created_at,
                  CASE WHEN nr.notification_id IS NOT NULL THEN 1 ELSE 0 END as is_read,
                  nr.read_at
           FROM notifications n
           JOIN classroom_students cs ON n.classroom_id = cs.classroom_id
           LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
           WHERE cs.student_id = ?
           ORDER BY n.created_at DESC""",
        [current_user["id"], current_user["id"]]
    )
    
    return notifications

@router.post("/student/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can mark notifications as read")
    
    # Verify student has access to this notification
    notification = await db.fetch_one(
        """SELECT n.id FROM notifications n
           JOIN classroom_students cs ON n.classroom_id = cs.classroom_id
           WHERE n.id = ? AND cs.student_id = ?""",
        [notification_id, current_user["id"]]
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")
    
    # Mark as read (ignore if already read)
    await db.execute(
        "INSERT OR IGNORE INTO notification_reads (notification_id, student_id) VALUES (?, ?)",
        [notification_id, current_user["id"]]
    )
    
    return {"message": "Notification marked as read"}

@router.post("/student/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read for the current student"""
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can mark notifications as read")
    
    # Get all unread notifications for this student
    notifications = await db.fetch_all(
        """SELECT n.id FROM notifications n
           JOIN classroom_students cs ON n.classroom_id = cs.classroom_id
           LEFT JOIN notification_reads nr ON n.id = nr.notification_id AND nr.student_id = ?
           WHERE cs.student_id = ? AND nr.notification_id IS NULL""",
        [current_user["id"], current_user["id"]]
    )
    
    # Mark all as read
    for notification in notifications:
        await db.execute(
            "INSERT OR IGNORE INTO notification_reads (notification_id, student_id) VALUES (?, ?)",
            [notification["id"], current_user["id"]]
        )
    
    return {"message": f"Marked {len(notifications)} notifications as read"}