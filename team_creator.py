# -*- coding: utf-8 -*-
import streamlit as st
import base64
import json
import os
import time
from ui_components import IMAGE_OPTIONS, TYPE_IMAGE_OPTIONS, prepare_base64_images, show_icon, render_monster_card, show_label, render_icon_selector
from team_editor import load_saved_teams

# セーブ先の宣言
SAVE_PATH = "saved_teams.json"

# base64画像を準備
TYPE_IMAGE_BASE64 = prepare_base64_images(TYPE_IMAGE_OPTIONS)
IMAGE_BASE64 = prepare_base64_images(IMAGE_OPTIONS)

# 初期化
def initialize_team_creator_state():
    if "selected_monster" not in st.session_state:
        st.session_state["selected_monster"] = 1
    if "selected_target" not in st.session_state:
        st.session_state["selected_target"] = "タイプ1"
    if "saved_monsters" not in st.session_state:
        st.session_state["saved_monsters"] = {}
    if "set_teamname" not in st.session_state:
        st.session_state["set_teamname"] = ""


# 現在選択中のモンスターの入力内容をセッションの保存データに反映
def set_selected_monster():

    # 編集対象のモンスター番号を取得
    i = st.session_state["selected_monster"]

    # モンスターの各種情報取得してセッションの保存領域に格納（辞書形式）（未選択時は"未"）
    st.session_state["saved_monsters"][i] = {
        "名前": st.session_state.get(f"name{i}") or "未",
        "タイプ": [st.session_state.get(f"types{i}_0") or "未",
                   st.session_state.get(f"types{i}_1") or "未"
        ],
        "画像": st.session_state.get(f"selected_image{i}") or "未",
        "わざ": [st.session_state.get(f"selected_move_image{i}_1") or "未",
                 st.session_state.get(f"selected_move_image{i}_2") or "未",
                 st.session_state.get(f"selected_move_image{i}_3") or "未"
        ]
    }

