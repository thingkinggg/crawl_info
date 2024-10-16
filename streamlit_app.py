import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime, timedelta
import sqlite3
import hashlib
import uuid

st.set_page_config(layout="wide")

# 하드코딩된 관리자 정보
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password_123"  # 실제 운영 환경에서는 더 강력한 비밀번호를 사용해야 합니다

# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect('user_database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# 데이터베이스 초기화 함수
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 사용자 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  salt TEXT NOT NULL,
                  is_admin INTEGER DEFAULT 0)''')
    
    # 로그인 이력 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS login_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

# 데이터베이스 초기화
init_db()

def hash_password(password, salt=None):
    if salt is None:
        salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest(), salt

def verify_password(stored_password, stored_salt, provided_password):
    return stored_password == hashlib.sha256(stored_salt.encode() + provided_password.encode()).hexdigest()

def create_user(username, password, is_admin=0):
    conn = get_db_connection()
    c = conn.cursor()
    hashed_password, salt = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password, salt, is_admin) VALUES (?, ?, ?, ?)", 
                  (username, hashed_password, salt, is_admin))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    if username == ADMIN_USERNAME:
        return password == ADMIN_PASSWORD
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT password, salt FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        stored_password, stored_salt = result['password'], result['salt']
        return verify_password(stored_password, stored_salt, password)
    return False

def change_password(username, new_password):
    if username != ADMIN_USERNAME:
        conn = get_db_connection()
        c = conn.cursor()
        hashed_password, salt = hash_password(new_password)
        c.execute("UPDATE users SET password=?, salt=? WHERE username=?", 
                  (hashed_password, salt, username))
        conn.commit()
        conn.close()

def log_login(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO login_history (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

def get_login_history(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT login_time FROM login_history WHERE username=? ORDER BY login_time DESC LIMIT 5", (username,))
    result = c.fetchall()
    conn.close()
    return result

def is_admin(username):
    if username == ADMIN_USERNAME:
        return True
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result['is_admin'] if result else False

def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, is_admin FROM users")
    users = c.fetchall()
    conn.close()
    return [(ADMIN_USERNAME, 1)] + [(user['username'], user['is_admin']) for user in users]

def delete_user(username):
    if username != ADMIN_USERNAME:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()
        conn.close()

def toggle_admin(username):
    if username != ADMIN_USERNAME:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET is_admin = 1 - is_admin WHERE username=?", (username,))
        conn.commit()
        conn.close()

# Admin 계정이 없으면 생성
def ensure_admin_exists():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (ADMIN_USERNAME,))
    if not c.fetchone():
        create_user(ADMIN_USERNAME, ADMIN_PASSWORD, is_admin=1)
    conn.close()

# 애플리케이션 시작 시 Admin 계정 확인
ensure_admin_exists()

def login_page():
    st.title("🎈 지자체 크롤링 로그인")
    username = st.text_input("사용자 이름")
    password = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if verify_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.is_admin = is_admin(username)
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
        elif username == ADMIN_USERNAME:
            st.error("이 사용자 이름은 사용할 수 없습니다.")
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
    if st.session_state.username == ADMIN_USERNAME:
        st.error("관리자 계정의 비밀번호는 변경할 수 없습니다.")
        return
    
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

def admin_page():
    st.title("사용자 관리")
    users = get_all_users()
    
    for user in users:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"사용자: {user[0]}")
        with col2:
            if user[0] != ADMIN_USERNAME and st.button("삭제", key=f"delete_{user[0]}"):
                delete_user(user[0])
                st.success(f"{user[0]} 사용자가 삭제되었습니다.")
                st.rerun()
        with col3:
            admin_status = "관리자" if user[1] else "일반사용자"
            if user[0] != ADMIN_USERNAME and st.button(f"{admin_status} 전환", key=f"toggle_{user[0]}"):
                toggle_admin(user[0])
                st.success(f"{user[0]}의 관리자 상태가 변경되었습니다.")
                st.rerun()
        with col4:
            if user[0] != ADMIN_USERNAME and st.button("비밀번호 초기화", key=f"reset_{user[0]}"):
                new_password = "password123"  # 초기 비밀번호
                change_password(user[0], new_password)
                st.success(f"{user[0]}의 비밀번호가 초기화되었습니다.")
              
def main_app():
    st.title("🎈 지자체 크롤링")
    st.write("2024년 10월 15일 22:33 업데이트\n")
    st.write("작업진행상황 : 102개 site 최신 1page 수집 작업 완료\n")
    st.write("향후진행계획 : 나머지 site 최신 페이지 수집, 수집실패사이트점검, 2page이상 수집하도록 변경")
    
    # 여기에 기존의 메인 애플리케이션 코드를 넣습니다.
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
    def get_recent_files(file_prefix):
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
        return sorted(recent_files, reverse=True)
    
    # df_log 파일 읽기
    recent_file_path, previous_file_path = get_two_recent_files('df_log')
    
    # 최근 파일 처리
    if recent_file_path:
        df_log_recent = pd.read_excel(recent_file_path, engine='openpyxl')
        st.write(f" - 최근 df_log 파일: {recent_file_path}에서 데이터를 읽었습니다.")
    else:
        st.write(" - 최근 일주일 내에 df_log 파일을 찾을 수 없습니다.")
    
    # 이전 파일 처리
    if previous_file_path:
        df_log_previous = pd.read_excel(previous_file_path, engine='openpyxl')
        st.write(f" - 이전 df_log 파일: {previous_file_path}에서 데이터를 읽었습니다.")
    else:
        st.write(" - 이전 df_log 파일을 찾을 수 없습니다.")
    
    # df_log 파일 처리
    if recent_file_path and previous_file_path:
        merge_columns = ['URL', 'unique_date', 'max_date']
        df_merged = pd.merge(df_log_recent, 
                             df_log_previous[merge_columns], 
                             on='URL', 
                             suffixes=('_recent', '_previous'), 
                             how='left')
        
        st.write("최근 파일과 이전 파일을 left join한 데이터:")
        st.dataframe(df_merged, use_container_width=True)
    
        df_merged['max_date_recent'] = pd.to_datetime(df_merged['max_date_recent'], errors='coerce')
        
        today_str = today.strftime('%Y-%m-%d')
        max_date_recent = df_merged['max_date_recent'].max()
        problematic_rows = df_merged[(df_merged['unique_date_recent'].isnull()) | ((df_merged['unique_date_recent'] == 1) & (df_merged['max_date_recent'] == max_date_recent))]
        
        if not problematic_rows.empty:
            st.warning(f"덜 수집된 사이트 리스트는 아래와 같습니다. 직접 접속 후 확인 필요합니다.")
            st.write("확인해야 할 사이트:")
            st.dataframe(problematic_rows, use_container_width=True)
        else:
            st.success("unique_date가 Null이거나 1인 데이터가 없습니다.")
    else:
        st.write("비교를 위해 이전 파일과 최근 파일이 모두 필요합니다.")
    
    # df_list 파일 읽기 및 처리
    df_list_file_paths = get_recent_files('df_list')
    if df_list_file_paths:
        combined_df_list = pd.DataFrame()
        
        for file_path in df_list_file_paths:
            df = pd.read_excel(file_path, engine='openpyxl')
            combined_df_list = pd.concat([combined_df_list, df], ignore_index=True)
        
        combined_df_list = combined_df_list.drop_duplicates()
    
        column_order = ['SITE_NO', '출처', '제목', 'URL', '작성일']
        combined_df_list = combined_df_list.reindex(columns=column_order)
    
        combined_df_list['URL'] = combined_df_list['URL'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
    
        combined_df_list['작성일'] = pd.to_datetime(combined_df_list['작성일'], errors='coerce')
        combined_df_list = combined_df_list.sort_values(by='작성일', ascending=False)
    
        st.markdown("""
            <style>
            table {
                width: 100%;
            }
            th, td {
                padding: 5px;
            }
            th {
                text-align: left;
            }
            td {
                max-width: 200px;
                overflow-wrap: break-word;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.write(f"최근 일주일 내에 df_list 파일 {len(df_list_file_paths)}개를 불러왔습니다.")
        
        search_keyword = st.text_input("df_list 파일에서 검색할 키워드를 입력하세요")
    
        if search_keyword:
            search_results = combined_df_list[combined_df_list['제목'].str.contains(search_keyword, na=False)]
            st.write(f"'{search_keyword}' 검색 결과:")
            st.markdown(search_results.to_html(escape=False), unsafe_allow_html=True)
        else:
            st.write("df_list 파일의 전체 데이터:")
            st.markdown(combined_df_list.to_html(escape=False), unsafe_allow_html=True)
    else:
        st.write("최근 일주일 내에 df_list 파일을 찾을 수 없습니다.")
    
    # 중간 일배치 수집 로그 텍스트
    st.subheader("일배치 수집 로그")
    log_text = """
    Processing rows:   0%|          | 0/103 [00:00<?, ?it/s]<ipython-input-1-b1a9e246c457>:94: FutureWarning: Setting an item of incompatible dtype is deprecated and will raise in a future error of pandas. Value '2023-03-17' has dtype incompatible with float64, please explicitly cast to a compatible dtype first.
      df.at[index, 'min_date'] = min_date
    <ipython-input-1-b1a9e246c457>:95: FutureWarning: Setting an item of incompatible dtype is deprecated and will raise in a future error of pandas. Value '2024-09-03' has dtype incompatible with float64, please explicitly cast to a compatible dtype first.
      df.at[index, 'max_date'] = max_date
    Processing rows:  42%|████▏     | 43/103 [04:42<07:58,  7.98s/it]경기도_광명시페이지 정보를 추출할 수 없습니다.
    Processing rows:  46%|████▌     | 47/103 [04:50<03:09,  3.38s/it]요청 오류: 417 Client Error: Expectation Failed for url: https://www.gimpo.go.kr/portal/ntfcPblancList.do?key=1004&cate_cd=1&searchCnd=40900000000
    경기도_김포시페이지 정보를 추출할 수 없습니다.
    Processing rows:  84%|████████▍ | 87/103 [10:51<02:32,  9.54s/it]강원도_정선군페이지 정보를 추출할 수 없습니다.
    Processing rows: 100%|██████████| 103/103 [13:51<00:00,  8.07s/it]
    """
    st.text(log_text)
    # (df_log 파일 처리, df_list 파일 처리, 로그 표시 등)

    if st.button("비밀번호 변경"):
        st.session_state.change_password = True
        st.rerun()
    
    if st.button("로그인 이력 보기"):
        st.session_state.show_history = True
        st.rerun()

    if st.session_state.is_admin:
      if st.button("사용자 관리"):
          st.session_state.admin_page = True
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
    elif 'admin_page' in st.session_state and st.session_state.admin_page and st.session_state.is_admin:
        admin_page()
    else:
        main_app()
