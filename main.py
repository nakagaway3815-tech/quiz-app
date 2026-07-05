import streamlit as st
import pandas as pd
import random
from gtts import gTTS
import io
import os  # 💡 ファイルの存在チェックに必要です

# --- 1. 音声読み上げ用の関数 ---
def speak_text(text):
    tts = gTTS(text=text, lang='ja')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    st.audio(fp, format='audio/mp3', autoplay=True)

# --- 2. 初期設定 ---
if "wrong_list" not in st.session_state:
    st.session_state.wrong_list = []

st.set_page_config(page_title="介護用語トレーニング", layout="centered")

# 【UI工夫①】サクラ色のテーマ
st.markdown("<style>:root { --primary-color: #ffb6c1; }</style>", unsafe_allow_html=True)

# レベルに応じたCSVファイルを読み込む関数
def load_data_by_level(level):
    if level == 1:
        filename = "data.csv"
    else:
        filename = f"data_level{level}.csv"
    return pd.read_csv(filename)

# 💡 【新機能】すべてのCSVと画像ファイルが一致しているか自動テストする関数
def run_data_check():
    st.subheader("🔍 データ自動チェック結果")
    error_found = False
    
    # レベル1から3まで順番に調べる
    for lvl in [1, 2, 3]:
        try:
            df = load_data_by_level(lvl)
            st.write(f"📁 **レベル {lvl} の確認中...** (全 {len(df)} 語)")
            
            for idx, row in df.iterrows():
                if '画像ファイル名' in row and pd.notna(row['画像ファイル名']):
                    img_name = str(row['画像ファイル名']).strip()
                    
                    # 空欄や "no.png" 以外の画像名が書かれている場合だけチェック
                    if img_name != "" and img_name != "nan" and img_name != "no.png":
                        # GitHub上（ローカルフォルダ内）にそのファイルがあるか確認
                        if not os.path.exists(img_name):
                            st.error(f"❌ レベル{lvl}の「{row['用語']}」: `{img_name}` という画像ファイルが見つかりません！")
                            error_found = True
        except Exception as e:
            st.error(f"❌ レベル {lvl} のCSVファイル自体が開けません: {e}")
            error_found = True
            
    if not error_found:
        st.success("✅ パーフェクト！ すべての画像ファイルが正しく存在しています。バグはありません！")

# セッション状態（データ保持）の初期化
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
    st.session_state.selected_level = None
    st.session_state.index = 0
    st.session_state.answered = False
    st.session_state.correct_count = 0
    st.session_state.current_options = []
    st.session_state.max_questions = 0

# --- 3. レベル選択 ＆ 出題数選択画面 ---
if st.session_state.quiz_data is None:
    st.title("🏥 介護用語クイズ")
    
    # ステップA：まだレベルが選ばれていない場合
    if st.session_state.selected_level is None:
        
        # 💡 【新機能】画面の右上にテスト実行用の拡張エリアを作る
        with st.expander("⚙️ データチェック（管理者用）"):
            if st.button("テストを実行する"):
                run_data_check()
        
        st.write("---")
        st.subheader("レベルを えらんでください（難易度選択）")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🌟 レベル1\n(初級・基本の30語)", use_container_width=True):
                st.session_state.selected_level = 1
                st.rerun()
        with col2:
            if st.button("🔥 レベル2\n(中級・福祉士レベル)", use_container_width=True):
                st.session_state.selected_level = 2
                st.rerun()
        with col3:
            if st.button("🏆 レベル3\n(上級・医療連携レベル)", use_container_width=True):
                st.session_state.selected_level = 3
                st.rerun()
        st.stop()
        
    # ステップB：レベルは選ばれたが、問題数がまだの場合
    else:
        level_names = {1: "初級 (レベル1)", 2: "中級 (レベル2)", 3: "上級 (レベル3)"}
        st.write(f"現在の選択: **{level_names[st.session_state.selected_level]}**")
        st.subheader("今日は何問解きますか？")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("10問", use_container_width=True):
                st.session_state.max_questions = 10
        with col2:
            if st.button("20問", use_container_width=True):
                st.session_state.max_questions = 20
        with col3:
            if st.button("30問", use_container_width=True):
                st.session_state.max_questions = 30
                
        if st.session_state.max_questions > 0:
            level_df = load_data_by_level(st.session_state.selected_level)
            num = min(st.session_state.max_questions, len(level_df))
            st.session_state.quiz_data = level_df.sample(n=num).reset_index(drop=True)
            st.rerun()
        st.stop()

