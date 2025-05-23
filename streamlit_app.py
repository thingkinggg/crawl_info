import streamlit as st
import pandas as pd
import glob
import os
import webbrowser
from datetime import datetime, timedelta
from io import BytesIO
import html

st.set_page_config(layout="wide")


PASSWORD = "yc0943312***"

def login():
    st.title(" 🎈 지자체 크롤링 로그인 ")
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
    
    st.write("문의 있으실 경우 deepbid2024@gmail.com 으로 연락부탁드립니다.")
  
    
    # 버튼 클릭 시 Google 스프레드시트로 이동
    st.markdown(
    """
    <a href="https://docs.google.com/spreadsheets/d/1t7rp43AJtoGFSpPwUPAkNBduUqwbl6zddsVv_TJPGdM/edit?usp=sharing" 
    target="_blank" style="text-decoration: none;">
        <button style="display: inline-block; padding: 10px 20px; font-size: 16px; color: white; background-color: #4CAF50; border: none; border-radius: 5px; cursor: pointer;">
            진행현황 확인하기 🚀
        </button>
    </a>
    """,
    unsafe_allow_html=True
)
    
    # 오늘 일자 및 최근 15일 계산
    today = datetime.today()
    one_week_ago = today - timedelta(days=16)
    today_str = today.strftime('%Y%m%d')
    
   # 특정 접두사를 가지는 최근 파일들을 반환하는 함수
    def get_recent_files_by_date(file_prefix):
        files = glob.glob(f"{file_prefix}_*.xlsx")
        file_dates = []
        for file in files:
            file_date_str = file.split('_')[-1].replace('.xlsx', '')
            try:
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                if one_week_ago <= file_date :
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
                if one_week_ago <= file_date :
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
                combined_df_log = pd.concat([combined_df_log, df], ignore_index=True)
            
            # max_date를 YYYY-MM-DD 형식으로 변경
            if 'max_date' in combined_df_log.columns:
                combined_df_log['max_date'] = pd.to_datetime(combined_df_log['max_date'], errors='coerce').dt.date.astype(str)
            
            # Check problematic rows
            problematic_rows = combined_df_log[
                (combined_df_log['unique_date'].isnull()) | (combined_df_log['unique_date'] == 1) | (combined_df_log['unique_date'] == 0)
            ]
            
            if not problematic_rows.empty:
                st.warning(f"선택한 날짜({selected_date})에 덜 수집된 사이트 리스트는 아래와 같습니다. 직접 접속 후 확인 필요합니다.")
                st.write("   전라도 강진군 1/15 사이트 접속 불가 16일 재수집예정")
                
                # Replace the "URL" column with "확인하기" buttons
                problematic_rows = problematic_rows.copy()
                problematic_rows['URL'] = problematic_rows['URL'].apply(
                    lambda x: f'<a href="{html.escape(x)}" target="_blank"><button>확인하기</button></a>' if pd.notna(x) else ''
                )
                
                # Render the DataFrame as HTML
                st.markdown(problematic_rows.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            else:
                st.success(f"  선택한 날짜({selected_date})에는 모든 데이터를 수집했습니다.  ")
        else:
            st.write(f"선택한 날짜({selected_date})에 해당하는 df_log 파일을 찾을 수 없습니다.")
    else:
        st.write("최근 15일 내에 df_log 파일을 찾을 수 없습니다.")
    
    # df_list 파일 읽기 및 처리
    df_list_file_paths = get_recent_files('df_list')
    
    if df_list_file_paths:
        combined_df_list = pd.DataFrame()
        
        for file_path in df_list_file_paths:
            df = pd.read_excel(file_path, engine='openpyxl')
            combined_df_list = pd.concat([combined_df_list, df], ignore_index=True)

        combined_df_list = combined_df_list.dropna(subset=['작성일', '수집일'])
        
        combined_df_list['작성일'] = pd.to_datetime(combined_df_list['작성일'], errors='coerce')
        # '수집일' 컬럼 포맷 변경
        combined_df_list['수집일'] = pd.to_datetime(combined_df_list['수집일'], errors='coerce')
       
        # 중복 제거: 동일한 ('SITE_NO', '출처', '제목', 'URL', '작성일') 조합에서 '수집일'이 가장 작은 행만 남김
        combined_df_list = combined_df_list.loc[
            combined_df_list.groupby(['SITE_NO', '출처', '제목', '작성일'])['수집일'].idxmin()
            ]
        
        # 데이터 정렬: '수집일' 내림차순, '작성일' 내림차순, 'SITE_NO' 오름차순, '제목' 오름차순
        combined_df_list = combined_df_list.sort_values(
            by=['수집일', '작성일', 'SITE_NO', '제목'],
            ascending=[False, False, True, True]
        )

        # 컬럼 순서 재정렬
        column_order = ['SITE_NO', '출처', '제목', 'URL', '작성일', '수집일']
        combined_df_list = combined_df_list.reindex(columns=column_order)

        # 최근 업데이트 일시 확인
        most_recent_date = combined_df_list['수집일'].max()
        if pd.notnull(most_recent_date):
            recent_update = most_recent_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            recent_update = "N/A"

        combined_df_list['수집일'] = combined_df_list['수집일'].dt.strftime('%Y-%m-%d %H:%M:%S')

                # General CSS styling for the top table
        st.markdown("""
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th {
                    text-align: center;  /* Center-align the headers */
                    background-color: #f2f2f2;  /* Light gray background for headers */
                    padding: 8px;
                }
                td {
                    padding: 8px;
                    text-align: left;  /* Align text to the left in table cells */
                    max-width: 200px;  /* Adjust max-width to better fit content */
                    word-wrap: break-word;  /* Enable word wrap for long text */
                }
                a {
                    color: #0066cc;  /* Link color */
                    text-decoration: none;  /* Remove underline from links */
                }
                a:hover {
                    text-decoration: underline;  /* Underline on hover */
                }
                button {
                    font-size: 12px;
                    padding: 5px 10px;
                }
                .lower-table td:nth-child(1) {
                    max-width: 50px;  /* Reduce the width of the 2nd column */
                }                
                .lower-table td:nth-child(2) {
                    max-width: 100px;  /* Reduce the width of the 2nd column */
                }
                .lower-table td:nth-child(3) {
                    max-width: 300px;  /* Increase the width of the 3rd column */
                }
                .lower-table td:nth-child(4) {
                    max-width: 50px;  /* Increase the width of the 3rd column */
                }
                .lower-table td:nth-child(5) {
                    max-width: 50px;  /* Increase the width of the 3rd column */
                }
            </style>
        """, unsafe_allow_html=True)
    

        st.write(f"최근 15일 내에 수집된 공고 파일 {len(df_list_file_paths)}개를 불러왔습니다.")
        st.write("포함 키워드 : 특허, 제안, 심의, 공법")
        st.write(f"📅 **최근 업데이트 일시**: {recent_update}")

        # 엑셀 파일 다운로드 버튼 추가
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            combined_df_list.to_excel(writer, index=False, sheet_name='df_list_data')
            writer.close()  # save() 대신 close()를 사용합니다.
            processed_data = output.getvalue()
        st.download_button(
            label="📥 공고 파일 엑셀 다운로드",
            data=processed_data,
            file_name=f"recent_df_list_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        search_keyword = st.text_input("수집된 공고 제목에서 검색할 키워드를 입력하세요")
    
        if search_keyword:
            search_results = combined_df_list[combined_df_list['제목'].str.contains(search_keyword, na=False)]
            st.write(f"'{search_keyword}' 검색 결과:")
            search_results = search_results.copy()
            search_results['URL'] = search_results['URL'].apply(
                lambda x: f'<a href="{html.escape(x)}" target="_blank"><button>확인하기</button></a>' if pd.notna(x) else ''
            )
            st.markdown(f'<div class="lower-table">{search_results.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
        else:
            st.write("df_list 파일의 전체 데이터:")
            # Replace the "URL" column with "확인하기" buttons
            combined_df_list = combined_df_list.copy()
            combined_df_list['URL'] = combined_df_list['URL'].apply(
                lambda x: f'<a href="{html.escape(x)}" target="_blank"><button>확인하기</button></a>' if pd.notna(x) else ''
            )
            
            # Render the DataFrame as HTML
            st.markdown(f'<div class="lower-table">{combined_df_list.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
      

    else:
        st.write("최근 15일 내에 df_list 파일을 찾을 수 없습니다.")
    


# 메인 실행 흐름
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_app()
else:
    login()