# 選択中（タイプ1～スペシャルわざ）の項目を強調するラベル
def render_target_label(monster_index, target_options, target_map, type_image_base64):
    
    # 現在選択中の編集対象（タイプ1～スペシャルわざ2）を取得
    selected_target = st.session_state["selected_target"]

    # 編集対象の数だけ横並びのカラムを作成
    cols = st.columns(len(target_options))
    
    # 選択中のラベルを強調表示
    for idx, label in enumerate(target_options):
        with cols[idx]:
            is_selected = (selected_target == label)
            bg_color = "#ffccdd" if is_selected else "#eeeeee"
            border = "2px solid #ff6699" if is_selected else "1px solid #cccccc"
            st.markdown(
                f"""
                <div style="background-color:{bg_color}; border:{border}; border-radius:6px; padding:6px; text-align:center;">
                    <span style="font-size:12px;">{label}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            # ラベルに対応するデータ種別（types or move）とスロット番号を取得
            kind, slot_index, _ = target_map[label]
            key = f"types{monster_index}_{slot_index}" if kind == "types" else f"selected_move_image{monster_index}_{slot_index}"
            
            # セッションにキーがなければ初期化（None）
            st.session_state.setdefault(key, None)

            # 現在選択されているタイプや技のラベルを取得
            selected_label = st.session_state[key]

             # タイプが選択されている場合：タイプ画像とラベルを表示
            if selected_label and selected_label in type_image_base64:
                img_base64 = type_image_base64[selected_label]
                st.markdown(
                    f"""
                    <div style="text-align:center; margin-top:6px;">
                        <img src="data:image/png;base64,{img_base64}" width="40"><br>
                        <div style="font-size:10px;">{selected_label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else: # ラベルが未選択の場合：未選択と表示
                st.markdown("<div style='text-align:center; font-size:10px;'>未選択</div>", unsafe_allow_html=True)
            
            # 編集ボタン
            if st.button("編集する", key=f"target_btn_{monster_index}_{slot_index}_{label}"):
                st.session_state["selected_target"] = label
                st.rerun()


# モンスターに設定された設定のプレビューと編集ボタン表示（タイプ1～スペシャルわざ2）
def render_monster_preview(i, selected_index, type_image_base64, image_base64):
    """
    　　n体目（選択中は枠を強調）
    　　　　　モンスター名
    モンスター画像　タイプアイコン1
    　　　　　　　　タイプアイコン2

    ノーマル技
    　　　　　タイプアイコン
    スペシャルわざ
    　　　　タイプアイコン2つ

    """
    # 選択中なら session_state から直接取得して表示
    if i == selected_index:
        mon = {
            "名前": st.session_state.get(f"name{i}", "未"),
            "画像": st.session_state.get(f"selected_image{i}", "未"),
            "タイプ": [
                st.session_state.get(f"types{i}_0", "未"),
                st.session_state.get(f"types{i}_1", "未")
            ],
            "わざ": [
                st.session_state.get(f"selected_move_image{i}_1", "未"),
                st.session_state.get(f"selected_move_image{i}_2", "未"),
                st.session_state.get(f"selected_move_image{i}_3", "未")
            ]
        }
    else:
        # 非選択中は保存済みデータを表示
        mon = st.session_state["saved_monsters"].get(i, {
            "名前": "未",
            "タイプ": ["未", "未"],
            "画像": "未",
            "わざ": ["未", "未", "未"]
        })

    # モンスター「n体目」のラベル表示（中央揃え＋選択中ならピンク）
    bg_color = "#ffccdd" if i == selected_index else "#eeeeee" # 選択中ならピンク、それ以外はグレーの背景色を設定
    border = "2px solid #ff6699" if i == selected_index else "1px solid #cccccc"# 選択中なら太枠、それ以外は細枠を設定
    st.markdown(
        f"""
        <div style="background-color:{bg_color}; border:{border}; border-radius:6px; padding:6px; text-align:center;">
            <span style="font-size:18px; font-weight:bold;">{i}体目</span>
        </div>
        """, unsafe_allow_html=True)

    # モンスターカード表示（画像・タイプ・わざ）
    render_monster_card(mon, type_image_base64, image_base64)
    return mon

# n体目の編集ボタンと切替処理
def handle_monster_edit(i):

    # 現在選択中のモンスターと異なる場合のみ処理を実行
    if i != st.session_state["selected_monster"]:
       if st.button(f"{i}体目を編集する", key=f"setup_monster_{i}"):

            # 現在編集中のモンスター情報を保存
            set_selected_monster()

            #　選択されたモンスターの処理へ
            st.session_state["selected_monster"] = i

            #　編集対象の項目を「タイプ1」に設定
            st.session_state["selected_target"] = "タイプ1"
            st.rerun()

# 3体分のプレビューと編集ボタン
def render_monster_list(num=3, type_image_base64=None, image_base64=None):

    # すべてのモンスターが設定済みかどうかを判定するフラグ
    all_ready = True

    # モンスター数に応じて横並びのカラムを作成
    cols = st.columns(num)

    # 各モンスター（1体目〜n体目）に対してループ処理
    for i in range(1, num + 1):
        with cols[i - 1]:

            # モンスターのプレビューを表示して保存済みデータを取得
            saved = render_monster_preview(i, st.session_state["selected_monster"], type_image_base64, image_base64)
            
            # 名前または画像が「未」の場合は未設定とみなす
            if saved["名前"] == "未" or saved["画像"] == "未":
                all_ready = False

            # n体目の編集切り替えボタンを表示
            handle_monster_edit(i)
    return all_ready

# セーブ前のエラーチェック
def validate_team_data():
    team_name = st.session_state.get("set_teamname", "").strip()
    saved_monsters = st.session_state.get("saved_monsters", {})
    errors = []

    # チーム名チェック
    if not team_name:
        errors.append("チーム名を入力してください")

    # モンスターごとのチェック
    for i in range(1, 4):
        mon = saved_monsters.get(i)
        if not mon:
            errors.append(f"{i}体目のモンスターが未設定です")
            continue

        name = mon["名前"]
        image = mon["画像"]
        moves = mon["わざ"]
        types = mon.get("タイプ", ["未", "未"])

        if name == "未":
            errors.append(f"{i}体目のモンスターの名前を入力してください")
        if image == "未":
            errors.append(f"{i}体目のモンスターの画像を選択してください")

        # タイプ1・2の両方が未設定ならエラー
        if types[0] == "未" and types[1] == "未":
            errors.append(f"{i}体目のモンスターのタイプを最低1つは選択してください")

        # 通常技は必須
        if moves[0] == "未":
            errors.append(f"{i}体目のモンスターの通常わざを選択してください")

        # スペシャルわざ1・2のどちらも未選択ならエラー
        if moves[1] == "未" and moves[2] == "未":
            errors.append(f"{i}体目のモンスターのスペシャルわざを最低1つは選択してください")

        # タイプ1・2が同じ場合（未設定以外）
        if types[0] != "未" and types[0] == types[1]:
            errors.append(f"{i}体目のモンスターのタイプ1とタイプ2が同じです。異なるタイプを選択してください")

    return errors

# チーム情報を保存ファイルに書込
def save_team(save_path):

    # 現在編集中のモンスター情報をセッションに保存（最後の編集内容を反映）
    set_selected_monster()

    # チーム名をセッションから取得
    team_name = st.session_state.get("set_teamname")

    # 保存済みのモンスター情報を取得
    team_data = st.session_state.get("saved_monsters", {})

    # チーム全体のデータ構造を作成（辞書形式）
    team = {"チーム名": team_name, "モンスター": team_data}

    # 保存ファイルが存在する場合：既存のチームデータを読込
    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            saved = json.load(f)

    # 存在しない場合：空のリストとして初期化
    else:
        saved = []

    if len(saved) >= 2:
        st.warning("保存できるチームは最大2件までです")
    else:
        saved.append(team)

        # 保存ファイルにチーム一覧を上書き保存
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(saved, f, ensure_ascii=False, indent=2)

        # 保存完了メッセージを表示
        st.success(f"チーム「{team_name}」を保存しました！5秒後にページを初期化します")

        # 5秒後に初期化処理(上限時の案内がすぐに出るのを防止)
        time.sleep(5)

        # 新規設定できるようにセッション情報をリセット
        for i in range(1, 4):
            for key in [f"name{i}", f"selected_image{i}"] + [f"types{i}_{j}" for j in range(2)] + [f"selected_move_image{i}_{k}" for k in range(1, 4)]:
                st.session_state.pop(key, None)

        st.session_state["saved_monsters"] = {}
        st.session_state["selected_monster"] = 1
        st.session_state["selected_target"] = "タイプ1"
        st.session_state.pop("set_teamname", None)
        st.session_state.clear()

        # ページを再描画して初期状態に戻す
        st.rerun()

# 【メイン】チーム選択ページ
def render_team_creator():

    # ローディング
    with st.status("データ を よみこみチュウ ... ⚡", expanded=True) as status:
        st.title("新規チーム作成")
        st.markdown(
            """
            ここでは、バトルに使うモンスター3体を選んで、自分のチームを作成・保存できます。  <br>
            名前やタイプ、わざなどを設定して、バトルに備えましょう！<br><br>
            <h3>◆チームの作り方</h3>
            1. まずは1体目のモンスターから、名前・タイプ・わざを順番に設定<br>
            2. 「n体目を編集する」ボタンで、2体目・3体目も同じように設定<br>
            3. 3体すべての設定が終わったら、チーム名を入力<br>
            4. 内容に問題なければ「チームを保存する」ボタンをクリックして登録完了！<br><br>
            """,
            unsafe_allow_html=True
        )
        # 保存済みチームの読み込み
        saved_teams = load_saved_teams()

        # チーム数が上限の場合：作成不可として案内を表示
        if len(saved_teams) >= 2:
            st.info("""
                    すでにチームが2件登録されています。  
                    新しいチームを作成するには、左の「チーム選択・削除」ページで不要なチームを削除してください。  
                    または、登録済みのチームを使って「バトル判定」ページでバトルをしてください。
            """)
            # ローディング完了メッセージ
            status.update(label="チーム が いっぱい です ... 🌀", state="complete")
            return

        # 初期化
        initialize_team_creator_state()
        selected_monster = st.session_state["selected_monster"]
        selected_target = st.session_state["selected_target"]

        # 編集対象の定義
        target_options = ["タイプ1", "タイプ2", "ノーマルわざ", "スペシャルわざ1", "スペシャルわざ2"]
        target_map = {
            "タイプ1": ("types", 0, True),
            "タイプ2": ("types", 1, False),
            "ノーマルわざ": ("move", 1, True),
            "スペシャルわざ1": ("move", 2, True),
            "スペシャルわざ2": ("move", 3, False)
        }
        st.markdown("---")

        # 編集対象のモンスター番号
        selected_monster = st.session_state["selected_monster"]

        # 保存済みの名前があれば復元する
        saved_name = st.session_state["saved_monsters"].get(selected_monster, {}).get("名前")
        if saved_name and saved_name != "未":
            st.session_state.setdefault(f"name{selected_monster}", saved_name)

        # 名前入力
        st.markdown(f"#### 1. {selected_monster}匹目のモンスターの名前を入力してください")
        st.text_input("▼ 名前を入力", key=f"name{selected_monster}", placeholder="例：ピカ―ドン")
        st.markdown("---")

        # ローディング用メッセージ
        status.update(label="モンスター を ひょうじチュウ...⚡")

        # モンスター画像選択
        image_key = f"selected_image{selected_monster}"
        st.session_state.setdefault(image_key, None)

        render_icon_selector(label_list=list(IMAGE_OPTIONS.keys()), base64_dict=IMAGE_BASE64, selected_labels=[st.session_state.get(image_key)], session_keys=(image_key,), max_select=1, title=f"2. {selected_monster}匹目のモンスターのアイコンを選択してください（表示のみ）", image_width=60, columns_per_row=9, highlight_color="#00ccff", border_color="#007BFF", show_label=False, rerun_on_select=True)
        st.markdown("---")

        # ローディング用メッセージ
        status.update(label="タイプアイコン を ひょうじチュウ...⚡")

        # タイプ・わざ選択（画像は共通で利用）
        kind, slot_index, required = target_map[selected_target]
        key = f"types{selected_monster}_{slot_index}" if kind == "types" else f"selected_move_image{selected_monster}_{slot_index}"
        st.session_state.setdefault(key, None)
        render_icon_selector(label_list=list(TYPE_IMAGE_OPTIONS.keys()), base64_dict=TYPE_IMAGE_BASE64, selected_labels=[st.session_state.get(key)], session_keys=(key,), max_select=1, title=f"3. {selected_monster}匹目のモンスターの「{selected_target}」のタイプを選択してください", image_width=40, columns_per_row=9, highlight_color="#00ccff", border_color="#007BFF", show_label=True, rerun_on_select=True, select_key_prefix=f"select_{selected_monster}_{selected_target}", unselect_key_prefix=f"unselect_{selected_monster}_{selected_target}")

        # 編集対象ボタン（タイプ1～スペシャルわざ2）
        render_target_label(selected_monster, target_options, target_map, TYPE_IMAGE_BASE64)
        st.markdown("「編集する」ボタンをクリックして各種タイプを編集してください")
        st.markdown("---")

        # ローディング用メッセージ
        status.update(label="プレビュー を ひょうじチュウ...⚡")

        # モンスター一覧表示
        st.markdown("#### 4. モンスターの設定をしてください")
        all_ready = render_monster_list(3, TYPE_IMAGE_BASE64, IMAGE_BASE64)
        st.markdown("未設定のモンスターの「n体目を編集する」ボタンをクリックして再度上から設定を行ってください")
        st.markdown("---")

        # チーム名入力
        st.markdown("#### ★ モンスター3体設定後： チーム名を入力してください")
        st.text_input("▼ チーム名を入力", key="set_teamname", placeholder="例：〇〇タイプチーム")
        st.markdown("---")

        # 保存
        st.markdown("#### 最後に：チームを保存してください")
        st.markdown("▼ 内容に問題がなければ保存ボタンをクリックしてください")

        if st.button("チームを保存する", key="final_save"):
            set_selected_monster()
            errors = validate_team_data()

            if errors:
                st.warning("修正が必要な項目があります。以下の項目を確認してください：")
                for msg in errors:
                    st.markdown(f"- {msg}")
            else:
                save_team(SAVE_PATH)


        # ローディング完了メッセージ
        status.update(label="じゅんび かんりょう！チームを つくろう ✊", state="complete")