# --- 4. 全問題終了後の画面 ---
df = st.session_state.quiz_data
if st.session_state.index >= len(df):
    st.balloons()
    st.header("🎉 終了！おつかれさまでした！")
    st.subheader(f"正解数: {st.session_state.correct_count} / {len(df)}")
    
    score_rate = st.session_state.correct_count / len(df)
    
    if score_rate == 1.0:
        st.success("🥇 **パーフェクト！ 満点（まんてん）です！**\n\n素晴らしいです！ あなたは介護用語の天才（てんさい）ですね！✨")
    elif score_rate >= 0.8:
        st.info("🥈 **おしい！ あとすこしです！**\n\nとても良い成績（せいせき）です！ 次は満点を目指しましょう！👍")
    else:
        st.warning("🥉 **もうすこし 頑張り（がんばり）ましょう！**\n\n間違えた言葉を復習（ふくしゅう）して、もう一度チャレンジしてみてくださいね。😊")
    
    st.write("---")
    st.subheader("🚩 苦手克服リスト")
    if st.session_state.wrong_list:
        for q in st.session_state.wrong_list:
            st.write(f"・ **{q}**")
    else:
        st.success("完璧です！ 間違えた言葉はありません！")

    if st.button("メニューに戻る", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.stop()

# --- 5. クイズ画面 ---
row = df.iloc[st.session_state.index]

st.title("🏥 介護用語クイズ")
st.progress(st.session_state.index / len(df))
st.write(f"進捗: {st.session_state.index + 1} / {len(df)} 問目")

st.info(f"「**{row['用語']}**」はどういう意味ですか？")

if st.button("📢 おとを きく (音声読み上げ)"):
    speak_text(row['用語'])

if not st.session_state.answered and not st.session_state.current_options:
    options = [row['正しい意味'], row['不正解1'], row['不正解2']]
    random.shuffle(options)
    st.session_state.current_options = options

choice = st.radio("答えを選んでください：", st.session_state.current_options, index=None, key=f"q_{st.session_state.index}", horizontal=True)

if not st.session_state.answered:
    if st.button("回答する", use_container_width=True):
        if choice is None:
            st.warning("選択肢を選んでください！")
        else:
            st.session_state.answered = True
            st.rerun()

# --- 6. 回答後の処理 ---
if st.session_state.answered:
    if choice == row['正しい意味']:
        st.success("⭕ 正解です！ すごいですね！ ✨")

        if '画像ファイル名' in row and pd.notna(row['画像ファイル名']):
            img_name = str(row['画像ファイル名']).strip()
            # 💡 ここも no.png を弾くように安全対策をしてあります
            if img_name != "" and img_name != "nan" and img_name != "no.png":
                st.image(img_name, width=400)
            
        if 'last_counted' not in st.session_state or st.session_state.last_counted != st.session_state.index:
            st.session_state.correct_count += 1
            st.session_state.last_counted = st.session_state.index
    else:
        st.error(f"❌ ざんねん！ つぎは がんばりましょう！\n\n正解は： **{row['正しい意味']}**")
        if row['用語'] not in st.session_state.wrong_list:
            st.session_state.wrong_list.append(row['用語'])

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**【やさしい日本語】**\n\n" + str(row['やさしい日本語']))
    with col2:
        st.success("**【Bahasa Indonesia】**\n\n" + str(row['インドネシア語']))
    
    st.write("**【くわしい解説】**")
    st.write(row['解説'])

    if st.button("次の問題へ ➡️", use_container_width=True):
        st.session_state.index += 1
        st.session_state.answered = False
        st.session_state.current_options = []
        st.rerun()
