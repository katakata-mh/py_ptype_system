# -*- coding: utf-8 -*-
import json
import streamlit as st

# タイプ相性(JSON)を読み込む
with open("type_chart.json", encoding="utf-8") as f:
    type_chart = json.load(f)

# 倍率をラベル文字に置き換える
def get_label(attackvalue):
    if attackvalue >= 2.56:
        return "◎ ばつぐん"
    elif 1.59 <= attackvalue < 2.56:
        return "〇 ばつぐん"
    elif 0.99 <= attackvalue < 1.59:
        return "◇ ふつう"
    elif 0.61 <= attackvalue < 0.99:
        return "△ いまひとつ"
    elif 0.38 <= attackvalue < 0.61:
        return "▲ いまひとつ"
    elif attackvalue < 0.38:
        return "× ほぼこうかなし"
    else:
        return f"{attackvalue:.2f}倍"

# 自分のモンスターのわざに対して相手のモンスター（単一タイプと複合タイプ）への攻撃倍率の計算
def get_effectiveness(attacker_type, enemy_types, type_chart):

    # 攻撃タイプに対応する相性データを取得
    data = type_chart.get(attacker_type, {})
    attackvalue = 1.0

    # enemy_types が文字列の場合：リストに変換して統一処理
    if isinstance(enemy_types, str):
        enemy_types = [enemy_types]

    # "未" を除いた有効タイプだけ抽出
    valid_types = [t for t in enemy_types if t != "未"]

    # 有効タイプが1つだけの場合：単一タイプとして処理
    if len(valid_types) == 1:
        defender = valid_types[0]
        found = False

        # 相性表から該当タイプの倍率を探す
        for key, type_list in data.items():
            if defender in type_list:

                # "等倍" は1.0、それ以外は数値に変換して倍率に設定
                value = 1.0 if key == "等倍" else float(key)
                attackvalue = value
                found = True
                break

        # 該当タイプが相性表に存在しない場合は等倍扱い
        if not found:
            attackvalue = 1.0

    # 有効タイプが2つある場合：複合タイプとして倍率を掛け合わせる
    elif len(valid_types) == 2:
        for defender in valid_types:
            found = False

            # 各タイプに対して倍率を取得し掛け算
            for key, type_list in data.items():
                if defender in type_list:
                    value = 1.0 if key == "等倍" else float(key)
                    attackvalue *= value
                    found = True
                    break

            # 該当タイプが相性表に存在しない場合：等倍扱い
            if not found:
                attackvalue *= 1.0  # 未定義なら等倍扱い

    # どちらも "未" だった場合：念のため等倍扱い
    else:
        attackvalue = 1.0

    # 最終倍率とそれに対応する評価ラベルを返す
    return attackvalue, get_label(attackvalue)

# 総合評価（モンスターの攻撃・防御をもとに総合評価スコアと記号・色を返す）
def calculation_totalscore(mon, enemy_types, type_chart):
    """
    評価式：
    総合評価 = ノーマルわざ倍率 × 1.2 + スペシャルわざ最大倍率 × 1.0 − 被ダメージ最大倍率 × 1.0

    ノーマルわざ：使用頻度が高いため重視
    スペシャルわざ：火力は高いがシールド（最大3回）で無効化される可能性あり
    相手のこうげき（減点）：相手のタイプをわざとして自分に与えるより大きいダメージで計算（仮定）
    """
    # ノーマルわざ（最初の1つ）倍率取得
    normal_move = mon["わざ"][0]
    normal_attackvalue = get_effectiveness(normal_move, enemy_types, type_chart)[0] if normal_move and normal_move != "なし" else 1.0

    # スペシャルわざ（後ろ2つ）→ 最大倍率を採用
    special_moves = mon["わざ"][1:]
    special_attackvalue = max(
        get_effectiveness(move, enemy_types, type_chart)[0]
        for move in special_moves if move and move != "なし"
    ) if any(move and move != "なし" for move in special_moves) else 1.0

    # 被ダメージ予測（相手のタイプが使うと仮定）
    incoming_attackvalue = max(
        get_effectiveness(enemy_type, mon["タイプ"], type_chart)[0]
        for enemy_type in enemy_types if enemy_type and enemy_type != "なし"
    ) if any(enemy_type and enemy_type != "なし" for enemy_type in enemy_types) else 1.0

    # 総合スコア計算
    total_score = normal_attackvalue * 1.2 + special_attackvalue * 1.0 - incoming_attackvalue * 1.0

    # スコアに応じた記号と色（最大値：5.24、最小値：-1.7 を想定）
    def get_total_mark(score):
        if score >= 2.5:
            return "◎", "#d00"
        elif score >= 1.4:
            return "〇", "#d00"
        elif score >= 1.0:
            return "◇", "#000"
        elif score >= 0.5:
            return "△", "#00a"
        elif score >= 0:
            return "▲", "#00a"
        else:
            return "×", "#00a"

    return total_score, *get_total_mark(total_score)

