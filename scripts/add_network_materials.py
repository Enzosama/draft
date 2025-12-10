#!/usr/bin/env python3
"""
Script to add computer network materials to the database.
These materials will be available for practice/luyện tập.
"""

import sqlite3
import sys
from datetime import datetime

def add_network_materials():
    """Add computer network materials to the database"""
    
    # Materials data
    materials = [
        {
            "title": "Definition and Basic Benefits of Computer Networks",
            "author": "Google Drive",
            "subject": "Tin học",
            "category": "Tài Liệu",
            "description": "An overview of a computer network as a system of interconnected computers for sharing resources and data, along with practical benefits like hardware saving and easy information exchange.",
            "file_url": "https://drive.google.com/file/d/1BavHZujFeTMqELK0f8zpc6K9Fu4gGyI/view?usp=sharing"
        },
        {
            "title": "Basic Components and Network Architecture",
            "author": "Google Drive", 
            "subject": "Tin học",
            "category": "Tài Liệu",
            "description": "Analysis of the fundamental components of a computer network, such as End Systems, Transmission Media, and Communication Protocols, along with common network architectures (Client-Server, Peer-to-Peer).",
            "file_url": "https://drive.google.com/file/d/19kyIgegjc_kxTbBo3JLNnQ86c6lWATGU/view?usp=sharing"
        },
        {
            "title": "The OSI and TCP/IP Layered Reference Models",
            "author": "Google Drive",
            "subject": "Tin học", 
            "category": "Tài Liệu",
            "description": "Explanation of the layering principle and functions of each layer in the 7-layer OSI reference model and the TCP/IP model, clarifying the role of each layer in abstracting and reusing protocols.",
            "file_url": "https://drive.google.com/file/d/15bRTZ1v8cEy2ZhvLaHTx9O5MVnSKzsDd/view?usp=sharing"
        },
        {
            "title": "IP Address Classification and Subnetting Techniques",
            "author": "Google Drive",
            "subject": "Tin học",
            "category": "Tài Liệu", 
            "description": "Study of IP address classification (Class A, B, C) and the use of subnet masks to divide a large network into smaller subnets (subnetting) to optimize address space management and utilization.",
            "file_url": "https://drive.google.com/file/d/1EdRDvTWbhanv793cAT4DPq30O-z7cLcB/view?usp=sharing"
        },
        {
            "title": "The Application Layer and its Protocols",
            "author": "Google Drive",
            "subject": "Tin học",
            "category": "Tài Liệu",
            "description": "Survey of the principles of the Application Layer and its main protocols such as DNS (Domain Name System), HTTP (for the Web), along with email protocols (SMTP, POP3, IMAP) serving end-users.",
            "file_url": "https://drive.google.com/file/d/1NHeWPGhi3OhBpIzasyFltj7TQUiDMAq8/view?usp=sharing"
        },
        {
            "title": "The Transport Layer: TCP and UDP Protocols",
            "author": "Google Drive",
            "subject": "Tin học",
            "category": "Tài Liệu",
            "description": "Comparison of the two main Transport Layer protocols: TCP (connection-oriented, reliable protocol) with its principles of connection establishment/release and congestion control, and UDP (connectionless protocol).",
            "file_url": "https://drive.google.com/file/d/1OyEsYhRII8A7krkuQg8JyBNUb8u8Cgiz/view?usp=sharing"
        },
        {
            "title": "The Network Layer: Routing Principles and IP",
            "author": "Google Drive",
            "subject": "Tin học",
            "category": "Tài Liệu",
            "description": "Analysis of Routing principles in IP networks, the structure of IP packets, routing tables, and the difference between routing algorithms like Distance Vector and Link State.",
            "file_url": "https://drive.google.com/file/d/1xchK6QY3OY78tx0mLtRIFUb6mSdnBqiP/view?usp=sharing"
        },
        {
            "title": "Basic Network Practical Guide (IT3080)",
            "author": "Google Drive",
            "subject": "Tin học",
            "category": "Tài Liệu",
            "description": "A collection of essential practical exercises, including network cable crimping skills, building and configuring a LAN, setting up static routing, and using tools to analyze network protocol behavior.",
            "file_url": "https://drive.google.com/file/d/1vdYxcMx_cg8uilxRh5QrVIxO-VgQsvLY/view?usp=sharing"
        }
    ]
    
    try:
        # Connect to database
        conn = sqlite3.connect('/Users/enzo/Downloads/perl_python/backend/db.sqlite')
        cursor = conn.cursor()
        
        # Get current date
        current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        added_count = 0
        
        for material in materials:
            try:
                # Check if material already exists
                cursor.execute("""
                    SELECT id FROM posts 
                    WHERE title = ? AND file_url = ?
                """, (material['title'], material['file_url']))
                
                if cursor.fetchone():
                    print(f"⏭️  Skipped (already exists): {material['title']}")
                    continue
                
                # Insert new material
                cursor.execute("""
                    INSERT INTO posts (title, author, date, subject, category, description, views, downloads, class, specialized, file_url, user_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?, ?)
                """, (
                    material['title'],
                    material['author'],
                    current_date,
                    material['subject'],
                    material['category'],
                    material['description'],
                    None,  # class
                    None,  # specialized
                    material['file_url'],
                    None,  # user_id
                    current_datetime,
                    current_datetime
                ))
                
                added_count += 1
                print(f"✅ Added: {material['title']}")
                
            except sqlite3.Error as e:
                print(f"❌ Error adding {material['title']}: {e}")
                continue
        
        # Commit changes
        conn.commit()
        print(f"\n🎉 Successfully added {added_count} network materials to database!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM posts WHERE subject = 'Tin học'")
        total_tin_hoc = cursor.fetchone()[0]
        print(f"📊 Total computer science materials: {total_tin_hoc}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Adding computer network materials to database...")
    success = add_network_materials()
    sys.exit(0 if success else 1)