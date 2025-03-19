import time
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
BONUS_TIME_FILE = 'bonus_times.csv'

# 전역 변수
DEFAULT_TITLE = "GCK Lap time board"
KEY_NAME = "이름"
KEY_LAP_NUMBER = "주행 차수"
KEY_LAP_TIME = "시간"
KEY_BONUS_TIME = "가산초"
KEY_PENALTY_TIME = "패널티초"
KEY_TOTAL_TIME = "합계 시간"
KEY_TOTAL_TIME_MS = "합계 시간(ms)"
KEY_DIFF_TIME = "시간 차이"
KEY_RANKING = "순위"
KEY_MM = "분"
KEY_SS = "초"
KEY_MS = "밀리초"
# COLUMN_NAMES = [KEY_NAME, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_BONUS_TIME, KEY_PENALTY_TIME, KEY_TOTAL_TIME, KEY_DIFF_TIME]
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

# 시간을 분:초:밀리초 형식으로 밀리초로 변환하는 함수
def time_str_to_ms(time_str):
    minutes, seconds, milliseconds = map(int, time_str.split(':'))
    return (minutes * 60 + seconds) * 1000 + milliseconds

# 시간을 분:초:밀리초 형식으로 변환하는 함수
def format_time(ms):
    try:
        ms = int(ms)  # 먼저 ms를 정수형으로 변환
        total_seconds = ms // 1000
        minutes, seconds = divmod(total_seconds, 60)
        milliseconds = ms % 1000
        return f"{int(minutes)}:{int(seconds):02}:{int(milliseconds):03}"
    except ValueError:
        return "Invalid time format"

def time_to_ms(time_str):
    minutes, seconds, milliseconds = map(int, time_str.split(":"))
    return (minutes * 60 + seconds) * 1000 + milliseconds

# 시간 차이를 계산하는 함수
def calculate_time_difference(df):
    differences = []
    total_times_ms = df[KEY_TOTAL_TIME].apply(time_str_to_ms)  # 총 시간을 밀리초로 변환

    for i in range(len(df)):
        if i == 0:
            differences.append("0:00:000")  # 첫 번째는 비교 대상이 없으므로 0으로 표시
        else:
            diff = total_times_ms.iloc[i] - total_times_ms.iloc[i - 1]  # 밀리초로 차이 계산
            differences.append(format_time(diff))  # 밀리초를 포맷하여 추가
    return differences

# 자동 가산초 입력 파일 불러오기
def load_bonus_times():
    if os.path.exists(BONUS_TIME_FILE):
        try:
            if os.path.getsize(BONUS_TIME_FILE) > 0:
                st.session_state.bonus_times = pd.read_csv(BONUS_TIME_FILE, encoding='utf-8')
            else:
                st.session_state.bonus_times = pd.DataFrame(columns=[KEY_NAME, KEY_BONUS_TIME])
        except Exception as e:
            st.error(f"가산초 데이터 로드 중 오류가 발생했습니다: {e}")
    else:
        st.session_state.bonus_times = pd.DataFrame(columns=[KEY_NAME, KEY_BONUS_TIME])

# CSV 파일 존재 확인 및 로드
def load_data():
    if os.path.exists(DATA_FILE):
        if os.path.getsize(DATA_FILE) > 0:
            st.session_state.leaderboard = pd.read_csv(DATA_FILE, encoding='utf-8')
        else:
            st.session_state.leaderboard = pd.DataFrame(columns=COLUMN_NAMES)
    else:
        st.session_state.leaderboard = pd.DataFrame(columns=COLUMN_NAMES)

    import pdb
    for i, row in st.session_state.leaderboard.iterrows():
        name = row[KEY_NAME]
        laptime = row[KEY_LAP_TIME]
        bonus = row[KEY_BONUS_TIME]
        penalty = row[KEY_PENALTY_TIME]

        if name in st.session_state.bonus_times[KEY_NAME].values:
            bonus = st.session_state.bonus_times.loc[st.session_state.bonus_times[KEY_NAME] == name, KEY_BONUS_TIME].values[0]
            st.session_state.leaderboard.at[i, KEY_BONUS_TIME] = bonus

        total_ms = time_str_to_ms(laptime) + (bonus * 1000) + (penalty * 1000)
        st.session_state.leaderboard.at[i, KEY_TOTAL_TIME] = format_time(total_ms)

