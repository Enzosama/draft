#!/usr/bin/env python3
"""
Test script for the new teacher and classroom functionality
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

# Test data
test_admin = {
    "fullname": "Admin User",
    "email": "admin@test.com",
    "phone": "0123456789",
    "password": "admin123"
}

test_teacher = {
    "fullname": "Teacher User",
    "email": "teacher@test.com",
    "phone": "0987654321",
    "password": "teacher123",
    "subject": "Toán học"
}

test_student = {
    "fullname": "Student User",
    "email": "student@test.com",
    "phone": "0112233445",
    "password": "student123"
}

def register_user(user_data):
    """Register a new user"""
    response = requests.post(f"{BASE_URL}/api/register", json=user_data)
    return response.json() if response.status_code == 201 else None

def login_user(email, password):
    """Login and get token"""
    response = requests.post(f"{BASE_URL}/api/login", json={"email": email, "password": password})
    return response.json() if response.status_code == 200 else None

def test_teacher_functionality():
    """Test all teacher functionality"""
    print("🧪 Testing Teacher and Classroom Functionality")
    print("=" * 50)
    
    # Register test users
    print("1. Registering test users...")
    register_user(test_student)
    time.sleep(0.5)
    
    # Login as admin to create teacher
    print("2. Creating teacher account...")
    admin_login = login_user("admin@test.com", "admin123")
    if not admin_login:
        print("❌ Admin login failed")
        return
    
    admin_token = admin_login["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create teacher via admin endpoint
    teacher_response = requests.post(
        f"{BASE_URL}/api/admin/teachers/",
        json=test_teacher,
        headers=headers
    )
    
    if teacher_response.status_code == 201:
        teacher_data = teacher_response.json()
        print(f"✅ Teacher created: {teacher_data['email']}")
    elif teacher_response.status_code == 400 and "already registered" in teacher_response.text:
        # Teacher already exists, get the existing one
        teachers_response = requests.get(f"{BASE_URL}/api/admin/teachers/", headers=headers)
        if teachers_response.status_code == 200:
            teachers = teachers_response.json()
            teacher_data = next((t for t in teachers if t['email'] == test_teacher['email']), None)
            if teacher_data:
                print(f"✅ Using existing teacher: {teacher_data['email']}")
            else:
                print(f"❌ Could not find existing teacher")
                return
        else:
            print(f"❌ Could not list teachers: {teachers_response.text}")
            return
    else:
        print(f"❌ Teacher creation failed: {teacher_response.text}")
        return
    
    # Login as teacher
    print("3. Testing teacher login...")
    teacher_login = login_user(test_teacher["email"], test_teacher["password"])
    if not teacher_login:
        print("❌ Teacher login failed")
        return
    
    teacher_token = teacher_login["access_token"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    print("✅ Teacher login successful")
    
    # Test classroom creation
    print("4. Testing classroom creation...")
    classroom_data = {
        "name": "Lớp Toán 12A1",
        "description": "Lớp học Toán cao cấp",
        "subject": "Toán học"
    }
    
    classroom_response = requests.post(
        f"{BASE_URL}/api/teacher/classrooms/",
        json=classroom_data,
        headers=teacher_headers
    )
    
    if classroom_response.status_code != 201:
        print(f"❌ Classroom creation failed: {classroom_response.text}")
        return
    
    classroom = classroom_response.json()
    print(f"✅ Classroom created: {classroom['name']} (Code: {classroom['code']})")
    
    # Test post creation as teacher
    print("5. Testing teacher post creation...")
    post_data = {
        "title": "Bài học về Đạo hàm",
        "date": "2024-11-15",
        "subject": "Toán học",
        "category": "Bài giảng",
        "description": "Giới thiệu về đạo hàm và ứng dụng",
        "class_field": "12",
        "specialized": "Toán cao cấp"
    }
    
    post_response = requests.post(
        f"{BASE_URL}/api/teacher/posts/",
        json=post_data,
        headers=teacher_headers
    )
    
    if post_response.status_code != 201:
        print(f"❌ Teacher post creation failed: {post_response.text}")
        return
    
    teacher_post = post_response.json()
    print(f"✅ Teacher post created: {teacher_post['title']}")
    
    # Test assigning post to classroom
    print("6. Testing post assignment to classroom...")
    assign_response = requests.post(
        f"{BASE_URL}/api/teacher/posts/{teacher_post['id']}/assign/{classroom['id']}",
        headers=teacher_headers
    )
    
    if assign_response.status_code != 201:
        print(f"❌ Post assignment failed: {assign_response.text}")
        return
    
    print("✅ Post assigned to classroom successfully")
    
    # Test notification creation
    print("7. Testing notification creation...")
    notification_data = {
        "classroom_id": classroom['id'],
        "title": "Thông báo quan trọng",
        "content": "Ngày mai có bài kiểm tra giữa kỳ. Các em chuẩn bị kỹ nhé!",
        "is_announcement": True
    }
    
    notification_response = requests.post(
        f"{BASE_URL}/api/teacher/notifications/",
        json=notification_data,
        headers=teacher_headers
    )
    
    if notification_response.status_code != 201:
        print(f"❌ Notification creation failed: {notification_response.text}")
        return
    
    notification = notification_response.json()
    print(f"✅ Notification created: {notification['title']}")
    
    # Test student joining classroom
    print("8. Testing student joining classroom...")
    student_login = login_user(test_student["email"], test_student["password"])
    if not student_login:
        print("❌ Student login failed")
        return
    
    student_token = student_login["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    
    join_response = requests.post(
        f"{BASE_URL}/api/teacher/classrooms/join/{classroom['code']}",
        headers=student_headers
    )
    
    if join_response.status_code != 201:
        print(f"❌ Student join classroom failed: {join_response.text}")
        return
    
    print("✅ Student joined classroom successfully")
    
    # Test student viewing notifications
    print("9. Testing student viewing notifications...")
    student_notifications = requests.get(
        f"{BASE_URL}/api/teacher/notifications/student/my-notifications",
        headers=student_headers
    )
    
    if student_notifications.status_code != 200:
        print(f"❌ Student notifications failed: {student_notifications.text}")
        return
    
    notifications = student_notifications.json()
    print(f"✅ Student can see {len(notifications)} notifications")
    
    # Test student marking notification as read
    if notifications:
        print("10. Testing student marking notification as read...")
        mark_read_response = requests.post(
            f"{BASE_URL}/api/teacher/notifications/student/notifications/{notifications[0]['id']}/read",
            headers=student_headers
        )
        
        if mark_read_response.status_code != 200:
            print(f"❌ Mark notification as read failed: {mark_read_response.text}")
        else:
            print("✅ Notification marked as read successfully")
    
    # Test teacher viewing classroom students
    print("11. Testing teacher viewing classroom students...")
    students_response = requests.get(
        f"{BASE_URL}/api/teacher/classrooms/{classroom['id']}/students",
        headers=teacher_headers
    )
    
    if students_response.status_code != 200:
        print(f"❌ View classroom students failed: {students_response.text}")
        return
    
    students = students_response.json()
    print(f"✅ Teacher can see {len(students)} students in classroom")
    
    # Test teacher viewing their own posts
    print("12. Testing teacher viewing their posts...")
    my_posts_response = requests.get(
        f"{BASE_URL}/api/teacher/posts/",
        headers=teacher_headers
    )
    
    if my_posts_response.status_code != 200:
        print(f"❌ View teacher posts failed: {my_posts_response.text}")
        return
    
    my_posts = my_posts_response.json()
    print(f"✅ Teacher has {my_posts['total']} posts")
    
    # Test admin viewing all teachers
    print("13. Testing admin viewing all teachers...")
    teachers_response = requests.get(
        f"{BASE_URL}/api/admin/teachers/",
        headers=headers
    )
    
    if teachers_response.status_code != 200:
        print(f"❌ View all teachers failed: {teachers_response.text}")
        return
    
    all_teachers = teachers_response.json()
    print(f"✅ Admin can see {len(all_teachers)} teachers")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("✅ Teacher and classroom functionality is working correctly")

if __name__ == "__main__":
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        test_teacher_functionality()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")