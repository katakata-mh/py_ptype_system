import streamlit as st
import base64

# モンスター画像
IMAGE_OPTIONS = {
    "ほのお": "images/Fire_icon.png",
    "みず": "images/Water_icon.png",
    "くさ": "images/Grass_icon.png",
    "でんき": "images/Electric_icon.png",
    "こおり": "images/Ice_icon.png",
    "かくとう": "images/Fighting_icon.png",
    "ひこう": "images/Flying_icon.png",
    "エスパー": "images/Psychic_icon.png",
    "むし": "images/Bug_icon.png",
    "どく": "images/Poison_icon.png",
    "じめん": "images/Ground_icon.png",
    "いわ": "images/Rock_icon.png",
    "ゴースト": "images/Ghost_icon.png",
    "ドラゴン": "images/Dragon_icon.png",
    "あく": "images/Dark_icon.png",
    "はがね": "images/Steel_icon.png",
    "フェアリー": "images/Fairy_icon.png",
    "ノーマル": "images/Normal_icon.png",
}
# わざ画像
TYPE_IMAGE_OPTIONS = {
    "ほのお": "move_icons/Fire_move.png",
    "みず": "move_icons/Water_move.png",
    "くさ": "move_icons/Grass_move.png",
    "でんき": "move_icons/Electric_move.png",
    "こおり": "move_icons/Ice_move.png",
    "かくとう": "move_icons/Fighting_move.png",
    "ひこう": "move_icons/Flying_move.png",
    "エスパー": "move_icons/Psychic_move.png",
    "むし": "move_icons/Bug_move.png",
    "どく": "move_icons/Poison_move.png",
    "じめん": "move_icons/Ground_move.png",
    "いわ": "move_icons/Rock_move.png",
    "ゴースト": "move_icons/Ghost_move.png",
    "ドラゴン": "move_icons/Dragon_move.png",
    "あく": "move_icons/Dark_move.png",
    "はがね": "move_icons/Steel_move.png",
    "フェアリー": "move_icons/Fairy_move.png",
    "ノーマル": "move_icons/Normal_move.png",
}

