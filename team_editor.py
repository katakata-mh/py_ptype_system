# -*- coding: utf-8 -*-
import streamlit as st
import base64
import uuid
import json
import os
import random
from ui_components import IMAGE_OPTIONS, TYPE_IMAGE_OPTIONS, prepare_base64_images, render_monster_card, show_icon

# セーブ先の宣言
SAVE_PATH = "saved_teams.json"

# base64画像を準備
TYPE_IMAGE_BASE64 = prepare_base64_images(TYPE_IMAGE_OPTIONS)
IMAGE_BASE64 = prepare_base64_images(IMAGE_OPTIONS)

# セーブデータをロードする
def load_saved_teams(filepath="saved_teams.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# チーム名を20文字だけ表示する（チーム名が長い場合の対策）
def shorten_name(name, max_len=20):
    return name if len(name) <= max_len else name[:max_len] + "…"


# チームを削除する
def delete_team(load_teams, i):
    del load_teams[i]
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(load_teams, f, ensure_ascii=False, indent=2)
    return load_teams


# 【メイン】保存されているチームの表示
def render_team_editor():

    # ローディング
    with st.status("セーブデータ を よみこみチュウ ... ⚡", expanded=True) as status:

        st.title("チーム選択")
        st.markdown(
            """
            作成済みのチームから、バトルで使用するチームを選びましょう。 <br>
            選択されたチームには「⭐ バトルで使用中」と表示され、デフォルトでは一番上のチームが選ばれています。<br>
            <br>
            最大で2つのチームを作成できます。<br>
            上限に達している場合は、不要なチームを削除してから新しいチームを作成してください。<br><br>
            <h3>◆チーム選択の手順</h3>
            1. バトルに使いたいチームの「バトルで使用する」ボタンをクリック<br>
            2. 使わなくなったチームは「削除」ボタンで削除できます<br>
            <br><br>
            """,
            unsafe_allow_html=True
        )
        # チームデータの読み込み
        load_teams = load_saved_teams()

        # チームが存在しない場合：案内
        if not isinstance(load_teams, list) or not load_teams:
            st.info("作成済みのチームはありません。左のメニューから「新規チーム作成」を選んで、チームを登録してください。")
            
            # ローディング完了メッセージ
            status.update(label="まずは モンスター を つかまえて チーム を つくろう 💧 ", state="complete")
            return

        # デフォルトで1番左のチームを選択
        if "selected_team_index" not in st.session_state:
            st.session_state["selected_team_index"] = 0

        # チーム詳細表示
        st.markdown("▼ チーム名をクリックするとチームの情報が確認できます")
        tabs = st.tabs([f"{shorten_name(team['チーム名'])}" for team in load_teams])

        # 各タブにチーム詳細を表示
        for idx, (tab, myteam) in enumerate(zip(tabs, load_teams)):
            with tab:

                # ローディング用メッセージ
                status.update(label=f"{myteam['チーム名']} の モンスター を ひょうじチュウ ... ⚡")

                # 選択状態の判定
                is_selected = st.session_state["selected_team_index"] == idx

                # ボタン（選択・削除）表示
                button_cols = st.columns([3, 5, 2])

                with button_cols[0]:
                    if is_selected:
                        st.markdown("⭐ **バトルで使用中**")
                    else:
                        if st.button("バトルで使用する", key=f"select_team_{idx}"):
                            st.session_state["selected_team_index"] = idx
                            st.rerun()

                with button_cols[2]:
                    if st.button("削除", key=f"delete_team_{idx}"):
                        delete_team(load_teams, idx)
                        st.rerun()

                # モンスターの表示
                cols = st.columns(3)
                for i in range(3):
                    with cols[i]:
                        monster_data = myteam["モンスター"][str(i + 1)]
                        render_monster_card(monster_data, TYPE_IMAGE_BASE64, IMAGE_BASE64)


        # ローディング完了メッセージ
        status.update(label="じゅんび かんりょう！ チーム を えらぼう 🌸", state="complete")

