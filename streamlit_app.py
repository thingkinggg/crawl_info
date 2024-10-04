import streamlit as st
import pandas as pd

st.title("🎈 지자체 크롤링")
st.write(
    "2024년 10월 4일 13:40 업데이트"
)


# 파일에서 데이터 읽기
df_log_file = pd.read_excel('df_log.xlsx', engine='openpyxl')
df_fin_file = pd.read_excel('df_list.xlsx', engine='openpyxl')


# df_log 파일 처리
if df_log_file is not None:
    df_log = pd.read_excel(df_log_file)
    
    # unique_date가 Null이거나 1인 경우에 대한 필터링
    problematic_rows = df_log[df_log['unique_date'].isnull() | (df_log['unique_date'] == 1)]
    
    # 경고 메시지 표시
    if not problematic_rows.empty:
        st.warning("unique_date가 Null이거나 1인 경우가 있습니다. 사이트에서 확인해야 합니다.")
        st.write("확인해야 할 데이터:")
        st.dataframe(problematic_rows)
    else:
        st.success("unique_date가 Null이거나 1인 데이터가 없습니다.")

    # df_log 전체 데이터 표시
    st.write("df_log 파일의 전체 데이터:")
    st.dataframe(df_log)

# df_fin 파일 처리
if df_fin_file is not None:
    df_fin = pd.read_excel(df_fin_file)

    # 검색 기능 구현
    search_keyword = st.text_input("df_fin 파일에서 검색할 키워드를 입력하세요")

    if search_keyword:
        # 검색어를 포함한 행 필터링
        search_results = df_fin[df_fin['제목'].str.contains(search_keyword, na=False)]
        st.write(f"'{search_keyword}' 검색 결과:")
        st.dataframe(search_results)
    else:
        st.write("df_fin 파일의 전체 데이터:")
        st.dataframe(df_fin)
