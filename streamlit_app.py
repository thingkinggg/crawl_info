import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime, timedelta
import sqlite3
import hashlib
import uuid

# 데이터베이스 설정
conn = sqlite3.connect('user_database.db')
c = conn.cursor()

# 사용자 테이블 생성
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              salt TEXT NOT NULL)''')

# 로그인 이력 테이블 생성
c.execute('''CREATE TABLE IF NOT EXISTS login_history
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL,
              login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

conn.commit()

def hash_password(password, salt=None):
    if salt is None:
        salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest(), salt

def verify_password(stored_password, stored_salt, provided_password):
    return stored_password == hashlib.sha256(stored_salt.encode() + provided_password.encode()).hexdigest()

def create_user(username, password):
    hashed_password, salt = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password, salt) VALUES (?, ?, ?)", 
                  (username, hashed_password, salt))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    c.execute("SELECT password, salt FROM users WHERE username=?", (username,))
    result = c.fetchone()
    if result:
        stored_password, stored_salt = result
        return verify_password(stored_password, stored_salt, password)
    return False

def change_password(username, new_password):
    hashed_password, salt = hash_password(new_password)
    c.execute("UPDATE users SET password=?, salt=? WHERE username=?", 
              (hashed_password, salt, username))
    conn.commit()

def log_login(username):
    c.execute("INSERT INTO login_history (username) VALUES (?)", (username,))
    conn.commit()

def get_login_history(username):
    c.execute("SELECT login_time FROM login_history WHERE username=? ORDER BY login_time DESC LIMIT 5", (username,))
    return c.fetchall()

def login_page():
    st.title("🎈 지자체 크롤링 로그인")
    username = st.text_input("사용자 이름")
    password = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if verify_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            log_login(username)
            st.success("로그인 성공!")
            st.rerun()
        else:
            st.error("사용자 이름 또는 비밀번호가 올바르지 않습니다.")
    
    if st.button("새 사용자 등록"):
        st.session_state.register = True
        st.rerun()

def register_page():
    st.title("새 사용자 등록")
    username = st.text_input("사용자 이름")
    password = st.text_input("비밀번호", type="password")
    confirm_password = st.text_input("비밀번호 확인", type="password")
    if st.button("등록"):
        if password != confirm_password:
            st.error("비밀번호가 일치하지 않습니다.")
        elif create_user(username, password):
            st.success("사용자가 성공적으로 등록되었습니다.")
            st.session_state.register = False
            st.rerun()
        else:
            st.error("이미 존재하는 사용자 이름입니다.")
    
    if st.button("로그인 페이지로 돌아가기"):
        st.session_state.register = False
        st.rerun()

def change_password_page():
    st.title("비밀번호 변경")
    current_password = st.text_input("현재 비밀번호", type="password")
    new_password = st.text_input("새 비밀번호", type="password")
    confirm_new_password = st.text_input("새 비밀번호 확인", type="password")
    if st.button("비밀번호 변경"):
        if verify_user(st.session_state.username, current_password):
            if new_password == confirm_new_password:
                change_password(st.session_state.username, new_password)
                st.success("비밀번호가 성공적으로 변경되었습니다.")
            else:
                st.error("새 비밀번호가 일치하지 않습니다.")
        else:
            st.error("현재 비밀번호가 올바르지 않습니다.")

def show_login_history():
    st.title("로그인 이력")
    history = get_login_history(st.session_state.username)
    for login_time in history:
        st.write(login_time[0])

def main_app():
    st.title("🎈 지자체 크롤링")
    st.write("2024년 10월 15일 22:33 업데이트\n")
    st.write("작업진행상황 : 102개 site 최신 1page 수집 작업 완료\n")
    st.write("향후진행계획 : 나머지 site 최신 페이지 수집, 수집실패사이트점검, 2page이상 수집하도록 변경")
    
    # 여기에 기존의 메인 애플리케이션 코드를 넣습니다.
    # (df_log 파일 처리, df_list 파일 처리, 로그 표시 등)

    if st.button("비밀번호 변경"):
        st.session_state.change_password = True
        st.rerun()
    
    if st.button("로그인 이력 보기"):
        st.session_state.show_history = True
        st.rerun()
    
    if st.button("로그아웃"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# 메인 실행 흐름
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    if 'register' in st.session_state and st.session_state.register:
        register_page()
    else:
        login_page()
else:
    if 'change_password' in st.session_state and st.session_state.change_password:
        change_password_page()
    elif 'show_history' in st.session_state and st.session_state.show_history:
        show_login_history()
    else:
        main_app()

# 데이터베이스 연결 종료
conn.close()