# 攻撃評価・防御予測を共通のUIで表示
def calculation_attack_defense_evaluation(title: str, items: list, target_types: list, type_icon_map: dict, type_chart: dict, is_attack: bool = True):
    """
    攻撃評価・防御予測の共通表示関数。
    - title: 表示タイトル（例："攻撃評価"）
    - items: わざやタイプのリスト（攻撃なら mon["わざ"], 防御なら enemy_types）
    - target_types: 対象となるタイプ（攻撃なら enemy_types, 防御なら mon["タイプ"]）
    - is_attack: Trueなら攻撃評価、Falseなら防御予測
    """

    # 最良倍率の初期値を設定（攻撃なら低く、防御なら高く）
    best_attackvalue = -1
    best_label = None
    evaluations = []

    # タイプやわざが未設定の場合：表示しない
    if (not target_types or all(t == "不明" or t is None for t in target_types)
        or not items or all(item == "なし" or item not in type_icon_map for item in items)
        ):
            return

    # 各わざやタイプに対して倍率と評価ラベルを計算
    for item in items:
        if item and item != "なし" and item in type_icon_map:
            attackvalue, label = get_effectiveness(item, target_types, type_chart)
            evaluations.append((item, attackvalue, label))

            # 最大倍率を探す
            if attackvalue > best_attackvalue:
                best_attackvalue = attackvalue
                best_label = label

    # 評価が1件もない場合：表示せず終了
    if not evaluations:
        return

    # # 最良倍率に応じた記号と色を返す関数（攻撃と防御で異なる）
    def get_mark_and_color(attackvalue):
        if is_attack:
            if best_attackvalue < 0.38:
                return "×", "#d00"
            elif 0.38 <= attackvalue < 0.61:
                return "▲", "#00a"
            elif 0.61 <= attackvalue < 0.99:
                return "△", "#00a"
            elif 0.99 <= attackvalue < 1.59:
                return "◇", "#000"
            elif 1.59 <= attackvalue < 2.56:
                return "〇", "#d00"
            else:
                return "◎", "#d00"
        else:
            if best_attackvalue < 0.38:
                return "◎", "#d00"
            elif 0.38 <= attackvalue < 0.75:
                return "●", "#d00"
            elif 0.75 <= attackvalue < 1.0:
                return "〇", "#000"
            elif 1.0 <= attackvalue < 1.59:
                return "◇", "#000"
            elif 1.59 <= attackvalue < 2.56:
                return "▲", "#00a"
            else:
                return "×", "#00a"

    # タイトルと評価記号を表示
    mark, mark_color = get_mark_and_color(best_attackvalue)
    st.markdown(
        f"<span style='font-size:18px; font-weight:bold;'>{title}：<span style='color:{mark_color};'>{mark}</span></span>",
        unsafe_allow_html=True
    )

    # こうかの色分け
    def get_label_color(attackvalue):
        try:
            attackvalue = round(attackvalue, 2)
        except (ValueError, TypeError):
            return "#000"
        if is_attack:
            # 攻撃評価：高いほど赤、低いほど青
            if attackvalue <= 0.5:
                return "#00a"
            elif attackvalue <= 1.0:
                return "#000"
            else:
                return "#d00"
        else:
            # 防御予測：高いほど赤、低いほど青
            if attackvalue <= 0.98:
                return "#d00"
            elif attackvalue <= 1.0:
                return "#000"
            else:
                return "#00a"

    # 各わざやタイプの評価をアイコン付きで表示
    for item, attackvalue, label in evaluations:
        color = get_label_color(attackvalue)
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:8px; font-size:16px;">
                <img src="data:image/png;base64,{type_icon_map[item]}" width="24">
                <span style="color:{color};">{label}{'（予測）' if not is_attack else ''}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# 評価方法についての説明（アコーディオン式）