load_bonus_times()  # 가산초 데이터 로드
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
        if uploaded_file is not None:
            try:
                st.session_state.leaderboard = pd.read_csv(uploaded_file, encoding='utf-8')
                st.session_state.leaderboard.to_csv(DATA_FILE, index=False, encoding='utf-8')
                st.success("리더보드가 갱신되었습니다.")
            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

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
    name = st.text_input(KEY_NAME, placeholder="선수의 이름을 입력하세요.")
with col2:
    lap_number = st.number_input(KEY_LAP_NUMBER, value=None, min_value=1, placeholder="1~ (기본값 1)")

# 분, 초, 밀리초 입력폼
col3, col4, col5 = st.columns(3)
with col3:
    minutes = st.number_input(KEY_MM, value=None, min_value=0, max_value=999, placeholder="0~999 min. (기본값 0)")
with col4:
    seconds = st.number_input(KEY_SS, value=None, min_value=0, max_value=59, placeholder="0~59 sec. (기본값 0)")
with col5:
    milliseconds = st.number_input(KEY_MS, value=None, min_value=0, max_value=999, placeholder="0~999 msec. (기본값 0)")

# 가산초 및 패널티초 입력폼
col6, col7 = st.columns(2)
with col6:
    bonus_time = st.number_input(KEY_BONUS_TIME, value=None, min_value=0.0, max_value=999.0, placeholder="0.0~999.0 sec. (기본값 0.000)", step=1., format="%.3f")
with col7:
    penalty_time = st.number_input(KEY_PENALTY_TIME, value=None, min_value=0.0, max_value=999.0, placeholder="0.0~999.0 sec. (기본값 0.000)", step=1., format="%.3f")

# value가 None일 경우 대응
lap_number = 1 if lap_number is None else lap_number
minutes = 0 if minutes is None else minutes
seconds = 0 if seconds is None else seconds
milliseconds = 0 if milliseconds is None else milliseconds
bonus_time = 0.0 if bonus_time is None else bonus_time
penalty_time = 0.0 if penalty_time is None else penalty_time

# 합계 시간 계산
input_time = (minutes * 60 + seconds) * 1000 + milliseconds

# <<<<<<< HEAD

# def time_to_ms(time_str):
#     minutes, seconds, milliseconds = map(int, time_str.split(":"))
#     return (minutes * 60 + seconds) * 1000 + milliseconds

# # 앞 순위와의 시간 차이 계산 함수
# def calculate_time_difference(df):
#     differences = []
#     for i in range(len(df)):
#         if i == 0:
#             differences.append("0:00:000")  # 첫 번째는 비교 대상이 없으므로 0으로 표시
#         else:
#             curr_total_time = time_to_ms(df[KEY_TOTAL_TIME].iloc[i])
#             prev_total_time = time_to_ms(df[KEY_TOTAL_TIME].iloc[i - 1])
#             diff = curr_total_time - prev_total_time
#             differences.append(format_time(diff))
#     return differences
# =======
# 자동 가산초 입력 기능 추가
if name in st.session_state.bonus_times[KEY_NAME].values:
    bonus_time = st.session_state.bonus_times.loc[st.session_state.bonus_times[KEY_NAME] == name, KEY_BONUS_TIME].values[0]
else:
    bonus_time = 0.0  # 이름이 없으면 기본값으로 설정

total_time = input_time + (bonus_time * 1000) + (penalty_time * 1000)

formatted_time = format_time(input_time)
formatted_total_time = format_time(total_time)
submit_button = st.button(label='제출')
submit_message = st.empty()

def submit_update(data, name, lap_number):
    if not st.session_state.leaderboard.empty:
        if ((st.session_state.leaderboard[KEY_NAME] == name) & (st.session_state.leaderboard[KEY_LAP_NUMBER] == lap_number)).any():
            submit_message.warning("이미 존재하는 이름과 주행 차수입니다. 다른 값을 입력하세요.")
            time.sleep(1)
            submit_message.empty()
            return
        else:
            new_entry = pd.DataFrame([[name, lap_number, formatted_time, bonus_time, penalty_time, formatted_total_time]], columns=COLUMN_NAMES)
            st.session_state.leaderboard = pd.concat([st.session_state.leaderboard, new_entry], ignore_index=True)
    else:
        new_entry = pd.DataFrame([[name, lap_number, formatted_time, bonus_time, penalty_time, formatted_total_time]], columns=COLUMN_NAMES)
        st.session_state.leaderboard = new_entry

    st.session_state.leaderboard = st.session_state.leaderboard.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)
    st.session_state.leaderboard.to_csv(DATA_FILE, index=False, encoding='utf-8')
    submit_message.success("기록이 성공적으로 저장되었습니다!")
    time.sleep(1)  # 1초 대기
    submit_message.empty()  # 메시지를 지움

