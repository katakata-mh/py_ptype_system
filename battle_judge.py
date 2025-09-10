# -*- coding: utf-8 -*-
import streamlit as st
import base64
import uuid
import json
import os
import random
from ui_components import IMAGE_OPTIONS, TYPE_IMAGE_OPTIONS, prepare_base64_images, show_icon, render_monster_image_battlestate, render_type_icons, render_icon_selector
from type_logic import  calculation_attack_defense_evaluation, calculation_totalscore, render_evaluation_guide
from team_editor import load_saved_teams

# タイプ相性表を読み込む
with open("type_chart.json", encoding="utf-8") as f:
    type_chart = json.load(f)

# base64画像を準備
TYPE_IMAGE_BASE64 = prepare_base64_images(TYPE_IMAGE_OPTIONS)
IMAGE_BASE64 = prepare_base64_images(IMAGE_OPTIONS)

# セッション初期化
def initialize_session_state(image_base64, load_teams):
    # チームが存在しない場合：セッションを強制初期化
    if not load_teams:

        # チーム選択インデックスを未選択に設定
        st.session_state["selected_team_index"] = None

        # モンスター設定を空に初期化
        st.session_state["saved_monsters"] = {}

        # 自分と相手のモンスターの「ひんし状態」を初期化（3体分）
        st.session_state["fainted"] = [False, False, False]
        st.session_state["enemy_fainted"] = [False, False, False]

        # 自分と相手の現在のバトル中モンスターの状態を初期化
        st.session_state["active_index"] = 0

        # 相手の構成パターン・タイプ情報を初期化
        st.session_state["enemy_active_index"] = 0
        st.session_state["enemy_config_index"] = 0
        st.session_state["enemy_type1"] = None
        st.session_state["enemy_type2"] = None

        # 相手モンスターの名前、画像、タイプを生成
        st.session_state["enemy_mons"] = [
            {"名前": f"相手モンスター{i+1}", "画像": "未", "タイプ": ["不明", "不明"]}
            for i in range(3)
        ]
        return # 処理を終了

    # チームが存在する場合：セッションに値がなければ初期値を設定
    defaults = {
        "enemy_config_index": 0,
        "enemy_type1": None,
        "enemy_type2": None,
        "fainted": [False, False, False],
        "enemy_fainted": [False, False, False],
        "active_index": 0,
        "enemy_active_index": 0,
    }
    # セッションに未設定のキーだけ初期値をセット
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    # 相手モンスターが未設定の場合：画像付きで初期化（画像はランダム）
    if "enemy_mons" not in st.session_state:
        available_enemy_images = [label for label in image_base64.keys() if label != "未"]
        st.session_state["enemy_mons"] = [
            {"名前": f"相手モンスター{i+1}", "画像": img, "タイプ": ["不明", "不明"]}
            for i, img in enumerate(random.sample(available_enemy_images, 3))
        ]

    # チーム選択インデックスが未設定の場合：0番目のチームを選択状態にする
    if "selected_team_index" not in st.session_state:
        st.session_state["selected_team_index"] = 0

# バトル開始前のリセット処理
def reset_battle():

    # 自分と相手のモンスターのひんし状態をリセット
    st.session_state["fainted"] = [False, False, False]
    st.session_state["enemy_fainted"] = [False, False, False]

    # 相手のタイプ選択状態をリセット
    st.session_state["enemy_type1"] = None
    st.session_state["enemy_type2"] = None

    # 相手モンスターのタイプ選択インデックスを初期化
    st.session_state["enemy_config_index"] = 0

    # 相手モンスター用の画像ラベルをランダムで（かぶりなし）
    available_enemy_images = [label for label in IMAGE_BASE64.keys() if label != "未"]
    enemy_images = random.sample(available_enemy_images, 3)

    # 相手モンスター3体のタイプを「不明」に初期化
    for i, mon in enumerate(st.session_state["enemy_mons"]):
        mon["タイプ"] = ["不明", "不明"]
        mon["画像"] = enemy_images[i] 
    
    # 自分と相手の選択中インデックスを初期化（0番目に戻す）
    st.session_state["enemy_active_index"] = 0
    st.session_state["active_index"] = 0
    st.rerun()