def render_evaluation_guide():
    with st.expander("評価について", expanded=False):
        st.markdown("""
            **◇ マークや文字の色って？**  
            - 「わざのこうか」と「評価」で使われるマークや色には少し違いがあります  
            - わざ：どれだけ効果があるか（攻撃の強さ）  
            - 評価：自分にとって有利か不利か（バトルの有利度）
            <table>
            <tr><th>色</th><th>わざのこうか ／ 評価</th></tr>
            <tr><td style="color:#d00;">赤</td><td style="color:#d00;">こうかあり ／ 自分にとって有利</td></tr>
            <tr><td style="color:#000;">黒</td><td style="color:#000;">ふつう</td></tr>
            <tr><td style="color:#00a;">青</td><td style="color:#00a;">いまいち ／ 自分にとって不利</td></tr>
            </table>

            ---

            **◇ 総合評価とは？**  
            - 「ノーマルわざ」「スペシャルわざ」「防御の強さ」をもとに計算された総合スコアです  
            - 評価式：ノーマル倍率 × 1.2 + スペシャル最大倍率 × 1.0 − 被ダメージ最大倍率 × 1.0  
            - 攻撃力と防御力のバランスが良いほど高評価になります

            <table>
              <tr><th>マーク</th><th>スコア</th><th>評価</th></tr>
              <tr><td style="color:#d00;">◎</td><td style="color:#d00;">2.5 ～ 5.24</td><td style="color:#d00;">すごく つよい かも</td></tr>
              <tr><td style="color:#d00;">〇</td><td style="color:#d00;">1.4 ～ 2.49</td><td style="color:#d00;">つよい かも</td></tr>
              <tr><td style="color:#000;">◇</td><td style="color:#000;">1.0 ～ 1.39</td><td style="color:#000;">ふつう かも</td></tr>
              <tr><td style="color:#00a;">△</td><td style="color:#00a;">0.5 ～ 0.99</td><td style="color:#00a;">よわい かも</td></tr>
              <tr><td style="color:#00a;">▲</td><td style="color:#00a;">0.0 ～ 0.49</td><td style="color:#00a;">よわい かも</td></tr>
              <tr><td style="color:#00a;">×</td><td style="color:#00a;">-1.7 ～ -0.01</td><td style="color:#00a;">すごく よわい かも</td></tr>
            </table>

            ▽ 評価式の補足
            - ノーマルわざ：使用頻度が高いため重視
            - スペシャルわざ：火力は高いがシールドで無効化される可能性あり
            - 被ダメージ：相手のタイプをわざとして仮定し、最大ダメージを予測

            ---

            **◇ 攻撃評価とは？**  
            - 自分のわざが、相手のタイプにどれだけ効くかを評価します
            - 倍率が高いほど「こうかばつぐん」で、評価も高くなります

            <table>
            <tr><th>マーク</th><th>こうげき</th></tr>
            <tr><td style="color:#d00;">◎</td><td style="color:#d00;">かなり ばつぐん</td></tr>
            <tr><td style="color:#d00;">〇</td><td style="color:#d00;">ばつぐん</td></tr>
            <tr><td style="color:#000;">◇</td><td style="color:#000;">ふつう</td></tr>
            <tr><td style="color:#00a;">△／▲</td><td style="color:#00a;">いまひとつ</td></tr>
            <tr><td style="color:#00a;">×</td><td style="color:#00a;">ほぼ こうかなし</td></tr>
            </table>

            ---

            **◇ 防御予測とは？**  

            - 相手のわざは読みづらいため、相手のタイプをわざのタイプとして予測  
            - そのわざが自分にどれだけ効くかを評価します


            <table>
            <tr><th>マーク</th><th>ぼうぎょ</th></tr>
            <tr><td style="color:#d00;">◎</td><td style="color:#d00;">てっぺき かも</td></tr>
            <tr><td style="color:#d00;">〇</td><td style="color:#d00;">かたい かも</td></tr>
            <tr><td style="color:#000;">◇</td><td style="color:#000;">ふつう かも</td></tr>
            <tr><td style="color:#00a;">△／▲</td><td style="color:#00a;">うすい かも</td></tr>
            <tr><td style="color:#00a;">×</td><td style="color:#00a;">もろい かも</td></tr>
            </table>
            """, unsafe_allow_html=True)