import time
import streamlit as st
import pandas as pd
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


from const import ADMIN_PASSWORD, BACKUP_FILE, COLUMN_NAMES, DATA_FILE, DEFAULT_TITLE, KEY_BONUS_TIME, KEY_CLASS, KEY_DIFF_TIME, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_MM, KEY_MS, KEY_NAME, KEY_PENALTY_TIME, KEY_RANKING, KEY_SS, KEY_TOTAL_TIME, KEY_TOTAL_TIME_MS, TITLE_FILE
from utils import calculate_time_difference, create_pdf, format_time, load_bonus_times, load_data, time_str_to_ms

# 클래스 목록
CAR_CLASSES = ["A", "B", "ND", "86", "M", "N"]

# 한글 폰트 등록
pdfmetrics.registerFont(TTFont('NotoSansKR', 'NotoSansKR-Regular.ttf'))

# 초기화
def initialize_session_state():
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


def input_form(classes):
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

    # 클래스 선택
    selected_class = st.selectbox("클래스를 선택하세요:", classes)

    # value가 None일 경우 대응
    lap_number = 1 if lap_number is None else lap_number
    minutes = 0 if minutes is None else minutes
    seconds = 0 if seconds is None else seconds
    milliseconds = 0 if milliseconds is None else milliseconds
    bonus_time = 0.0 if bonus_time is None else bonus_time
    penalty_time = 0.0 if penalty_time is None else penalty_time

    # 합계 시간 계산
    input_time = (minutes * 60 + seconds) * 1000 + milliseconds

    # 자동 가산초 입력 기능 추가
    if bonus_time == 0.0 and name in st.session_state.bonus_times[KEY_NAME].values:
        bonus_time = st.session_state.bonus_times.loc[st.session_state.bonus_times[KEY_NAME] == name, KEY_BONUS_TIME].values[0]
        bonus_time = float(bonus_time) if isinstance(bonus_time, str) else bonus_time

    total_time = input_time + int(bonus_time * 1000) + int(penalty_time * 1000)

    formatted_time = format_time(input_time)
    formatted_total_time = format_time(total_time)
    submit_button = st.button(label='제출')
    submit_message = st.empty()

    return name, lap_number, selected_class, formatted_time, bonus_time, penalty_time, formatted_total_time, submit_button, submit_message

def submit_update(data, name, lap_number, selected_class, formatted_time, bonus_time, penalty_time, formatted_total_time, submit_message):
    if not st.session_state.leaderboard.empty:
        # 클래스, 이름, 주행 차수 중복 확인
        if ((st.session_state.leaderboard[KEY_NAME] == name) &
            (st.session_state.leaderboard[KEY_LAP_NUMBER] == lap_number) &
            (st.session_state.leaderboard[KEY_CLASS] == selected_class)).any():
            submit_message.warning("이미 존재하는 이름과 주행 차수입니다. 다른 값을 입력하세요.")
            time.sleep(1)
            submit_message.empty()
            return
        else:
            new_entry = pd.DataFrame([[name, selected_class, lap_number, formatted_time, f"{bonus_time:.3f}", f"{penalty_time:.3f}", formatted_total_time]], columns=COLUMN_NAMES)
            st.session_state.leaderboard = pd.concat([st.session_state.leaderboard, new_entry], ignore_index=True)
    else:
        new_entry = pd.DataFrame([[name, selected_class, lap_number, formatted_time, f"{bonus_time:.3f}", f"{penalty_time:.3f}", formatted_total_time]], columns=COLUMN_NAMES)
        st.session_state.leaderboard = new_entry

    st.session_state.leaderboard = st.session_state.leaderboard.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)
    st.session_state.leaderboard.to_csv(DATA_FILE, index=False, encoding='utf-8')
    submit_message.success("기록이 성공적으로 저장되었습니다!")
    time.sleep(1)  # 1초 대기
    submit_message.empty()  # 메시지를 지움


def process_leaderboard(leaderboard):
    # 리더보드 정렬 및 시간 차이 계산
    leaderboard = leaderboard.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)

    # 합계 시간 차이 열 추가
    leaderboard[KEY_DIFF_TIME] = calculate_time_difference(leaderboard)

    # 합계 시간을 밀리초로 변환하여 정렬하기
    if not leaderboard.empty:
        leaderboard[KEY_TOTAL_TIME_MS] = leaderboard[KEY_TOTAL_TIME].apply(time_str_to_ms)
        leaderboard = leaderboard.sort_values(by=KEY_TOTAL_TIME_MS).reset_index(drop=True)
        leaderboard.drop(columns=[KEY_TOTAL_TIME_MS], inplace=True)  # 정렬 후 필요 없는 열 삭제

    # 가산초 및 패널티초 포맷 변경
    leaderboard[KEY_BONUS_TIME] = leaderboard[KEY_BONUS_TIME].map(lambda x: f"{float(x):.3f}" if x != "" else "0.000")
    leaderboard[KEY_PENALTY_TIME] = leaderboard[KEY_PENALTY_TIME].map(lambda x: f"{float(x):.3f}" if x != "" else "0.000")

    # 리더보드 정렬 및 시간 차이 계산
    leaderboard = leaderboard.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)

    # 합계 시간 차이 열 추가
    leaderboard[KEY_DIFF_TIME] = calculate_time_difference(leaderboard)

    return leaderboard


