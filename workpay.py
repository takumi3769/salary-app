import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import jpholiday
from sqlalchemy import text

# --- 1. データベース設定 ---
conn = st.connection('salary_db', type='sql', url='sqlite:///my_salary.db')

def init_db():
    with conn.session as s:
        s.execute(text('CREATE TABLE IF NOT EXISTS shifts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, start TEXT, end TEXT, total_h REAL, night_h REAL, salary INTEGER);'))
        s.execute(text('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);'))
        s.commit()

init_db()

def get_saved_wage():
    df = conn.query("SELECT value FROM settings WHERE key='hourly_wage'", ttl=0)
    return int(df.iloc[0]['value']) if not df.empty else 1200

def save_wage(wage):
    with conn.session as s:
        s.execute(text("INSERT OR REPLACE INTO settings (key, value) VALUES ('hourly_wage', :wage)"), {"wage": str(wage)})
        s.commit()

# --- 2. 画面基本設定 ---
st.set_page_config(page_title="給料管理", page_icon="💰", layout="centered")

# --- 3. カスタムCSS（クリック時の黒ずみ防止を追加） ---
st.markdown("""
    <style>
    /* 全体の背景色を水色に固定 */
    .stApp { background-color: #E0F2F7 !important; }
    header, [data-testid="stHeader"] { background-color: #E0F2F7 !important; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF !important; }

    /* --- ボタンの基本スタイル --- */
    div.stButton > button {
        background-color: #D3D3D3 !important; 
        color: #000000 !important; 
        border: 1px solid #999999 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.2s ease-in-out !important;
        width: 100%;
    }

    /* マウスホバー時 */
    div.stButton > button:hover {
        transform: translateY(-2px) scale(1.01);
        border-color: #ff4b4b !important;
        color: #ff4b4b !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        background-color: #DCDCDC !important; /* ホバー時はわずかに色を変える */
    }

    /* 【重要】クリック中・クリック後の黒ずみ/青枠を徹底排除 */
    div.stButton > button:focus,
    div.stButton > button:active,
    div.stButton > button:focus-visible {
        background-color: #D3D3D3 !important; /* 元のグレーを維持 */
        color: #000000 !important;             /* 文字色を黒で固定 */
        border: 1px solid #999999 !important; /* 枠線を維持 */
        box-shadow: none !important;           /* 影（黒ずみの原因）を消す */
        outline: none !important;              /* フォーカス枠を消す */
    }

    /* 入力エリアの背景白抜き設定 */
    div[data-baseweb="input"], 
    div[data-baseweb="select"] > div, 
    div[data-testid="stDateInput"] > div,
    div[data-testid="stNumberInput"] div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 8px !important;
    }

    input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* 文字色を黒に統一 */
    h1, h2, h3, p, label, span, [data-testid="stMetricValue"], [data-testid="stWidgetLabel"] p {
        color: #000000 !important;
    }

    /* 履歴テーブルの装飾 */
    div[data-testid="stTable"] { background-color: #FFFFFF !important; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. サイドバー：時給設定 ---
current_wage = get_saved_wage()
with st.sidebar:
    st.header("⚙️ 設定")
    new_wage = st.number_input("基本時給(円)", value=current_wage, step=10, key="wage_input")
    if st.button("時給を保存"):
        save_wage(new_wage)
        st.success("時給を保存しました")
        st.rerun()

st.title("💰 給料計算システム")

# --- 5. 入力セクション ---
st.subheader("📅 勤務日の選択")
d = st.date_input("日付", datetime.now())

is_holiday = jpholiday.is_holiday(d)
is_weekend = d.weekday() >= 5 
base_wage_today = current_wage + 50 if (is_holiday or is_weekend) else current_wage

if is_holiday or is_weekend:
    st.warning(f"📅 本日は土日祝手当適用：ベース時給 {base_wage_today}円")

st.divider()

st.subheader("🕒 勤務時間")
col_start, col_end = st.columns(2)
with col_start:
    st.write("**出勤**")
    c1, c2 = st.columns(2)
    with c1: sh = st.selectbox("時", list(range(24)), index=18, key="sh")
    with c2: sm = st.selectbox("分", list(range(60)), index=0, key="sm")
    s_t = time(sh, sm)
with col_end:
    st.write("**退勤**")
    c3, c4 = st.columns(2)
    with c3: eh = st.selectbox("時", list(range(24)), index=22, key="eh")
    with c4: em = st.selectbox("分", list(range(60)), index=0, key="em")
    e_t = time(eh, em)

st.write("---")

break_choice = st.radio("☕ 休憩の有無", ["なし", "あり"], horizontal=True)
has_break = (break_choice == "あり")

if has_break:
    col_b_start, col_b_end = st.columns(2)
    with col_b_start:
        st.write("**休憩開始**")
        bc1, bc2 = st.columns(2)
        with bc1: bsh = st.selectbox("時", list(range(24)), index=19, key="bsh")
        with bc2: bsm = st.selectbox("分", list(range(60)), index=0, key="bsm")
        b_s = time(bsh, bsm)
    with col_b_end:
        st.write("**休憩終了**")
        bc3, bc4 = st.columns(2)
        with bc3: beh = st.selectbox("時", list(range(24)), index=20, key="beh")
        with bc4: bem = st.selectbox("分", list(range(60)), index=0, key="bem")
        b_e = time(beh, bem)
else:
    b_s = b_e = time(0, 0)

# --- 6. 計算ロジック ---
def calculate_by_minute(d, s_t, e_t, b_s, b_e, base_wage, has_break):
    start_dt = datetime.combine(d, s_t)
    end_dt = datetime.combine(d, e_t)
    if end_dt <= start_dt: end_dt += timedelta(days=1)
    if has_break:
        bs_dt = datetime.combine(d, b_s); be_dt = datetime.combine(d, b_e)
        if be_dt <= bs_dt: be_dt += timedelta(days=1)
    else: bs_dt = be_dt = datetime.min
    
    total_salary = 0.0; work_minutes = 0; night_minutes = 0
    curr = start_dt
    while curr < end_dt:
        if not (bs_dt <= curr < be_dt):
            work_minutes += 1
            minute_wage = base_wage / 60.0
            if curr.hour >= 22 or curr.hour < 5:
                night_minutes += 1; total_salary += minute_wage * 1.25
            else: total_salary += minute_wage
        curr += timedelta(minutes=1)
    return work_minutes/60.0, night_minutes/60.0, int(total_salary)

actual_h, night_h, salary = calculate_by_minute(d, s_t, e_t, b_s, b_e, base_wage_today, has_break)

st.divider()
st.info(f"💡 **計算結果**\n\n実労働: {int(actual_h*60)}分 ({actual_h:.2f}h) ／ 深夜分: {int(night_h*60)}分 ／ 給料: **{salary:,}円**")

# --- 7. 保存・履歴管理 ---
if st.button("💾 この内容で履歴に保存"):
        with conn.session as s:
            s.execute(text("INSERT INTO shifts (date, start, end, total_h, night_h, salary) VALUES (:date, :start, :end, :total_h, :night_h, :salary)"),
                      {"date": d.strftime('%Y-%m-%d'), "start": s_t.strftime('%H:%M'), "end": e_t.strftime('%H:%M'), 
                       "total_h": round(actual_h, 2), "night_h": round(night_h, 2), "salary": salary})
            s.commit()
        st.success("履歴に保存しました！")
        st.rerun()

st.subheader("📊 勤務履歴")
df = conn.query("SELECT * FROM shifts ORDER BY date DESC", ttl=0)

if not df.empty:
    m1, m2 = st.columns(2)
    with m1: st.metric("累計支給額", f"{df['salary'].sum():,} 円")
    with m2: st.metric("総労働時間", f"{df['total_h'].sum():.2f} 時間")
    
    df_display = df.drop(columns=['id']).rename(columns={
        'date': '日付', 'start': '出勤', 'end': '退勤', 'total_h': '労働(h)', 'night_h': '深夜(h)', 'salary': '給料(円)'
    })
    st.table(df_display)

    with st.expander("🗑️ データの個別削除"):
        delete_options = {f"{row['date']} ({row['start']}~{row['end']}) - {row['salary']:,}円": row['id'] for _, row in df.iterrows()}
        target_label = st.selectbox("削除するデータを選択", options=list(delete_options.keys()), key="delete_select")
        if st.button("選択したデータを削除"):
            with conn.session as s:
                s.execute(text("DELETE FROM shifts WHERE id = :id"), {"id": delete_options[target_label]})
                s.commit()
            st.rerun()
else:
    st.write("履歴データはありません。")