# 戦闘時モンスター切替ボタン・ひんし設定
def render_monster_button(i: int, role: str = "self"):
    """
    モンスターの戦闘ボタン（入替え・ひんし）を描画し、
    ひんしになった場合は自動的に他のモンスターに切替える処理も行う。
    """
    # 状態管理用のキーを役割に応じて設定
    fainted_key = "fainted" if role == "self" else "enemy_fainted"  # ひんし状態のリスト
    active_key = "active_index" if role == "self" else "enemy_active_index"  # 現在選択中のインデックス
    mons_key = None if role == "self" else "enemy_mons"  # 相手の場合はモンスター情報も参照

    # ボタンや表示用テキストの設定
    select_label = "入替え"
    faint_label = "× ひんしにする"
    faint_display = "<span style='color:red; font-weight:bold;'>💀 ひんし状態</span>"

    # ボタン状態管理用キー
    select_key = f"use_{role}_{i}"
    faint_key = f"faint_{role}_{i}"

    # 現在の状態を取得
    fainted_list = st.session_state[fainted_key] # ひんし状態リスト
    active = st.session_state[active_key] == i # このモンスターが現在選択中かどうか
    fainted = fainted_list[i]  # このモンスターがひんしかどうか
    mons = st.session_state.get(mons_key) if mons_key else None

    # 選択中かつひんしでない場合の処理
    if active and not fainted:

        # ひんしにする
        if st.button(faint_label, key=faint_key):
            fainted_list[i] = True

            # 未反映のままひんしになった場合選択を解除
            if role == "enemy" and i == st.session_state["enemy_config_index"]:
                st.session_state["enemy_type1"] = None
                st.session_state["enemy_type2"] = None
                st.session_state["enemy_config_index"] += 1

            if role == "enemy":
                alive_indices = [
                    j for j, f in enumerate(fainted_list)
                    if not f and any(t != "不明" for t in mons[j]["タイプ"])
                ]

                # 条件①：2体ひんし → 残りの1体に自動切替
                if len(alive_indices) == 1:
                    st.session_state["enemy_active_index"] = alive_indices[0]

                # 条件②：1体目がひんし → 2体目が生存＆タイプ未設定なら2体目へ（自動で次を設定）
                elif i == 0 and not fainted_list[1] and all(t == "不明" for t in mons[1]["タイプ"]):
                    st.session_state["enemy_active_index"] = 1

            st.rerun()

    # ひんしでない場合：入替えボタンを表示
    elif not fainted:
        can_switch = True

        if role == "enemy":
            # 相手モンスターの場合：前のモンスターのタイプが未設定なら入替え不可
            prev_index = i - 1
            if prev_index >= 0:

                # 前のモンスターがひんしでなく、かつタイプがすべて「不明」なら入替え不可
                if not fainted_list[prev_index] and all(t == "不明" for t in mons[prev_index]["タイプ"]):
                    can_switch = False

        if can_switch:

            # 入替えボタンがクリックされた場合：
            if st.button(select_label, key=select_key):
                
                # 相手モンスターのタイプ選択中（未反映）なら保存してリセット
                if role == "enemy":
                    idx = st.session_state["enemy_config_index"]
                    type1 = st.session_state.get("enemy_type1")
                    type2 = st.session_state.get("enemy_type2")

                    # どちらかのタイプが選択されていれば、現在のモンスターに反映
                    if type1 or type2:
                        st.session_state["enemy_mons"][idx]["タイプ"] = [
                            type1 or "不明",
                            type2 or "不明"
                        ]
                        # 選択状態をリセットして次のモンスターへ
                        st.session_state["enemy_type1"] = None
                        st.session_state["enemy_type2"] = None
                        st.session_state["enemy_config_index"] += 1
                
                # 入替え対象のモンスターに移動する
                st.session_state[active_key] = i
                st.rerun()
        else:
            # モンスターのタイプ未選択時：入替え不可の案内を表示
            st.markdown(
                "<div style='text-align:left; font-size:15px; color:#999;'>左のモンスターのタイプを設定すると選択できます</div>",
                unsafe_allow_html=True
            )
    # ひんしの場合：「ひんしです」の文字を表示
    else:
        st.markdown(faint_display, unsafe_allow_html=True)

        # ひんし状態のモンスターが選択されている場合 → 入替えを促す
        if active:
            # 他に生存していてタイプが設定済みのモンスターがいるかチェック
            selectable_indices = [
                j for j, f in enumerate(fainted_list)
                if not f and (mons_key is None or any(t != "不明" for t in mons[j]["タイプ"]))
            ]
            if selectable_indices:
                st.markdown(
                    "<div style='font-size:10px; color:red;'>※入替えてください</div>",
                    unsafe_allow_html=True)
            