def display_leaderboard_by_class(classes, leaderboard):
    # 각 클래스에 대해 리더보드 표시
    for class_name in classes:
        if not leaderboard.empty and leaderboard[KEY_CLASS].isin([class_name]).any():
            st.subheader(f"리더보드 {class_name}")
            display_data = leaderboard.copy()
            
            # 클래스 필터링
            display_data = display_data[display_data[KEY_CLASS] == class_name]
            
            # 순위 계산 (동일한 시간은 같은 순위로 표시)
            display_data = display_data.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)
            display_data[KEY_RANKING] = display_data[KEY_TOTAL_TIME].rank(method='min').astype(int)
            # 셀 번호를 1부터 시작하도록 설정
            display_data.index = display_data.index + 1
            st.table(display_data[[KEY_RANKING, KEY_CLASS, KEY_NAME, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_BONUS_TIME, KEY_PENALTY_TIME, KEY_TOTAL_TIME, KEY_DIFF_TIME]])

def display_overall_leaderboard(leaderboard):
    # 리더보드 전체 표시
    st.subheader("리더보드 All")
    if not leaderboard.empty:
        display_data = leaderboard.copy()
        # 순위 계산 (동일한 시간은 같은 순위로 표시)
        display_data = display_data.sort_values(by=KEY_TOTAL_TIME).reset_index(drop=True)
        display_data[KEY_RANKING] = display_data[KEY_TOTAL_TIME].rank(method='min').astype(int)
        # 셀 번호를 1부터 시작하도록 설정
        display_data.index = display_data.index + 1
        st.table(display_data[[KEY_RANKING, KEY_CLASS, KEY_NAME, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_BONUS_TIME, KEY_PENALTY_TIME, KEY_TOTAL_TIME, KEY_DIFF_TIME]])

def download_features(leaderboard, title):
    if st.button("리더보드 CSV 다운로드"):
        if not leaderboard.empty:
            display_data = leaderboard.copy()
            display_data[KEY_RANKING] = display_data.index + 1
            csv = display_data.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("Download CSV", csv, file_name=f"{title}.csv", mime='text/csv')
        else:
            st.warning("리더보드에 데이터가 없습니다.")

    if st.button("리더보드 HTML 다운로드"):
        if not leaderboard.empty:
            display_data = leaderboard.copy()
            display_data[KEY_RANKING] = display_data.index + 1
            html = display_data.to_html(index=False, escape=False)
            html_with_title = f"<h1 style='text-align: center;'>{title}</h1>\n" + html
            st.download_button("Download HTML", html_with_title.encode('utf-8'), file_name=f"{title}.html", mime='text/html')
        else:
            st.warning("리더보드에 데이터가 없습니다.")

    if st.button("리더보드 PDF 다운로드"):
        if not leaderboard.empty:
            pdf_buffer = create_pdf(leaderboard)
            st.download_button("Download PDF", pdf_buffer, file_name=f"{title}.pdf", mime='application/pdf')
        else:
            st.warning("리더보드에 데이터가 없습니다.")

    # Markdown 저장 기능
    if st.button("리더보드 Markdown 다운로드"):
        if not leaderboard.empty:
            display_data = leaderboard.copy()
            display_data[KEY_RANKING] = display_data.index + 1
            markdown = display_data.to_markdown(index=False)
            st.download_button("Download Markdown", markdown.encode('utf-8'), file_name=f"{title}.md", mime='text/markdown')
        else:
            st.warning("리더보드에 데이터가 없습니다.")


def admin_features():
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


def main():
    initialize_session_state()

    load_bonus_times()  # 가산초 데이터 로드
    load_data()

    st.title(st.session_state.title)

    # Call the function
    name, lap_number, selected_class, formatted_time, bonus_time, penalty_time, formatted_total_time, submit_button, submit_message = input_form(CAR_CLASSES)

    # 제출 시 데이터 업데이트
    if submit_button and name:
        submit_update(st.session_state.leaderboard, name, lap_number, selected_class, formatted_time, bonus_time, penalty_time, formatted_total_time, submit_message)

    # Process the leaderboard
    st.session_state.leaderboard = process_leaderboard(st.session_state.leaderboard)

    display_leaderboard_by_class(CAR_CLASSES, st.session_state.leaderboard)
    display_overall_leaderboard(st.session_state.leaderboard)

    # 다운로드 기능
    st.markdown("---")
    st.subheader("다운로드 기능")
    download_features(st.session_state.leaderboard, st.session_state.title)

    st.markdown("---")
    admin_features()

if __name__ == "__main__":
    main()
