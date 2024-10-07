import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

st.title("🎈 지자체 크롤링")
st.write(
    "2024년 10월 7일 14:33 업데이트"
    "작업진행상황 : 92개 site 최신 1page 수집 작업 완료"
    "향후진행상황 : 나머지 site 최신 페이지 수집, 수집실패사이트점검, 2page이상 수집하도록 변경"
)

# 오늘 일자 및 최근 7일 계산
today = datetime.today()
one_week_ago = today - timedelta(days=7)
today_str = today.strftime('%Y%m%d')

# 최근 일주일 내의 파일을 읽어오기 위한 함수
def get_recent_file(file_prefix):
    # 최근 일주일 내의 파일 목록
    files = glob.glob(f"{file_prefix}_*.xlsx")
    recent_files = []
    for file in files:
        # 파일명에서 날짜 추출
        file_date_str = file.split('_')[-1].replace('.xlsx', '')
        try:
            file_date = datetime.strptime(file_date_str, '%Y%m%d')
            if one_week_ago <= file_date <= today:
                recent_files.append(file)
        except ValueError:
            continue
    # 최근 파일 반환 (여러 개일 경우 가장 최신 파일 선택)
    if recent_files:
        return sorted(recent_files, reverse=True)[0]
    return None

# df_log 파일 읽기
df_log_file_path = get_recent_file('df_log')
if df_log_file_path:
    df_log = pd.read_excel(df_log_file_path, engine='openpyxl')
    st.write(f"df_log 파일: {df_log_file_path}에서 데이터를 읽었습니다.")
else:
    st.write("최근 일주일 내에 df_log 파일을 찾을 수 없습니다.")

# df_list 파일 읽기
df_list_file_path = get_recent_file('df_list')
if df_list_file_path:
    df_list = pd.read_excel(df_list_file_path, engine='openpyxl')
    st.write(f"df_list 파일: {df_list_file_path}에서 데이터를 읽었습니다.")
else:
    st.write("최근 일주일 내에 df_list 파일을 찾을 수 없습니다.")

# df_log 파일 처리
if df_log_file_path:
    # unique_date가 null이거나 1이고 max_date가 오늘 일자인 경우 필터링
    today_str = today.strftime('%Y-%m-%d')  # 오늘 일자 문자열 변환
    problematic_rows = df_log[(df_log['unique_date'].isnull() | (df_log['unique_date'] == 1)) & (df_log['max_date'] == today_str)]
    
    # 경고 메시지 표시
    if not problematic_rows.empty:
        st.warning("unique_date가 Null이거나 1인 경우이며, max_date가 오늘인 데이터가 있습니다. 사이트에서 확인해야 합니다.")
        st.write("확인해야 할 데이터:")
        st.dataframe(problematic_rows, use_container_width=True)
    else:
        st.success("unique_date가 Null이거나 1인 데이터가 없습니다.")

    # df_log 전체 데이터 표시
    st.write("df_log 파일의 전체 데이터:")
    st.dataframe(df_log, use_container_width=True)

# df_list 파일 처리 및 검색 기능
if df_list_file_path:
    # 검색 기능 구현
    search_keyword = st.text_input("df_list 파일에서 검색할 키워드를 입력하세요")

    if search_keyword:
        # 검색어를 포함한 행 필터링
        search_results = df_list[df_list['제목'].str.contains(search_keyword, na=False)]
        st.write(f"'{search_keyword}' 검색 결과:")
        st.dataframe(search_results, use_container_width=True)
    else:
        st.write("df_list 파일의 전체 데이터:")
        st.dataframe(df_list, use_container_width=True)

# 중간 일배치 수집 로그 텍스트
st.subheader("일배치 수집 로그")
log_text = """
Processing rows:  16%|█▋        | 15/92 [00:20<01:34,  1.23s/it] 페이지 로딩 시간이 초과되었습니다: 광주도시관리공사
Processing rows:  17%|█▋        | 16/92 [01:31<28:03, 22.16s/it] 광주도시관리공사 페이지 정보를 추출할 수 없습니다.
Processing rows:  28%|██▊       | 26/92 [02:17<07:03,  6.42s/it] 읽기 타임아웃: 서버가 데이터를 제공하는 시간이 초과되었습니다.
강원고시공고 페이지 정보를 추출할 수 없습니다.
Processing rows:  37%|███▋      | 34/92 [02:49<05:48,  6.01s/it] 읽기 타임아웃: 서버가 데이터를 제공하는 시간이 초과되었습니다.
고양특례시고시공고 페이지 정보를 추출할 수 없습니다.
Processing rows:  47%|████▋     | 43/92 [04:11<05:15,  6.43s/it] 광명시 페이지 정보를 추출할 수 없습니다.
Processing rows:  51%|█████     | 47/92 [04:14<01:37,  2.18s/it] 요청 오류: 417 Client Error: Expectation Failed for url: https://www.gimpo.go.kr/portal/ntfcPblancList.do?key=1004&cate_cd=1&searchCnd=40900000000
김포시 페이지 정보를 추출할 수 없습니다.
Processing rows:  66%|██████▋   | 61/92 [05:56<03:33,  6.87s/it] 읽기 타임아웃: 서버가 데이터를 제공하는 시간이 초과되었습니다.
양주시 페이지 정보를 추출할 수 없습니다.
Processing rows:  71%|███████   | 65/92 [06:12<02:10,  4.85s/it] 연결 타임아웃: 서버로부터 응답이 없습니다.
의정부시 페이지 정보를 추출할 수 없습니다.
Processing rows:  95%|█████████▍| 87/92 [09:05<00:49,  9.92s/it] 정선군 페이지 정보를 추출할 수 없습니다.
Processing rows: 100%|██████████| 92/92 [09:29<00:00,  6.19s/it]
"""
st.text(log_text)
