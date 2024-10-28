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
        else:
            st.error("비밀번호가 올바르지 않습니다.")

def main_app():
    st.title("🎈 지자체 크롤링")
    update_time = st.session_state.get('update_time', "2024년 10월 27일 22:28 업데이트")
    st.write(f"{update_time}\n")
    st.write("작업진행상황 : 211개 전체 site 최신 1page 수집 작업 완료(1차완료) \n")
    st.write("향후진행계획 : 수집실패사이트점검, 2page이상 수집하도록 변경")
    
    # 오늘 일자 및 최근 7일 계산
    today = datetime.today()
    one_week_ago = today - timedelta(days=7)
    today_str = today.strftime('%Y%m%d')
    
   # 특정 접두사를 가지는 최근 파일들을 반환하는 함수
    def get_recent_files_by_date(file_prefix):
        files = glob.glob(f"{file_prefix}_*.xlsx")
        file_dates = []
        for file in files:
            file_date_str = file.split('_')[-1].replace('.xlsx', '')
            try:
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                if one_week_ago <= file_date <= today:
                    file_dates.append(file_date_str)
            except ValueError:
                continue
        return sorted(set(file_dates), reverse=True)
    
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
    
    # df_log 파일에서 최근 날짜 목록을 가져오기
    available_dates = get_recent_files_by_date('df_log')
    
    if available_dates:
        # 사용자가 선택한 날짜에 따른 파일 목록 표시
        selected_date = st.selectbox("날짜를 선택하세요", available_dates)
        
        # 선택된 날짜에 해당하는 df_log 파일 읽기
        df_log_files = glob.glob(f"df_log_{selected_date}.xlsx")
        
        if df_log_files:
            st.write(f"선택한 날짜: {selected_date}")
            
            combined_df_log = pd.DataFrame()
            for file_path in df_log_files:
                df = pd.read_excel(file_path, engine='openpyxl')
                df['파일명'] = os.path.basename(file_path)
                combined_df_log = pd.concat([combined_df_log, df], ignore_index=True)
            
            # Check problematic rows
            problematic_rows = combined_df_log[
                (combined_df_log['unique_date'].isnull()) | (combined_df_log['unique_date'] == 1) | (combined_df_log['unique_date'] == 0)
            ]
            
            if not problematic_rows.empty:
                st.warning(f"선택한 날짜({selected_date})에 덜 수집된 사이트 리스트는 아래와 같습니다. 직접 접속 후 확인 필요합니다.")
                st.write("확인해야 할 사이트:")
                st.dataframe(problematic_rows, use_container_width=True)
            else:
                st.success(f"선택한 날짜({selected_date})에는 unique_date가 Null이거나 1인 데이터가 없습니다.")
        else:
            st.write(f"선택한 날짜({selected_date})에 해당하는 df_log 파일을 찾을 수 없습니다.")
    else:
        st.write("최근 일주일 내에 df_log 파일을 찾을 수 없습니다.")
    
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
    
   # 중간 일배치 수집 로그 텍스트 관리
    log_text = """
   Processing rows:   0%|          | 0/211 [00:00<?, ?it/s]<ipython-input-5-c0391dc5c3fd>:112: FutureWarning: Setting an item of incompatible dtype is deprecated and will raise an error in a future version of pandas. Value '2023-03-17' has dtype incompatible with float64, please explicitly cast to a compatible dtype first.
  df.at[index, 'min_date'] = min_date
<ipython-input-5-c0391dc5c3fd>:113: FutureWarning: Setting an item of incompatible dtype is deprecated and will raise an error in a future version of pandas. Value '2024-09-03' has dtype incompatible with float64, please explicitly cast to a compatible dtype first.
  df.at[index, 'max_date'] = max_date
Processing rows:  20%|██        | 43/211 [04:30<21:53,  7.82s/it]경기도_광명시페이지 정보를 추출할 수 없습니다.
Processing rows:  22%|██▏       | 47/211 [04:38<08:54,  3.26s/it]요청 오류: 417 Client Error: Expectation Failed for url: https://www.gimpo.go.kr/portal/ntfcPblancList.do?key=1004&cate_cd=1&searchCnd=40900000000
경기도_김포시페이지 정보를 추출할 수 없습니다.
Processing rows:  28%|██▊       | 59/211 [06:34<23:57,  9.46s/it]연결 타임아웃: 경기도_안성시 서버로부터 응답이 없습니다.
경기도_안성시페이지 정보를 추출할 수 없습니다.
Processing rows:  32%|███▏      | 67/211 [07:48<21:52,  9.12s/it]페이지 로딩 시간이 초과되었습니다: 경기도_평택시
Processing rows:  43%|████▎     | 90/211 [12:09<17:02,  8.45s/it]읽기 타임아웃: 강원도_홍천군 서버가 데이터를 제공하는 시간이 초과되었습니다.
강원도_홍천군페이지 정보를 추출할 수 없습니다.
Processing rows:  54%|█████▍    | 114/211 [17:42<22:17, 13.79s/it]WARNING:urllib3.connection:Failed to parse headers (url=https://www.geumsan.go.kr:443/kr/html/sub03/030302.html): [MissingHeaderBodySeparatorDefect()], unparsed data: 'P3P : CP="NOI CURa ADMa DEVa TAIa OUR DELa BUS IND PHY ONL UNI COM NAV INT DEM PRE"\r\nSet-Cookie: SIDNAME=ronty; path=/; HttpOnly; secure; SameSite=None; secure\r\nCache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0\r\nPragma: no-cache\r\nSet-Cookie: PHPSESSID=vl6re9loeqlon179jjbui0o2e4; path=/; HttpOnly; secure; SameSite=None\r\nExpires: Thu, 19 Nov 1981 08:52:00 GMT\r\n\r\n'
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/dist-packages/urllib3/connection.py", line 510, in getresponse
    assert_header_parsing(httplib_response.msg)
  File "/usr/local/lib/python3.10/dist-packages/urllib3/util/response.py", line 88, in assert_header_parsing
    raise HeaderParsingError(defects=defects, unparsed_data=unparsed_data)
urllib3.exceptions.HeaderParsingError: [MissingHeaderBodySeparatorDefect()], unparsed data: 'P3P : CP="NOI CURa ADMa DEVa TAIa OUR DELa BUS IND PHY ONL UNI COM NAV INT DEM PRE"\r\nSet-Cookie: SIDNAME=ronty; path=/; HttpOnly; secure; SameSite=None; secure\r\nCache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0\r\nPragma: no-cache\r\nSet-Cookie: PHPSESSID=vl6re9loeqlon179jjbui0o2e4; path=/; HttpOnly; secure; SameSite=None\r\nExpires: Thu, 19 Nov 1981 08:52:00 GMT\r\n\r\n'
Processing rows:  58%|█████▊    | 122/211 [19:15<18:59, 12.80s/it]전라도_군산시페이지 정보를 추출할 수 없습니다.
Processing rows:  59%|█████▉    | 124/211 [19:20<10:48,  7.46s/it]요청 오류: 400 Client Error: Bad Request for url: https://www.namwon.go.kr/board/post/list.do?boardUid=ff8080818ea1fec5018ea24137680031&menuUid=ff8080818e3beff0018e4077131b007a&beginDateStr=&endDateStr=&searchType=postTtl&keyword=%EC%A0%9C%EC%95%88&paramString=Us7WVBAxc13kgzv1JU3ayAslPphGSM%2FmlfdB4qtWC4OBeJsElaKmGl7kvQ4Au%2B3O&size=10
전라도_남원시페이지 정보를 추출할 수 없습니다.
Processing rows:  60%|█████▉    | 126/211 [20:11<22:20, 15.77s/it]연결 타임아웃: 전라도_전주시 서버로부터 응답이 없습니다.
전라도_전주시페이지 정보를 추출할 수 없습니다.
Processing rows:  61%|██████    | 129/211 [20:50<19:10, 14.03s/it]cleaned_dates 리스트가 비어 있습니다.
Processing rows:  63%|██████▎   | 133/211 [21:45<19:55, 15.33s/it]전라도_임실군페이지 정보를 추출할 수 없습니다.
Processing rows:  66%|██████▋   | 140/211 [23:12<11:43,  9.91s/it]요청 오류: ('Received response with content-encoding: gzip, but failed to decode it.', error('Error -3 while decompressing data: incorrect data check'))
전라도_여수시페이지 정보를 추출할 수 없습니다.
Processing rows:  69%|██████▉   | 146/211 [24:04<09:35,  8.86s/it]요청 오류: ('Received response with content-encoding: gzip, but failed to decode it.', error('Error -3 while decompressing data: incorrect data check'))
전라도_무안군페이지 정보를 추출할 수 없습니다.
Processing rows:  70%|██████▉   | 147/211 [24:14<10:00,  9.38s/it]읽기 타임아웃: 전라도_보성군 서버가 데이터를 제공하는 시간이 초과되었습니다.
전라도_보성군페이지 정보를 추출할 수 없습니다.
Processing rows:  74%|███████▍  | 157/211 [25:17<07:09,  7.95s/it]전라도_화순군페이지 정보를 추출할 수 없습니다.
Processing rows:  77%|███████▋  | 162/211 [25:50<05:09,  6.31s/it]요청 오류: 404 Client Error: Not Found for url: https://www.gbmg.go.kr/portal/saeol/gosi/list.do?mId=0301060000
경상도_문경시페이지 정보를 추출할 수 없습니다.
Processing rows:  79%|███████▊  | 166/211 [26:01<02:23,  3.19s/it]경상도_영천시페이지 정보를 추출할 수 없습니다.
Processing rows:  81%|████████  | 170/211 [26:37<05:05,  7.45s/it]cleaned_dates 리스트가 비어 있습니다.
Processing rows:  81%|████████  | 171/211 [26:49<05:49,  8.73s/it]cleaned_dates 리스트가 비어 있습니다.
Processing rows:  82%|████████▏ | 173/211 [27:03<05:11,  8.21s/it]cleaned_dates 리스트가 비어 있습니다.
Processing rows:  84%|████████▍ | 177/211 [27:51<06:17, 11.09s/it]cleaned_dates 리스트가 비어 있습니다.
Processing rows:  84%|████████▍ | 178/211 [28:04<06:28, 11.76s/it]경상도_청송군페이지 정보를 추출할 수 없습니다.
Processing rows:  91%|█████████▏| 193/211 [28:47<00:57,  3.21s/it]요청 오류: HTTPSConnectionPool(host='www.namhae.go.kr', port=443): Max retries exceeded with url: /modules/saeol/gosi.do?dep_nm=%EB%82%A8%ED%95%B4%EC%9D%8D&pageCd=WW0512010103&siteGubun=portal (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x7cf3b8176020>: Failed to resolve 'www.namhae.go.kr' ([Errno -2] Name or service not known)"))
경상도_남해군_남해읍페이지 정보를 추출할 수 없습니다.
Processing rows: 100%|██████████| 211/211 [29:58<00:00,  8.53s/it]
    """
    

    st.session_state.log_text = log_text
        
    st.text(log_text)

# 메인 실행 흐름
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    st.session_state.update_time = "2024년 10월 27일 22:28 업데이트"  # 원하는 시간으로 변경
    main_app()
