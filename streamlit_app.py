import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

PASSWORD = "ycenc1308"

# 로그인 함수
def login():
    st.title("🎈 지자체 크롤링 로그인")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if password == PASSWORD:
            st.session_state.logged_in = True
            # 접속 이력 기록
            log_access()
            st.success("로그인 성공!")
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
# 접속 이력 기록 함수
def log_access():
    ip = get_ip()
    access_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_agent = st.session_state.user_agent if 'user_agent' in st.session_state else 'unknown'
    
    log_data = {
        "접속시간": [access_time],
        "IP 주소": [ip],
        "User Agent": [user_agent]
    }
    
    # 로그 파일 저장 (CSV 또는 데이터베이스로 변경 가능)
    log_df = pd.DataFrame(log_data)
    if os.path.exists("access_log.csv"):
        log_df.to_csv("access_log.csv", mode='a', header=False, index=False)
    else:
        log_df.to_csv("access_log.csv", mode='w', header=True, index=False)
    
    st.write(f"접속 기록: IP={ip}, 접속시간={access_time}, User Agent={user_agent}")

# 사용자 IP 주소 가져오기
def get_ip():
    try:
        # 외부 API를 사용하여 IP 주소 가져오기
        ip_data = requests.get('https://api64.ipify.org?format=json').json()
        return ip_data['ip']
    except:
        return 'Unknown'


def main_app():
    st.title("🎈 지자체 크롤링")
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

    # 접속 이력 확인
    st.subheader("접속 이력 기록")
    
    # access_log.csv 파일이 있는지 확인
    log_file_path = "access_log.csv"
    if os.path.exists(log_file_path):
        # CSV 파일 읽기
        log_df = pd.read_csv(log_file_path)
        st.write("최근 접속 이력:")
        st.dataframe(log_df)  # 데이터를 표 형태로 표시
    else:
        st.write("접속 이력 파일을 찾을 수 없습니다.")

# Main 실행 함수
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'user_agent' not in st.session_state:
    # 브라우저의 User Agent 정보를 가져오기 위해 session_state에 저장
    st.session_state.user_agent = st.experimental_get_query_params().get('user_agent', ['unknown'])[0]

if not st.session_state.logged_in:
    login()
else:
    main_app()
