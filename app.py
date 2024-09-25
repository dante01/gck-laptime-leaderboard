import streamlit as st
import pandas as pd
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import ParagraphStyle

# 파일 경로
DATA_FILE = 'leaderboard.csv'
TITLE_FILE = 'title.txt'
BACKUP_FILE = 'leaderboard_backup.csv'

# 전역 변수
DEFAULT_TITLE = "GCK Lap time board"
KEY_NAME = "이름"
KEY_LAP_NUMBER = "주행 차수"
KEY_LAP_TIME = "시간"
KEY_BONUS_TIME = "가산초"
KEY_PENALTY_TIME = "패널티초"
KEY_TOTAL_TIME = "합계 시간"
KEY_RANKING = "순위"
KEY_MM = "분"
KEY_SS = "초"
KEY_MS = "밀리초"
COLUMN_NAMES = [KEY_NAME, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_BONUS_TIME, KEY_PENALTY_TIME, KEY_TOTAL_TIME]
ADMIN_PASSWORD = "gck@admin" #os.getenv("ADMIN_PASSWORD")  # 환경 변수로부터 비밀번호 불러오기

# 한글 폰트 등록
pdfmetrics.registerFont(TTFont('NotoSansKR', 'NotoSansKR-Regular.ttf'))

# 초기화
if 'title' not in st.session_state:
    if os.path.exists(TITLE_FILE):
        with open(TITLE_FILE, 'r', encoding='utf-8') as f:
            st.session_state.title = f.read().strip()
    else:
        st.session_state.title = DEFAULT_TITLE
if 'leaderboard' not in st.session_state:
    st.session_state.leaderboard = pd.DataFrame(columns=COLUMN_NAMES)
if 'admin' not in st.session_state:
    st.session_state.admin = False
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False

# CSV 파일 존재 확인 및 로드
def load_data():
    if os.path.exists(DATA_FILE):
        if os.path.getsize(DATA_FILE) > 0:
            st.session_state.leaderboard = pd.read_csv(DATA_FILE, encoding='utf-8')
        else:
            st.session_state.leaderboard = pd.DataFrame(columns=COLUMN_NAMES)
    else:
        st.session_state.leaderboard = pd.DataFrame(columns=COLUMN_NAMES)

load_data()

# 관리자 기능을 숨기기 위한 버튼
if st.button("관리자 기능"):
    st.session_state.show_admin = not st.session_state.show_admin

if st.session_state.show_admin:
    st.subheader("관리자 기능")
    admin_password = st.text_input("관리자 비밀번호", type="password", key="admin_pass")
    is_admin = st.button("관리자 로그인")

    if is_admin:
        if admin_password == ADMIN_PASSWORD:
            st.session_state.admin = True
        elif admin_password == "":
            st.warning("비밀번호를 입력하세요.")
        else:
            st.warning("잘못된 비밀번호입니다.")

    if st.session_state.admin:
        new_title = st.text_input("리더보드 제목", st.session_state.title)

        if st.button("타이틀 변경"):
            st.session_state.title = new_title
            with open(TITLE_FILE, 'w', encoding='utf-8') as f:
                f.write(new_title)
            st.success("타이틀이 변경되었습니다.")

        # 데이터 삭제 및 초기화
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
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)  # 데이터 파일 삭제
            if os.path.exists(BACKUP_FILE):
                os.remove(BACKUP_FILE)  # 백업 파일 삭제
            st.session_state.title = DEFAULT_TITLE
            with open(TITLE_FILE, 'w', encoding='utf-8') as f:
                f.write(st.session_state.title)
            st.success("리더보드가 초기화되었습니다.")

        if st.button("리더보드 갱신"):
            load_data()
            st.success("리더보드가 갱신되었습니다.")

        # 파일 업로드 기능
        uploaded_file = st.file_uploader("리더보드 CSV 파일 업로드")
        if uploaded_file:
            st.session_state.leaderboard = pd.read_csv(uploaded_file, encoding='utf-8')
            st.session_state.leaderboard.to_csv(DATA_FILE, index=False, encoding='utf-8')
            st.success("리더보드가 갱신되었습니다.")

        # 리더보드 백업 저장 기능
        if st.button("리더보드 백업 저장"):
            st.session_state.leaderboard.to_csv(BACKUP_FILE, index=False, encoding='utf-8')
            st.success("리더보드 백업이 저장되었습니다.")

        # 백업 파일 다운로드 기능
        if st.button("리더보드 백업 다운로드"):
            if os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE, 'rb') as f:
                    st.download_button("Download Backup", f, file_name='leaderboard_backup.csv', mime='text/csv')
            else:
                st.warning("백업 파일이 존재하지 않습니다.")