# 戦闘画面：相手または自分のモンスター3体を横並びで表示（自分には評価も表示）
def render_team_cards(mons, role="self", show_evaluation=False, type_chart=None):
    active_key = "active_index" if role == "self" else "enemy_active_index"
    fainted_key = "fainted" if role == "self" else "enemy_fainted"
    active_index = st.session_state[active_key]
    fainted_list = st.session_state[fainted_key]

    # 相手タイプ
    enemy_types = []
    if show_evaluation and role == "self":
        enemy_index = st.session_state.get("enemy_active_index")
        if enemy_index is not None:
            enemy_types = st.session_state["enemy_mons"][enemy_index]["タイプ"]
          
    cols = st.columns(3)
    for i in range(3):
        mon = mons[i]
        active = active_index == i
        fainted = fainted_list[i]

        with cols[i]:
            
            # ボタン表示
            render_monster_button(i=i, role=role)

            # 中央ぞろえでモンスター名表示(長い名前ように折り返し対策)
            st.markdown(f"<div style='text-align: center;font-weight: bold;font-size: 18px;word-wrap: break-word;white-space: normal;'>{mon['名前']}</div>""",unsafe_allow_html=True)

            # 画像とタイプ表示
            img_col, type_col = st.columns([1, 1])
            with img_col:
                render_monster_image_battlestate(IMAGE_BASE64[mon["画像"]], width=80, darken=fainted, highlight=active)
            with type_col:
                render_type_icons(mon["タイプ"], TYPE_IMAGE_BASE64, width=30)

            # 評価表示（自分側のみ）
            if show_evaluation and type_chart:
                if any(t != "不明" and t is not None for t in enemy_types):
                    score, mark, color = calculation_totalscore(mon, enemy_types, type_chart)
                    st.markdown(
                        f"<span style='font-size:20px; font-weight:bold;'>総合評価：<span style='color:{color};'>{mark}（{score:.2f}）</span></span>",
                        unsafe_allow_html=True
                    )
                    calculation_attack_defense_evaluation("攻撃評価", mon["わざ"], enemy_types, TYPE_IMAGE_BASE64, type_chart, is_attack=True)
                    calculation_attack_defense_evaluation("防御予測", enemy_types, mon["タイプ"], TYPE_IMAGE_BASE64, type_chart, is_attack=False)
                else:
                    st.markdown("<span style='color:gray;'>相手のモンスターのタイプを選択、またはモンスターをすると評価が表示されます</span>", unsafe_allow_html=True)

