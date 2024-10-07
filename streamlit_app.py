import streamlit as st
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

st.title("🎈 지자체 크롤링")
st.write("2024년 10월 7일 23:58 업데이트\n")
st.write("작업진행상황 : 93개 site 최신 1page 수집 작업 완료\n")
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
        # 파일명에서 날짜 추출
        file_date_str = file.split('_')[-1].replace('.xlsx', '')
        try:
            file_date = datetime.strptime(file_date_str, '%Y%m%d')
            if one_week_ago <= file_date <= today:
                recent_files.append(file)
        except ValueError:
            continue
    # 최근 2개의 파일 반환 (최신 파일 순으로 정렬)
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
        # 파일명에서 날짜 추출
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
    st.write(f"최근 df_log 파일: {recent_file_path}에서 데이터를 읽었습니다.")
else:
    st.write("최근 일주일 내에 df_log 파일을 찾을 수 없습니다.")

# 이전 파일 처리
if previous_file_path:
    df_log_previous = pd.read_excel(previous_file_path, engine='openpyxl')
    st.write(f"이전 df_log 파일: {previous_file_path}에서 데이터를 읽었습니다.")
else:
    st.write("이전 df_log 파일을 찾을 수 없습니다.")

# df_log 파일 처리
if recent_file_path and previous_file_path:
    # 파일들을 left join하여 비교 (필요한 컬럼만 처리)
    merge_columns = ['URL', 'unique_date', 'max_date']  # 비교하고자 하는 컬럼들만 명시
    df_merged = pd.merge(df_log_recent, 
                         df_log_previous[merge_columns], 
                         on='URL', 
                         suffixes=('_recent', '_previous'), 
                         how='left')
    
    # 변경된 값 비교
    st.write("최근 파일과 이전 파일을 left join한 데이터:")
    st.dataframe(df_merged, use_container_width=True)

    # unique_date가 null이거나 1이고 max_date가 오늘 일자인 경우 필터링
    today_str = today.strftime('%Y-%m-%d')  # 오늘 일자 문자열 변환
    problematic_rows = df_merged[(df_merged['unique_date_recent'].isnull()) | ((df_merged['unique_date_recent'] == 1) & (df_merged['max_date_recent'] == today_str))]
    
    # 경고 메시지 표시
    if not problematic_rows.empty:
        st.warning(f"unique_date가 Null이거나 1인 경우이며, max_date가 오늘인 데이터가 {len(problematic_rows)}건 있습니다. 사이트에서 확인해야 합니다.")
        st.write("확인해야 할 데이터:")
        st.dataframe(problematic_rows, use_container_width=True)
    else:
        st.success("unique_date가 Null이거나 1인 데이터가 없습니다.")

else:
    st.write("비교를 위해 이전 파일과 최근 파일이 모두 필요합니다.")


# df_list 파일 읽기
df_list_file_paths = get_recent_files('df_list')
if df_list_file_paths:
    combined_df_list = pd.DataFrame()  # 빈 데이터프레임 생성
    
    for file_path in df_list_file_paths:
        df = pd.read_excel(file_path, engine='openpyxl')
        combined_df_list = pd.concat([combined_df_list, df], ignore_index=True)
    
    # 중복 제거
    combined_df_list = combined_df_list.drop_duplicates()
    
    st.write(f"최근 일주일 내에 df_list 파일 {len(df_list_file_paths)}개를 불러왔습니다.")
    st.write("중복이 제거된 df_list 데이터:")
    st.dataframe(combined_df_list, use_container_width=True)
    
    # 검색 기능 구현
    search_keyword = st.text_input("df_list 파일에서 검색할 키워드를 입력하세요")

    if search_keyword:
        # 검색어를 포함한 행 필터링
        search_results = combined_df_list[combined_df_list['제목'].str.contains(search_keyword, na=False)]
        st.write(f"'{search_keyword}' 검색 결과:")
        st.dataframe(search_results, use_container_width=True)
    else:
        st.write("df_list 파일의 전체 데이터:")
        st.dataframe(combined_df_list, use_container_width=True)
else:
    st.write("최근 일주일 내에 df_list 파일을 찾을 수 없습니다.")

# 중간 일배치 수집 로그 텍스트
st.subheader("일배치 수집 로그")
log_text = """
Processing rows:  46%|████▌     | 43/93 [04:25<06:27,  7.76s/it]경기도_광명시페이지 정보를 추출할 수 없습니다.
Processing rows:  51%|█████     | 47/93 [04:32<02:26,  3.18s/it]요청 오류: 417 Client Error: Expectation Failed for url: https://www.gimpo.go.kr/portal/ntfcPblancList.do?key=1004&cate_cd=1&searchCnd=40900000000
경기도_김포시페이지 정보를 추출할 수 없습니다.
Processing rows:  94%|█████████▎| 87/93 [10:45<01:14, 12.46s/it]강원도_정선군페이지 정보를 추출할 수 없습니다.
Processing rows:  97%|█████████▋| 90/93 [11:02<00:25,  8.54s/it]읽기 타임아웃: 강원도_홍천군 서버가 데이터를 제공하는 시간이 초과되었습니다.
강원도_홍천군페이지 정보를 추출할 수 없습니다.
Processing rows: 100%|██████████| 93/93 [11:25<00:00,  7.37s/it]
"""
st.text(log_text)