# 画像ファイルをbase64文字列に変換
@st.cache_data
def get_base64_image(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        return ""

# ラベルと画像パスの辞書を受け取り、base64変換した辞書を返す(例：{"ほのお": "base64文字列"})
def prepare_base64_images(option_dict):
    result = {}
    for label, path in option_dict.items():
        try:
            base64_str = get_base64_image(path)
            if base64_str:
                result[label] = base64_str
        except Exception as e:
            print(f"画像読み込み失敗: {label} → {e}")

    return result

# ラベルに対応するbase64画像とラベル名を中央揃えで表示
def render_icon_with_label(label, base64_dict, width=32, font_size=10, fallback="未設定", show_label=True):
    try:
        img_base64 = base64_dict.get(label)
        if img_base64:
            label_html = f"<span style='font-size:{font_size}px;'>{label}</span>" if show_label else ""
            st.markdown(
                f"""
                <div style="text-align:center;">
                    <img src="data:image/png;base64,{img_base64}" width="{width}"><br>
                    {label_html}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='text-align:center; color:gray;'>{fallback}</div>",
                unsafe_allow_html=True
            )
    except Exception as e:
        st.error(f"表示エラー: {e}")
        st.write(f"ラベル: {label}")


# モンスター情報を表示する
def render_monster_card(mon, type_icon_map, image_base64_map, image_width=80, icon_width=24):
    """
    　　　　　モンスター名
    モンスター画像　タイプアイコン1
    　　　　　　　　タイプアイコン2

    ノーマル技
    　　　　　タイプアイコン
    スペシャルわざ
    　　　　タイプアイコン2つ
    """
    name = mon.get("名前", "未設定")
    image_label = mon.get("画像", "未")
    types = mon.get("タイプ", ["未", "未"])
    moves = mon.get("わざ", ["なし", "なし", "なし"])

    try:
        # 中央ぞろえでモンスター名表示(長い名前ように折り返し対策)
        st.markdown(f"<div style='text-align: center;font-weight: bold;font-size: 18px;word-wrap: break-word;white-space: normal;'>{name}</div>""",unsafe_allow_html=True)

        # モンスター画像とタイプ1・タイプ2を横並びで表示
        cols = st.columns([1, 2])
        with cols[0]:
            render_icon_with_label(image_label, image_base64_map, width=200, show_label=False)
        with cols[1]:
            for t in types:
                render_icon_with_label(t, type_icon_map, width=icon_width, font_size=10)

        # ノーマルわざ（画像＋ラベル表示）
        st.markdown("◆ ノーマルわざ：")
        render_icon_with_label(moves[0], type_icon_map)

        # スペシャルわざ1・2（横並び）
        st.markdown("◆ スペシャルわざ：")
        specials = moves[1:3] if len(moves) >= 3 else ["なし", "なし"]
        cols = st.columns(2)
        for i in range(2):
            with cols[i]:
                render_icon_with_label(specials[i], type_icon_map)
    except Exception as e:
        st.error(f"モンスター表示中にエラーが発生しました: {e}")
        st.write(mon)


# 画像の下のテキストラベルを中央揃えで表示する
def show_label(text):
    st.markdown(f"<div style='text-align:center;'>{text}</div>", unsafe_allow_html=True)

# 選択された画像とラベルを表示する
def show_icon(label, base64_dict, size=40, show_label_text=True):

    # ラベルがNone, 空文字, "未" のどれかなら未設定として処理
    if not label or label == "未" or label not in base64_dict:
        show_label("未")
        return

    # ラベル表示が必要な場合：小さい文字でラベルをつける
    label_html = f"<div style='font-size:10px;'>{label}</div>" if show_label_text else ""

    # base64画像データを辞書から取得
    img_base64 = base64_dict.get(label)

    # 画像とラベルを中央揃えで表示
    st.markdown(
        f"""
        <div style="text-align:center;">
            <img src="data:image/png;base64,{base64_dict[label]}" width="{size}">
            {label_html}
        </div>
        """,
        unsafe_allow_html=True
    )

# ひんし状態や選択状態に応じたモンスター画像表示
def render_monster_image_battlestate(image_base64: str, width: int = 80, darken: bool = False, highlight: bool = False):
    style = ""

    # ひんし状態なら暗く表示
    if darken:
        style += "filter: brightness(40%);"

    # 選択状態ならピンク枠で強調表示
    if highlight:
        style += "border: 3px solid pink; border-radius: 8px; padding: 2px;"
    
    # 上のスタイル設定に応じた画像を表示
    st.markdown(
        f"""
        <div style="{style} width:{width}px; display:inline-block;">
            <img src="data:image/png;base64,{image_base64}" width="{width}">
        </div>
        """,
        unsafe_allow_html=True
    )

# タイプアイコンを縦に表示
def render_type_icons(type_list: list, icon_map: dict, width: int = 24):
    valid_types = [t for t in type_list if t and t != "なし" and t in icon_map]

    # 有効なタイプがある場合：画像表示
    if valid_types:
        for t in valid_types:
            st.image(f"data:image/png;base64,{icon_map[t]}", width=width)
    
    # 有効なタイプがない場合：案内メッセージを表示
    else:
        st.markdown("<span style='color:gray;'>上部からタイプを選択してください</span>", unsafe_allow_html=True)

# 画像選択UI(タイプアイコンやモンスター画像の選択)
def render_icon_selector(label_list, base64_dict, selected_labels, session_keys, max_select=1, title="画像を選択してください", image_width=60, columns_per_row=9,
    highlight_color="#00ccff", border_color="#007BFF", show_label=True, select_key_prefix="select", unselect_key_prefix="unselect", rerun_on_select=True ):

    st.markdown(f"#### {title}")
    rows = [label_list[i:i+columns_per_row] for i in range(0, len(label_list), columns_per_row)]

    for row in rows:
        cols = st.columns(len(row))
        for i, label in enumerate(row):
            with cols[i]:
                selected = label in selected_labels
                border = f"3px solid {highlight_color}" if selected else "1px solid transparent"
                label_html = f"<div style='font-size:10px; white-space:nowrap;'>{label}</div>" if show_label else ""

                img_base64 = base64_dict.get(label, "")
                st.markdown(
                    f"""
                    <div style="border:{border}; border-radius:8px; padding:4px; text-align:center;">
                        <img src="data:image/png;base64,{img_base64}" width="{image_width}"><br>
                        {label_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # ボタン処理（選択されたら解除ボタンに変更する）
                if selected:
                    if st.button("解除", key=f"{unselect_key_prefix}_{label}_{i}"):
                        for key in session_keys:
                            if st.session_state.get(key) == label:
                                st.session_state[key] = None
                        if rerun_on_select:
                            st.rerun()
                else:
                    if st.button("選択", key=f"{select_key_prefix}_{label}_{i}"):
                        for key in session_keys:
                            if st.session_state.get(key) is None:
                                st.session_state[key] = label

                                # 編集中のモンスター情報を即座に保存
                                if rerun_on_select:
                                    st.rerun()
                                return
                        st.warning(f"最大{max_select}つまで選択できます")