st.title(st.session_state.title)

# 입력폼
col1, col2 = st.columns(2)
with col1:
    name = st.text_input(KEY_NAME, placeholder="경주자의 이름을 입력하세요.")
with col2:
    lap_number = st.number_input(KEY_LAP_NUMBER, value=None, min_value=1, placeholder="주행 차수를 입력하세요.")

# 분, 초, 밀리초 입력폼
col3, col4, col5 = st.columns(3)
with col3:
    minutes = st.number_input(KEY_MM, value=None, min_value=0, max_value=999, placeholder="분을 입력하세요.(기본값 0)")
with col4:
    seconds = st.number_input(KEY_SS, value=None, min_value=0, max_value=59, placeholder="초를 입력하세요.")
with col5:
    milliseconds = st.number_input(KEY_MS, value=None, min_value=0, max_value=999, placeholder="밀리초를 입력하세요.")

# 가산초 및 패널티초 입력폼
col6, col7 = st.columns(2)
with col6:
    bonus_time = st.number_input(KEY_BONUS_TIME, value=None, min_value=0, max_value=999, placeholder="가산 시간을 입력하세요.")
with col7:
    penalty_time = st.number_input(KEY_PENALTY_TIME, value=None, min_value=0, max_value=999, placeholder="패널티 시간을 입력하세요.")

# value가 None일 경우 대응
lap_number = 1 if lap_number is None else lap_number
minutes = 0 if minutes is None else minutes
seconds = 0 if seconds is None else seconds
milliseconds = 0 if milliseconds is None else milliseconds
bonus_time = 0 if bonus_time is None else bonus_time
penalty_time = 0 if penalty_time is None else penalty_time

# 합계 시간 계산
input_time = (minutes * 60 + seconds) * 1000 + milliseconds
total_time = input_time + (bonus_time * 1000) + (penalty_time * 1000)

# 시간을 분:초:밀리초 형식으로 변환하는 함수
def format_time(ms):
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    milliseconds = ms % 1000
    return f"{minutes}:{seconds:02}:{milliseconds:03}"

formatted_time = format_time(input_time)
formatted_total_time = format_time(total_time)
submit_button = st.button(label='제출')

# 제출 시 데이터 업데이트
if submit_button and name:
    if not st.session_state.leaderboard.empty:
        if ((st.session_state.leaderboard[KEY_NAME] == name) & (st.session_state.leaderboard[KEY_LAP_NUMBER] == lap_number)).any():
            st.warning("이미 존재하는 이름과 주행 차수입니다. 다른 값을 입력하세요.")
        else:
            new_entry = pd.DataFrame([[name, lap_number, formatted_time, bonus_time, penalty_time, formatted_total_time]], columns=COLUMN_NAMES)
            st.session_state.leaderboard = pd.concat([st.session_state.leaderboard, new_entry], ignore_index=True)
    else:
        new_entry = pd.DataFrame([[name, lap_number, formatted_time, bonus_time, penalty_time, formatted_total_time]], columns=COLUMN_NAMES)
        st.session_state.leaderboard = new_entry

    st.session_state.leaderboard = st.session_state.leaderboard.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)
    st.session_state.leaderboard.to_csv(DATA_FILE, index=False, encoding='utf-8')

