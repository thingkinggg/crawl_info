import streamlit as st

st.title("🎈 지자체 크롤링")
st.write(
    "2024년 9월 23일 17:35 업데이트"
)

import pandas as pd

# CSV 파일에서 데이터 읽기
@st.cache_data
def load_data():
    return pd.read_excel('data.xlsx', engine='openpyxl')

df = load_data()

# 앱 제목
st.title('간단한 검색 앱')

# 검색어 입력
search_term = st.text_input('검색어를 입력하세요:')

# 검색 버튼
if st.button('검색'):
    if search_term:
        # 이름 열에서 검색어를 포함하는 행 찾기
        result = df[df['이름'].str.contains(search_term, case=False)]
        
        if not result.empty:
            st.write('검색 결과:')
            st.dataframe(result)
        else:
            st.write('검색 결과가 없습니다.')
    else:
        st.write('검색어를 입력해주세요.')

# 전체 데이터 표시
st.write('전체 데이터:')
st.dataframe(df)