# 【メイン】バトルの評価
def render_battle_judge():

    # ローディング
    with st.status("データ を よみこみチュウ ... ⚡", expanded=True) as status:

        st.title("バトル評価")
        st.markdown(
            """
            このページでは、現在選択している自分のチームのモンスターと、<br>
            相手モンスターとの**タイプ相性**を診断できます。<br>
            バトルに使うチームを変更したい場合は、左のメニューからチームを作成・選択してください。<br>
            <br>
            <h3>◆バトル評価の使い方</h3>
            1. 相手のモンスターのタイプを選択<br>
            2. 自分のバトル中モンスターとの相性が表示されるので確認<br>
            3. 「入替え」や「ひんしにする」ボタンでモンスターの状態を変更しながらバトルを進めましょう<br>
            <br>
             <h3>◆ポイント</h3>
            - バトル中のモンスター：ピンク色の枠がついているモンスターが現在バトル中です<br>
            - モンスターの入替え：入替えたいモンスターの「入替え」ボタンをクリックします<br>
              ⇒ 相手がモンスターを入替えたら、タイプを選択して再評価できます <br>
            - ひんし：戦えなくなったモンスターは「ひんしにする」ボタンで状態変更し、別のモンスターに入替えましょう<br>
            <br>
            ▼ 評価の見方についてはここから確認してください<br>
            """,
            unsafe_allow_html=True
          )
        # 評価についての説明の表示
        render_evaluation_guide()
        st.markdown("---")

        # 保存済みのチームデータ読み込み
        load_teams = load_saved_teams()

        # チームが存在しない場合：案内を表示して処理終了
        if not isinstance(load_teams, list) or not load_teams:
            st.info("作成済みのチームはありません。左のメニューから「新規チーム作成」を選んで、チームを登録してください。")

            # ローディング完了メッセージ
            status.update(label="まずは モンスター を つかまえて チーム を つくろう ◓", state="complete")
            return

        # セッション初期化
        initialize_session_state(IMAGE_BASE64, load_teams)

        # ローディング用メッセージ
        status.update(label="タイプアイコン を ひょうじチュウ ... ⚡")

        # 相手モンスターのタイプ選択
        st.markdown("### 1. 相手のモンスターのタイプを２つまで選択してください")
        render_icon_selector(label_list=list(TYPE_IMAGE_OPTIONS.keys()), base64_dict=TYPE_IMAGE_BASE64, selected_labels=[st.session_state.get("enemy_type1"), st.session_state.get("enemy_type2")], session_keys=("enemy_type1", "enemy_type2"), max_select=2, title="", image_width=40, columns_per_row=9, highlight_color="#00ccff", border_color="#007BFF", show_label=True, rerun_on_select=True)

        # 自分の選択済みチームのモンスター3体を取得
        selected_team = load_teams[st.session_state["selected_team_index"]]
        my_mons = [selected_team["モンスター"][str(i)] for i in range(1, 4)]

        # タイプ選択の状態を取得（未選択時：不明）
        type1 = st.session_state.get("enemy_type1") or "不明"
        type2 = st.session_state.get("enemy_type2") or "不明"

        # 相手モンスター情報をセッションから取得
        enemy_mons = st.session_state["enemy_mons"]

        # 選択中の相手モンスターにタイプを仮設定
        if st.session_state["enemy_config_index"] < 3: 
            idx = st.session_state["enemy_config_index"]
            st.session_state["enemy_mons"][idx]["タイプ"] = [
                st.session_state.get("enemy_type1") or "不明",
                st.session_state.get("enemy_type2") or "不明"
            ]
            
        st.markdown("※ 一度他のモンスターに入替えるとタイプは変更できません")

        # ひんしチェックと警告表示
        fainted_self = st.session_state["fainted"]
        fainted_enemy = st.session_state["enemy_fainted"]

        # 自分または相手の全モンスターがひんしなら警告表示
        if all(fainted_self) or all(fainted_enemy):
            who = "自分" if all(fainted_self) else "相手"
            st.markdown(
                f"<div style='color:red; font-weight:bold;'>{who}のモンスターがすべてひんしです。ページ下部から次のバトルを選択してください。</div>",
                unsafe_allow_html=True
            )

        # ローディング用メッセージ
        status.update(label="あいて の モンスター を ひょうじチュウ ... ⚡")

        # バトル評価
        st.markdown("### 2.モンスターを入替えながらバトル相性を確認しよう")
        st.markdown("#### 相手のモンスター")
        render_team_cards(st.session_state["enemy_mons"], role="enemy")

        # 「VS」表示（配置：中央）
        left, center, right = st.columns([1, 2, 1])
        with center:
            st.markdown("<h3 style='text-align:center; font-family:monospace;'> V S </h3>", unsafe_allow_html=True)
        
        # ローディング用メッセージ
        status.update(label="じぶん の モンスター を ひょうじチュウ ... ⚡")

        # 自分のチームのモンスターとタイプ相性の評価の表示
        st.markdown("#### 自分のモンスター")
        render_team_cards(my_mons, role="self", show_evaluation=True, type_chart=type_chart)

        st.markdown("---")

        # 「新しいバトルをはじめる」ボタンが押されたら状態をリセット
        st.markdown("### バトル終了後：つぎのバトル")
        if st.button("新しいバトルをはじめる"):
            reset_battle()

    # ローディング完了メッセージ
    status.update(label="じゅんび かんりょう！ バトル を はじめよう 🔥", state="complete")