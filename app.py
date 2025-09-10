# -*- coding: utf-8 -*-
import streamlit as st
from team_creator import render_team_creator
from team_editor import render_team_editor
from battle_judge import render_battle_judge

# 左ペインのページ選択
page = st.sidebar.radio("▼ ページを選んでください", options=["トップページ", "新規チーム作成", "チーム選択・削除", "バトル判定"], index=0)

# ページの分岐
if page == "新規チーム作成":
    render_team_creator()
    st.stop()
elif page == "チーム選択・削除":
    render_team_editor()
    st.stop()
elif page == "バトル判定":
    render_battle_judge()
    st.stop()
else:
    # トップページ
    st.title("バトル相性カンニングシステム")
    st.markdown(
        """
        このシステムは某「街を歩いてモンスターを捕まえるゲーム」のモンスターバトルでのタイプ相性を診断するツールです。<br>
        自分のチームに登録したモンスターと、相手が使ってくるモンスターとのタイプ相性を自動で評価してくれます。<br>
        「タイプ相性が覚えられない…」「どのモンスターが有利かわからない…」という方にぴったりのツールです。<br>
        <br>
        <h3>◆ 使い方</h3>
        1. 「新規チーム作成」ページで自分のモンスター3体を選んでチームを作成<br>
        2. 「チーム選択・削除」ページでバトルで使うチームを選択<br>
        3. 「バトル判定」ページで相手のモンスターのタイプを入力すると相性診断が表示されます<br>
        <br>
        左側のメニュー（ラジオボタン）からページを選んでモンスターバトルに挑戦しましょう！
        """,
        unsafe_allow_html=True
    )
