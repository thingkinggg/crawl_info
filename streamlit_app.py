import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

PASSWORD = "ycenc1308"

def login():
    st.title("🎈 지자체 크롤링 로그인")
    password = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if password == PASSWORD:
            st.session_state.logged_in = True
            st.success("로그인 성공!")
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")

def main_app():
    st.title("🎈 지자체 크롤링")
    st.write("2024년 10월 21일 22:33 업데이트\n")
    st.write("작업진행상황 : 128개 site 최신 1page 수집 작업 완료\n")
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
   Processing rows:  28%|██▊       | 36/129 [03:08<12:30,  8.07s/it]경기도_수원_권선구페이지 정보를 추출할 수 없습니다.
Processing rows:  33%|███▎      | 43/129 [04:30<11:14,  7.84s/it]경기도_광명시페이지 정보를 추출할 수 없습니다.
Processing rows:  36%|███▋      | 47/129 [04:37<04:19,  3.16s/it]요청 오류: 417 Client Error: Expectation Failed for url: https://www.gimpo.go.kr/portal/ntfcPblancList.do?key=1004&cate_cd=1&searchCnd=40900000000
경기도_김포시페이지 정보를 추출할 수 없습니다.
Processing rows:  46%|████▌     | 59/129 [06:27<10:29,  9.00s/it]연결 타임아웃: 경기도_안성시 서버로부터 응답이 없습니다.
경기도_안성시페이지 정보를 추출할 수 없습니다.
Processing rows:  88%|████████▊ | 114/129 [15:45<03:21, 13.44s/it]WARNING:urllib3.connection:Failed to parse headers (url=https://www.geumsan.go.kr:443/kr/html/sub03/030302.html): [MissingHeaderBodySeparatorDefect()], unparsed data: 'P3P : CP="NOI CURa ADMa DEVa TAIa OUR DELa BUS IND PHY ONL UNI COM NAV INT DEM PRE"\r\nSet-Cookie: SIDNAME=ronty; path=/; HttpOnly; secure; SameSite=None; secure\r\nCache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0\r\nPragma: no-cache\r\nSet-Cookie: PHPSESSID=5pb84ecdnrmqi2sb8kvt4fbht6; path=/; HttpOnly; secure; SameSite=None\r\nExpires: Thu, 19 Nov 1981 08:52:00 GMT\r\n\r\n'
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/dist-packages/urllib3/connection.py", line 510, in getresponse
    assert_header_parsing(httplib_response.msg)
  File "/usr/local/lib/python3.10/dist-packages/urllib3/util/response.py", line 88, in assert_header_parsing
    raise HeaderParsingError(defects=defects, unparsed_data=unparsed_data)
urllib3.exceptions.HeaderParsingError: [MissingHeaderBodySeparatorDefect()], unparsed data: 'P3P : CP="NOI CURa ADMa DEVa TAIa OUR DELa BUS IND PHY ONL UNI COM NAV INT DEM PRE"\r\nSet-Cookie: SIDNAME=ronty; path=/; HttpOnly; secure; SameSite=None; secure\r\nCache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0\r\nPragma: no-cache\r\nSet-Cookie: PHPSESSID=5pb84ecdnrmqi2sb8kvt4fbht6; path=/; HttpOnly; secure; SameSite=None\r\nExpires: Thu, 19 Nov 1981 08:52:00 GMT\r\n\r\n'
Processing rows:  95%|█████████▍| 122/129 [17:16<01:34, 13.52s/it]전라도_군산시페이지 정보를 추출할 수 없습니다.
Processing rows:  96%|█████████▌| 124/129 [17:19<00:36,  7.28s/it]요청 오류: 400 Client Error: Bad Request for url: https://www.namwon.go.kr/board/post/list.do?boardUid=ff8080818ea1fec5018ea24137680031&menuUid=ff8080818e3beff0018e4077131b007a&beginDateStr=&endDateStr=&searchType=postTtl&keyword=%EC%A0%9C%EC%95%88&paramString=Us7WVBAxc13kgzv1JU3ayAslPphGSM%2FmlfdB4qtWC4OBeJsElaKmGl7kvQ4Au%2B3O&size=10
전라도_남원시페이지 정보를 추출할 수 없습니다.
Processing rows:  98%|█████████▊| 126/129 [17:59<00:39, 13.24s/it]연결 타임아웃: 전라도_전주시 서버로부터 응답이 없습니다.
전라도_전주시페이지 정보를 추출할 수 없습니다.
Processing rows: 100%|██████████| 129/129 [18:38<00:00,  8.67s/it]cleaned_dates 리스트가 비어 있습니다.
    """
    st.text(log_text)

# 메인 실행 흐름
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    main_app()
