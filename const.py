# 파일 경로
DATA_FILE = 'leaderboard.csv'
TITLE_FILE = 'title.txt'
BACKUP_FILE = 'leaderboard_backup.csv'
BONUS_TIME_FILE = 'bonus_times.csv'

# 전역 변수
DEFAULT_TITLE = "🏆 GCK Lap time board"
KEY_NAME = "이름"
KEY_CLASS = "클래스"
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
COLUMN_NAMES = [KEY_NAME, KEY_CLASS, KEY_LAP_NUMBER, KEY_LAP_TIME, KEY_BONUS_TIME, KEY_PENALTY_TIME, KEY_TOTAL_TIME]
ADMIN_PASSWORD = "gck@admin" #os.getenv("ADMIN_PASSWORD")  # 환경 변수로부터 비밀번호 불러오기

