import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# 사용자 정보
users = {
    "admin": "yc123",
    "yc": "yc123"
}

def login():
    st.title("🎈 지자체 크롤링 로그인")
    
    # ID와 패스워드 입력 필드
    username = st.text_input("아이디를 입력하세요")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    
    if st.button("로그인"):
        # 사용자 인증
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("로그인 성공!")
            st.experimental_rerun()  # 로그인 성공 후 화면 갱신
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

def main_app():
    st.title("🎈 지자체 크롤링")
    st.write(f"안녕하세요, {st.session_state.username}님!")
    st.write("2024년 10월 15일 22:33 업데이트\n")
    st.write("작업진행상황 : 102개 site 최신 1page 수집 작업 완료\n")
    st.write("향후진행계획 : 나머지 site 최신 페이지 수집, 수집실패사이트점검, 2page이상 수집하도록 변경")
    
    # 오늘 일자 및 최근 7일 계산
    today = datetime.today()
    one_week_ago = today - timedelta(days=7)
    today_str = today.strftime('%Y%m%d')
    
    # 최근 파일 2개를 반환하는 함수
    def get_two_recent_files(file_prefix):
        files = glob.glob(f"{file_prefix}_*.xlsx")
        recent_files = []
        for file in files:
            file_date_str = file.split('_')[-1].replace('.xlsx', '')
            try:
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                if one_week_ago <= file_date <= today:
                    recent_files.append(file)
            except ValueError:
                continue
        if len(recent_files) >= 2:
            return sorted(recent_files, reverse=True)[:2]
        elif len(recent_files) == 1:
            return recent_files[0], None
        return None, None
    
    # 최근 일주일 내의 파일을 읽어오기 위한 함수
    def get
