import streamlit as st
import pandas as pd
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# 데이터 파일 경로
DATA_FILE = 'leaderboard.csv'

# 전역 변수
DEFAULT_TITLE = "GCK Lap time board"
COLUMN_NAMES = ["이름", "차수", "시간 (ms)"]

# 한글 폰트 등록
pdfmetrics.registerFont(TTFont('NotoSans', 'NotoSansKR-Regular.ttf'))

# 초기화
if 'title' not in st.session_state:
    st.session_state.title = DEFAULT_TITLE
if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = pd.DataFrame(columns=COLUMN_NAMES)
if 'admin' not in st.session_state:
    st.session_state.admin = False
if 'show_admin' not in st.session_state:  # show_admin 초기화
    st.session_state.show_admin = False

# CSV 파일 존재 확인 및 로드
def load_data():
    if os.path.exists(DATA_FILE):
        if os.path.getsize(DATA_FILE) > 0:
            st.session_state.leaderboard = pd.read_csv(DATA_FILE, encoding='utf-8')
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("타이틀,"):
                        st.session_state.title = line.strip().split(",")[1]
                        break
        else:
            st.session_state.leaderboard = pd.DataFrame(columns=COLUMN_NAMES)
    else:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            f.write(f"타이틀,{DEFAULT_TITLE}\n")

load_data()

# 관리자 기능을 숨기기 위한 버튼
if st.button("관리자 기능"):
    st.session_state.show_admin = not st.session_state.show_admin
    
if st.session_state.show_admin:
    st.subheader("관리자 기능")
    admin_password = st.text_input("관리자 비밀번호", type="password", key="admin_pass")
    is_admin = st.button("관리자 로그인")

    if is_admin:
        if admin_password == "gck@admin":
            st.session_state.admin = True
        elif admin_password == "":
            st.warning("비밀번호를 입력하세요.")
        else:
            st.warning("잘못된 비밀번호입니다.")

    if st.session_state.admin:
        new_title = st.text_input("리더보드 제목", st.session_state.title)

        if st.button("타이틀 변경"):
            st.session_state.title = new_title
            # 파일 업데이트
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.startswith("타이틀,"):
                        f.write(f"타이틀,{new_title}\n")
                    else:
                        f.write(line)
            st.success("타이틀이 변경되었습니다.")
            load_data()  # 데이터 다시 로드하여 UI 갱신

        # 삭제할 데이터의 순번을 입력
        if len(st.session_state.leaderboard) > 0:
            delete_index = st.number_input("삭제할 데이터의 순위", min_value=1, max_value=len(st.session_state.leaderboard), step=1)
            if st.button("해당 데이터 삭제"):
                if delete_index > 0 and delete_index <= len(st.session_state.leaderboard):
                    st.session_state.leaderboard = st.session_state.leaderboard.drop(delete_index - 1).reset_index(drop=True)
                    st.session_state.leaderboard.to_csv(DATA_FILE, index=False, encoding='utf-8')
                    st.success("데이터가 삭제되었습니다.")
                else:
                    st.warning("유효한 순번을 입력하세요.")

        if st.button("리더보드 초기화"):
            st.session_state.leaderboard = pd.DataFrame(columns=COLUMN_NAMES)
            st.session_state.title = DEFAULT_TITLE  # 타이틀 초기화
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                f.write(f"타이틀,{st.session_state.title}\n")
            st.success("리더보드가 초기화되었습니다.")

        if st.button("리더보드 갱신"):
            load_data()
            st.success("리더보드가 갱신되었습니다.")

st.title(st.session_state.title)

# 입력폼
with st.form(key='input_form'):
    name = st.text_input("이름")
    lap_number = st.number_input("주행 차수", min_value=1)
    minutes = st.number_input("분", min_value=0)
    seconds = st.number_input("초", min_value=0, max_value=59)
    milliseconds = st.number_input("밀리초", min_value=0, max_value=999)

    total_time = (minutes * 60 + seconds) * 1000 + milliseconds
    submit_button = st.form_submit_button(label='제출')

# 제출 시 데이터 업데이트
if submit_button and name:
    if not st.session_state.leaderboard.empty:
        if ((st.session_state.leaderboard['이름'] == name) & (st.session_state.leaderboard['차수'] == lap_number)).any():
            st.warning("이미 존재하는 이름과 주행 차수입니다. 다른 값을 입력하세요.")
        else:
            new_entry = pd.DataFrame([[name, lap_number, total_time]], columns=COLUMN_NAMES)
            st.session_state.leaderboard = pd.concat([st.session_state.leaderboard, new_entry], ignore_index=True)
            st.session_state.leaderboard = st.session_state.leaderboard.sort_values(by="시간 (ms)").reset_index(drop=True)
            st.session_state.leaderboard.to_csv(DATA_FILE, index=False, encoding='utf-8')
    else:
        new_entry = pd.DataFrame([[name, lap_number, total_time]], columns=COLUMN_NAMES)
        st.session_state.leaderboard = new_entry
        st.session_state.leaderboard.to_csv(DATA_FILE, index=False, encoding='utf-8')

# 시간을 분:초:밀리초 형식으로 변환하는 함수
def format_time(ms):
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    milliseconds = ms % 1000
    return f"{minutes}:{seconds:02}:{milliseconds // 10:02}"

# 리더보드 표시
st.subheader("리더보드")
if not st.session_state.leaderboard.empty:
    display_data = st.session_state.leaderboard.copy()
    display_data["시간"] = display_data["시간 (ms)"].apply(format_time)
    display_data["순위"] = display_data.index + 1  # '순번'을 '순위'로 변경
    display_data = display_data[["순위", "이름", "차수", "시간"]]  # 순위로 변경
    st.table(display_data)

# 다운로드 기능
st.markdown("---")  # 구분선 추가
st.subheader("다운로드 기능")

# CSV 다운로드 기능
if st.button("리더보드 CSV 다운로드"):
    if not st.session_state.leaderboard.empty:
        csv = st.session_state.leaderboard.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, file_name=f"{st.session_state.title}.csv", mime='text/csv')
    else:
        st.warning("리더보드에 데이터가 없습니다.")

# HTML 다운로드 기능
if st.button("리더보드 HTML 다운로드"):
    if not st.session_state.leaderboard.empty:
        html = display_data.to_html(index=False, escape=False)
        st.download_button("Download HTML", html, file_name=f"{st.session_state.title}.html", mime='text/html')
    else:
        st.warning("리더보드에 데이터가 없습니다.")

# PDF 다운로드 기능
def create_pdf(dataframe):
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)

    data = [["순위", "이름", "차수", "시간"]] + dataframe.values.tolist()  # '순번'을 '순위'로 변경
    table = Table(data)
    
    # 테이블 스타일 적용
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'NotoSans'),  # 한글 폰트 적용
    ]))

    pdf.build([table])
    buffer.seek(0)
    return buffer

if st.button("리더보드 PDF 다운로드"):
    if not st.session_state.leaderboard.empty:
        pdf_buffer = create_pdf(display_data)
        st.download_button("Download PDF", pdf_buffer, file_name=f"{st.session_state.title}.pdf", mime='application/pdf')
    else:
        st.warning("리더보드에 데이터가 없습니다.")

# Markdown 다운로드 기능
if st.button("리더보드 Markdown 다운로드"):
    if not st.session_state.leaderboard.empty:
        markdown = display_data.to_markdown(index=False)
        st.download_button("Download Markdown", markdown, file_name=f"{st.session_state.title}.md", mime='text/markdown')
    else:
        st.warning("리더보드에 데이터가 없습니다.")