# 리더보드 표시
st.subheader("리더보드")
if not st.session_state.leaderboard.empty:
    display_data = st.session_state.leaderboard.copy()
    display_data[KEY_RANKING] = display_data.index + 1
    st.table(display_data[[KEY_RANKING, KEY_NAME, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_BONUS_TIME, KEY_PENALTY_TIME, KEY_TOTAL_TIME]])

# 다운로드 기능
st.markdown("---")
st.subheader("다운로드 기능")

if st.button("리더보드 CSV 다운로드"):
    if not st.session_state.leaderboard.empty:
        display_data = st.session_state.leaderboard.copy()
        display_data[KEY_RANKING] = display_data.index + 1
        csv = display_data.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("Download CSV", csv, file_name=f"{st.session_state.title}.csv", mime='text/csv')
    else:
        st.warning("리더보드에 데이터가 없습니다.")

if st.button("리더보드 HTML 다운로드"):
    if not st.session_state.leaderboard.empty:
        display_data = st.session_state.leaderboard.copy()
        display_data[KEY_RANKING] = display_data.index + 1
        html = display_data.to_html(index=False, escape=False)
        html_with_title = f"<h1 style='text-align: center;'>{st.session_state.title}</h1>\n" + html
        st.download_button("Download HTML", html_with_title.encode('utf-8'), file_name=f"{st.session_state.title}.html", mime='text/html')
    else:
        st.warning("리더보드에 데이터가 없습니다.")

# PDF 생성 기능
def create_pdf(dataframe):
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    title_style = ParagraphStyle(name='TitleStyle', fontName='NotoSansKR', fontSize=20, alignment=1)
    header_style = ParagraphStyle(name='HeaderStyle', fontName='NotoSansKR', fontSize=16, alignment=1)
    cell_style = ParagraphStyle(name='CellStyle', fontName='NotoSansKR', fontSize=12)

    elements = []
    elements.append(Paragraph(st.session_state.title, title_style))
    elements.append(Spacer(1, 12))

    data = [[Paragraph(KEY_RANKING, header_style), Paragraph(KEY_NAME, header_style), Paragraph(KEY_LAP_NUMBER, header_style),
             Paragraph(KEY_LAP_TIME, header_style), Paragraph(KEY_BONUS_TIME, header_style), Paragraph(KEY_PENALTY_TIME, header_style), Paragraph(KEY_TOTAL_TIME, header_style)]]

    for i, row in dataframe.iterrows():
        data.append([Paragraph(str(i + 1), cell_style), Paragraph(row[KEY_NAME], cell_style), Paragraph(str(row[KEY_LAP_NUMBER]), cell_style),
                     Paragraph(format_time(row[KEY_LAP_TIME]), cell_style), Paragraph(str(row[KEY_BONUS_TIME]), cell_style),
                     Paragraph(str(row[KEY_PENALTY_TIME]), cell_style), Paragraph(format_time(row[KEY_TOTAL_TIME]), cell_style)])

    table = Table(data, colWidths=[40, 80, 50, 100, 50, 50, 100])
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'NotoSansKR'),
                               ('FONTSIZE', (0, 0), (-1, -1), 12),
                               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                               ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    elements.append(table)
    pdf.build(elements)
    buffer.seek(0)
    return buffer

if st.button("리더보드 PDF 다운로드"):
    if not st.session_state.leaderboard.empty:
        pdf_buffer = create_pdf(st.session_state.leaderboard)
        st.download_button("Download PDF", pdf_buffer, file_name=f"{st.session_state.title}.pdf", mime='application/pdf')
    else:
        st.warning("리더보드에 데이터가 없습니다.")

# Markdown 저장 기능
if st.button("리더보드 Markdown 다운로드"):
    if not st.session_state.leaderboard.empty:
        display_data = st.session_state.leaderboard.copy()
        display_data[KEY_RANKING] = display_data.index + 1
        markdown = display_data.to_markdown(index=False)
        st.download_button("Download Markdown", markdown.encode('utf-8'), file_name=f"{st.session_state.title}.md", mime='text/markdown')
    else:
        st.warning("리더보드에 데이터가 없습니다.")
