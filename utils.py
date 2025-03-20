
# import time
import io
import streamlit as st
import pandas as pd
import os

from const import BONUS_TIME_FILE, COLUMN_NAMES, DATA_FILE, KEY_BONUS_TIME, KEY_DIFF_TIME, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_NAME, KEY_PENALTY_TIME, KEY_RANKING, KEY_TOTAL_TIME
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

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