# 제출 시 데이터 업데이트
if submit_button and name:
    submit_update(st.session_state.leaderboard, name, lap_number)

# 리더보드 정렬 및 시간 차이 계산
st.session_state.leaderboard = st.session_state.leaderboard.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)

# 합계 시간 차이 열 추가
st.session_state.leaderboard[KEY_DIFF_TIME] = calculate_time_difference(st.session_state.leaderboard)

# 합계 시간을 밀리초로 변환하여 정렬하기
if not st.session_state.leaderboard.empty:
    st.session_state.leaderboard[KEY_TOTAL_TIME_MS] = st.session_state.leaderboard[KEY_TOTAL_TIME].apply(time_str_to_ms)
    st.session_state.leaderboard = st.session_state.leaderboard.sort_values(by=KEY_TOTAL_TIME_MS).reset_index(drop=True)
    st.session_state.leaderboard.drop(columns=[KEY_TOTAL_TIME_MS], inplace=True)  # 정렬 후 필요 없는 열 삭제

# 가산초 및 패널티초 포맷 변경
st.session_state.leaderboard[KEY_BONUS_TIME] = st.session_state.leaderboard[KEY_BONUS_TIME].map(lambda x: f"{x:.3f}")
st.session_state.leaderboard[KEY_PENALTY_TIME] = st.session_state.leaderboard[KEY_PENALTY_TIME].map(lambda x: f"{x:.3f}")

# 리더보드 정렬 및 시간 차이 계산
st.session_state.leaderboard = st.session_state.leaderboard.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)

# 합계 시간 차이 열 추가
st.session_state.leaderboard[KEY_DIFF_TIME] = calculate_time_difference(st.session_state.leaderboard)

# 시간 차이를 포맷하여 보여주기
# st.session_state.leaderboard[KEY_DIFF_TIME] = st.session_state.leaderboard[KEY_DIFF_TIME].apply(lambda x: format_time(x) if x is not None else "N/A")

# 리더보드 표시
st.subheader("리더보드")
if not st.session_state.leaderboard.empty:
    display_data = st.session_state.leaderboard.copy()
    # display_data = st.session_state.leaderboard.copy().iloc[1:]  # 첫 번째 행을 제외한 데이터프레임
    display_data[KEY_RANKING] = display_data.index + 1
    st.table(display_data[[KEY_RANKING, KEY_NAME, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_BONUS_TIME, KEY_PENALTY_TIME, KEY_TOTAL_TIME, KEY_DIFF_TIME]])

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
    title_style = ParagraphStyle(name='TitleStyle', fontName='NotoSansKR', fontSize=18, alignment=1)
    header_style = ParagraphStyle(name='HeaderStyle', fontName='NotoSansKR', fontSize=14, alignment=1)
    cell_style = ParagraphStyle(name='CellStyle', fontName='NotoSansKR', fontSize=11)

    elements = []
    elements.append(Paragraph(st.session_state.title, title_style))
    elements.append(Spacer(1, 40))

    data = [[Paragraph(KEY_RANKING, header_style),
             Paragraph(KEY_NAME, header_style),
             Paragraph(KEY_LAP_NUMBER, header_style),
             Paragraph(KEY_LAP_TIME, header_style),
             Paragraph(KEY_BONUS_TIME, header_style),
             Paragraph(KEY_PENALTY_TIME, header_style),
             Paragraph(KEY_TOTAL_TIME, header_style),
             Paragraph(KEY_DIFF_TIME, header_style)]]

    for i, row in dataframe.iterrows():
        data.append([Paragraph(str(i + 1), cell_style),
                     Paragraph(row[KEY_NAME], cell_style), 
                     Paragraph(str(row[KEY_LAP_NUMBER]), cell_style),
                     Paragraph(row[KEY_LAP_TIME], cell_style), 
                     Paragraph(str(row[KEY_BONUS_TIME]), cell_style),
                     Paragraph(str(row[KEY_PENALTY_TIME]), cell_style), 
                     Paragraph(row[KEY_TOTAL_TIME], cell_style),
                     Paragraph(row[KEY_DIFF_TIME], cell_style)])

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

