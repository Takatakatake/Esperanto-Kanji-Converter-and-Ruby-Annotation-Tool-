import streamlit as st
import pandas as pd
import io
import os
import re
import json
import unicodedata

# # 字上符付き文字の表記形式変換用の辞書型配列
# x_to_circumflex = {'cx': 'ĉ', 'gx': 'ĝ', 'hx': 'ĥ', 'jx': 'ĵ', 'sx': 'ŝ', 'ux': 'ŭ','Cx': 'Ĉ', 'Gx': 'Ĝ', 'Hx': 'Ĥ', 'Jx': 'Ĵ', 'Sx': 'Ŝ', 'Ux': 'Ŭ'}
# circumflex_to_x = {'ĉ': 'cx', 'ĝ': 'gx', 'ĥ': 'hx', 'ĵ': 'jx', 'ŝ': 'sx', 'ŭ': 'ux','Ĉ': 'Cx', 'Ĝ': 'Gx', 'Ĥ': 'Hx', 'Ĵ': 'Jx', 'Ŝ': 'Sx', 'Ŭ': 'Ux'}
# x_to_hat = {'cx': 'c^', 'gx': 'g^', 'hx': 'h^', 'jx': 'j^', 'sx': 's^', 'ux': 'u^','Cx': 'C^', 'Gx': 'G^', 'Hx': 'H^', 'Jx': 'J^', 'Sx': 'S^', 'Ux': 'U^'}
# hat_to_x = {'c^': 'cx', 'g^': 'gx', 'h^': 'hx', 'j^': 'jx', 's^': 'sx', 'u^': 'ux','C^': 'Cx', 'G^': 'Gx', 'H^': 'Hx', 'J^': 'Jx', 'S^': 'Sx', 'Ux': 'Ux'}
# hat_to_circumflex = {'c^': 'ĉ', 'g^': 'ĝ', 'h^': 'ĥ', 'j^': 'ĵ', 's^': 'ŝ', 'u^': 'ŭ','C^': 'Ĉ', 'G^': 'Ĝ', 'H^': 'Ĥ', 'J^': 'Ĵ', 'S^': 'S^', 'U^': 'Ŭ'}
# circumflex_to_hat = {'ĉ': 'c^', 'ĝ': 'g^', 'ĥ': 'h^', 'ĵ': 'j^', 'ŝ': 's^', 'ŭ': 'u^','Ĉ': 'C^', 'Ĝ': 'G^', 'Ĥ': 'H^', 'Ĵ': 'J^', 'Ŝ': 'S^', 'Ŭ': 'U^'}

# # 字上符付き文字の表記形式変換用の関数
# def replace_esperanto_chars(text,letter_dictionary):
#     for esperanto_char, x_char in letter_dictionary.items():
#         text = text.replace(esperanto_char, x_char)
#     return text

# 事前に作成した Unicode_BMP全范围文字幅(宽)_Arial16.json ファイルを読み込み
with open("./files_needed_to_get_replacements_list_json_format/Unicode_BMP全范围文字幅(宽)_Arial16.json", "r", encoding="utf-8") as fp:
    char_widths_dict = json.load(fp)

def measure_text_width_Arial16(text, char_widths_dict):
    """
    JSONで読み込んだ  {文字: 幅(px)} の辞書 (char_widths_dict) を用いて、
    与えられた文字列 text の幅を合計して返す。
    """
    total_width = 0
    for ch in text:
        # JSONにない文字の場合は幅 8 とみなす（または別の処理）
        char_width = char_widths_dict.get(ch, 8)
        total_width += char_width
    return total_width


def contains_digit(s):# 対象の文字列sに数字となりうる文字列(数字)が含まれるかどうかを確認する関数
    return any(char.isdigit() for char in s)

def import_placeholders(filename):# placeholder(占位符)をインポートするためだけの関数
    with open(filename, 'r') as file:
        placeholders = [line.strip() for line in file if line.strip()]
    return placeholders


# def capitalize_rt_tag(match):
def capitalize_ruby_and_rt(text):

    pattern = re.compile(
        r'^'              # 行頭／文字列頭
        r'(.*?)'          # グループ1: <ruby> より左側(外側)のテキスト
        r'(<ruby>)'       # グループ2: "<ruby>"
        r'([^<]+)'        # グループ3: "<ruby>"～"<rt" の間にある文字列　親要素(本文)
        r'(<rt[^>]*>)'    # グループ4: "<rt class="xxx"等 >"
        r'([^<]+)'        # グループ5: <rt>～</rt> の中身　子要素(ルビ部分)
        r'(</rt>)'        # グループ6: "</rt>"
        r'(</ruby>)?'     # グループ7: "</ruby>"
        r'(.*)'           # グループ8: 残り(この <ruby> ブロックの後ろのテキストすべて)
        r'$'              # 行末／文字列末
    )

    def replacer(match):
        g1 = match.group(1)# グループ1: <ruby> より左側(外側)のテキスト
        g2 = match.group(2)# グループ2: "<ruby>"
        g3 = match.group(3)# グループ3: "<ruby>"～"<rt" の間にある文字列　親要素(本文)
        g4 = match.group(4)# グループ4: "<rt class="xxx"等 >"
        g5 = match.group(5)# グループ5: <rt>～</rt> の中身　子要素(ルビ部分)
        g6 = match.group(6)# グループ6: "</rt>"
        g7 = match.group(7)# グループ7: "</ruby>"
        g8 = match.group(8)# グループ8: 残り(この <ruby> ブロックの後ろのテキストすべて)
        
        # 左側(外側)のテキストが空ではない場合 → 左側の先頭を大文字化
        if g1.strip():
            return g1.capitalize() + g2 + g3 + g4 + g5 + g6 + (g7 if g7 else "") + g8
        else:
            # 左側が空の場合 → <ruby> 内の親文字列/ルビ文字列を大文字化
            parent_text = g3.capitalize()
            rt_text = g5.capitalize()
            return g1 + g2 + parent_text + g4 + rt_text + g6 + (g7 if g7 else "") + g8

    replaced_text = pattern.sub(replacer, text)

    # もし置換が1箇所も行われなかった(=パターン不一致)なら、先頭を大文字化
    if replaced_text == text:
        replaced_text = text.capitalize()

    return replaced_text


# サンプルファイルのパス
file_path0 = './files_needed_to_get_replacements_list_json_format/韓国語訳ルビリスト_202501.csv'
# ファイルを読み込む
with open(file_path0, "rb") as file:
    btn = st.download_button(
            label="サンプル CSV ファイル 0 ダウンロード(韓国語翻訳ルビリスト)",
            data=file,
            file_name="韓国語翻訳ルビリスト_202501.csv",
            mime="text/csv"
        )
    
# サンプルファイルのパス
json_file_path = './files_needed_to_get_replacements_list_json_format/世界语单词词根分解法user设置.json'
# JSONファイルを読み込んでダウンロードボタンを生成
with open(json_file_path, "rb") as file_json:
    btn_json = st.download_button(
        label="サンプル JSON ファイル 1 ダウンロード(世界語単語語根分解法ユーザー設定)",
        data=file_json,
        file_name="世界语单词词根分解法user设置.json",
        mime="application/json"
    )

# サンプルエクセルファイルのダウンロードボタン
st.write("エスペラント語根に翻訳ルビを追加する難易度をユーザーが設定できるサンプル Excel ファイルです。これを活用して上記のサンプル形式と同様の CSV ファイルを作成してください。")
with open('./files_needed_to_get_replacements_list_json_format/E-Korea vortolisto kun lernado-nivelo.xlsx', "rb") as file:
    st.download_button(
        label="サンプル Excel ファイル ダウンロード: E-Korea vortolisto kun lernado-nivelo",
        data=file,
        file_name="E-Korea_vortolisto_kun_lernado-nivelo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ユーザーに出力形式を選択してもらう
def output_format(main_text, ruby_content, format_type):
    if format_type == 'HTML格式_Ruby文字_大小调整':
        if measure_text_width_Arial16(ruby_content, char_widths_dict)/measure_text_width_Arial16(main_text, char_widths_dict)>(10/4):# main_text(親要素)とruby_content(ルビ)の文字幅の比率に応じて、ルビサイズを6段階に分ける。
            return '<ruby>{}<rt class="ruby-XS_S_S">{}</rt></ruby>'.format(main_text, ruby_content)# "や'などの特殊文字については、jsonモジュールが自動的にエスケープして、正しく処理してくれるので心配無用。
        elif  measure_text_width_Arial16(ruby_content, char_widths_dict)/measure_text_width_Arial16(main_text, char_widths_dict)>(10/5):
            return '<ruby>{}<rt class="ruby-S_S_S">{}</rt></ruby>'.format(main_text, ruby_content)
        elif  measure_text_width_Arial16(ruby_content, char_widths_dict)/measure_text_width_Arial16(main_text, char_widths_dict)>(10/6):
            return '<ruby>{}<rt class="ruby-M_M_M">{}</rt></ruby>'.format(main_text, ruby_content)
        elif  measure_text_width_Arial16(ruby_content, char_widths_dict)/measure_text_width_Arial16(main_text, char_widths_dict)>(10/7):
            return '<ruby>{}<rt class="ruby-L_L_L">{}</rt></ruby>'.format(main_text, ruby_content)
        elif  measure_text_width_Arial16(ruby_content, char_widths_dict)/measure_text_width_Arial16(main_text, char_widths_dict)>(10/8):
            return '<ruby>{}<rt class="ruby-XL_L_L">{}</rt></ruby>'.format(main_text, ruby_content)
        else:
            return '<ruby>{}<rt class="ruby-XXL_L_L">{}</rt></ruby>'.format(main_text, ruby_content)
    elif format_type == 'HTML格式_Ruby文字_大小调整_汉字替换':
        if measure_text_width_Arial16(main_text, char_widths_dict)/measure_text_width_Arial16(ruby_content, char_widths_dict)>(10/4):# ruby_content(親要素)とmain_text(ルビ)の文字幅の比率に応じて、ルビサイズを6段階に分ける。
            return '<ruby>{}<rt class="ruby-XS_S_S">{}</rt></ruby>'.format(ruby_content, main_text)# "や'などの特殊文字については、jsonモジュールが自動的にエスケープして、正しく処理してくれるので心配無用。
        elif  measure_text_width_Arial16(main_text, char_widths_dict)/measure_text_width_Arial16(ruby_content, char_widths_dict)>(10/5):
            return '<ruby>{}<rt class="ruby-S_S_S">{}</rt></ruby>'.format(ruby_content, main_text)
        elif  measure_text_width_Arial16(main_text, char_widths_dict)/measure_text_width_Arial16(ruby_content, char_widths_dict)>(10/6):
            return '<ruby>{}<rt class="ruby-M_M_M">{}</rt></ruby>'.format(ruby_content, main_text)
        elif  measure_text_width_Arial16(main_text, char_widths_dict)/measure_text_width_Arial16(ruby_content, char_widths_dict)>(10/7):
            return '<ruby>{}<rt class="ruby-L_L_L">{}</rt></ruby>'.format(ruby_content, main_text)
        elif  measure_text_width_Arial16(main_text, char_widths_dict)/measure_text_width_Arial16(ruby_content, char_widths_dict)>(10/8):
            return '<ruby>{}<rt class="ruby-XL_L_L">{}</rt></ruby>'.format(ruby_content, main_text)
        else:
            return '<ruby>{}<rt class="ruby-XXL_L_L">{}</rt></ruby>'.format(ruby_content, main_text)
    elif format_type == 'HTML格式':
        return '<ruby>{}<rt>{}</rt></ruby>'.format(main_text, ruby_content)
    elif format_type == 'HTML格式_汉字替换':
        return '<ruby>{}<rt>{}</rt></ruby>'.format(ruby_content, main_text)
    elif format_type == '括弧(号)格式':
        return '{}({})'.format(main_text, ruby_content)
    elif format_type == '括弧(号)格式_汉字替换':
        return '{}({})'.format(ruby_content, main_text)
    elif format_type == '替换后文字列のみ(仅)保留(简单替换)':
        return '{}'.format(ruby_content)
    
# ユーザーに見せる選択肢（韓国語）→これを日本語表記に変更
options = {
    'HTML 형식＿루비 크기 조절': 'HTML格式_Ruby文字_大小调整',
    'HTML 형식＿루비 크기 조절(한자 교체)': 'HTML格式_Ruby文字_大小调整_汉字替换',
    'HTML 형식': 'HTML格式',
    'HTML 형식(한자 교체)': 'HTML格式_汉字替换',
    '괄호 형식': '括弧(号)格式',
    '괄호 형식(한자 교체)': '括弧(号)格式_汉字替换',
    '단순 치환 형식': '替换后文字列のみ(仅)保留(简单替换)'
}

# ユーザーに見せる選択肢を日本語で表示
display_options = list(options.keys())
# Streamlit の selectbox を表示（韓国語部分→日本語へ）
selected_display = st.selectbox('出力形式を選択:', display_options)

# 内部で使用する値を取得
format_type = options[selected_display]


# 例示
main_text = '汉字'
ruby_content = 'hanzi'
formatted_text = output_format(main_text, ruby_content, format_type)
st.write('フォーマット済みテキスト:', formatted_text)

# # Streamlitでファイルアップロード機能を追加（コメントアウト部分・韓国語→日本語へ変換）
# uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=['csv'])
# if uploaded_file is not None:
#     # Streamlitの環境でファイルを読み込むために必要な変更
#     input_csv_file = pd.read_csv(uploaded_file)
#     input_csv_file.to_csv("./files_needed_to_get_replacements_list_json_format/世界语词根列表＿user.csv", index=False)
#     st.success("CSVファイルがアップロードおよび保存されました。")

#     # ここで JSON アップロードを追加
#     st.write("---")
#     st.write("### JSONファイルアップロード (任意)")

#     # デフォルトで使用する JSON のパス
#     default_json_path = "./files_needed_to_get_replacements_list_json_format/世界语单词词根分解法user设置.json"
    
#     uploaded_json = st.file_uploader("JSONファイルをアップロードしてください", type=['json'])
    
#     if uploaded_json is not None:
#         # アップロードされた JSON を読み込む
#         change_dec = json.load(uploaded_json)

#         st.success("JSONファイルがアップロードおよび保存されました。")

#     else:
#         st.info("JSONファイルがアップロードされていません。デフォルト JSON を使用します。")
#         # アップロードがなければ、デフォルト JSON を読み込む
#         with open(default_json_path, "r", encoding="utf-8") as g:
#             change_dec = json.load(g)


# --- CSV アップロード or デフォルト使用 ---
csv_choice = st.radio("CSVファイルをどうしますか？", ("アップロードする", "デフォルトを使用する"))

csv_path_default = "./files_needed_to_get_replacements_list_json_format/世界语词根列表＿default.csv" 
    # ↑デフォルトとして使いたいCSVファイルのパス(例)

input_csv_file = None  # 後ほど使うために先に宣言

if csv_choice == "アップロードする":
    uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type=['csv'])
    if uploaded_file is not None:
        # アップロードされたCSVを読み込む
        input_csv_file = pd.read_csv(uploaded_file)
        st.success("CSVファイルがアップロードおよび保存されました。")
    else:
        st.warning("CSVファイルがアップロードされていません。")
        st.stop()
        # 「アップロードする」を選択したのにアップロードが無い場合、以降の処理を止める。
        
elif csv_choice == "デフォルトを使用する":
    try:
        input_csv_file = pd.read_csv(csv_path_default, encoding="utf-8")
        st.info("デフォルトの CSV を使用します。")
    except FileNotFoundError:
        st.error("デフォルトの CSV ファイルが見つかりません。処理を中断します。")
        st.stop()

# CSV がいずれにせよ input_csv_file に読み込まれた状態で次に進む
# --------------------------------------------------------------------------------------
st.write("---")
st.write("## JSONファイルをどうしますか？")

json_choice = st.radio("JSONファイルをどうしますか？", ("アップロードする", "デフォルトを使用する"))

json_path_default = "./files_needed_to_get_replacements_list_json_format/世界语单词词根分解法user设置.json"

change_dec = None  # JSON を格納

if json_choice == "アップロードする":
    uploaded_json = st.file_uploader("JSONファイルをアップロードしてください", type=['json'])
    if uploaded_json is not None:
        change_dec = json.load(uploaded_json)
        st.success("JSONファイルがアップロードおよび保存されました。")
    else:
        st.warning("JSONファイルがアップロードされていません。")
        st.stop()
elif json_choice == "デフォルトを使用する":
    # デフォルト JSON を読む
    try:
        with open(json_path_default, "r", encoding="utf-8") as g:
            change_dec = json.load(g)
        st.info("デフォルトの JSON を使用します。")
    except FileNotFoundError:
        st.error("デフォルトの JSON ファイルが見つかりません。処理を中断します。")
        st.stop()


with open("./files_needed_to_get_replacements_list_json_format/PEJVO(世界语全部单词列表)'全部'について、词尾(a,i,u,e,o,n等)をcutし、comma(,)で隔てて词性と併せて记录した列表(stem_with_part_of_speech_list).json", "r", encoding="utf-8") as g:
    stem_with_part_of_speech_list = json.load(g)

# 上の作業で抽出した、'PEJVO(世界语全部单词列表)'全部'について、词尾(a,i,u,e,o,n等)をcutし、comma(,)で隔てて词性と併せて记录した列表'(stem_with_part_of_speech_list)を文字列(漢字)置換するための、置換リストを作成していく。
# "'PEJVO(世界语全部单词列表)'全部'について、词尾(a,i,u,e,o,n等)をcutし、comma(,)で隔てて词性と併せて记录した列表'(stem_with_part_of_speech_list)を文字列(漢字)置換し終えたリスト"こそが最終的な置換リスト(replacements_final_list)の大元になる。
# '既に'/'(スラッシュ)によって完全に語根分解された状態の単語'が対象であれば、文字数の多い語根順に文字列(漢字)置換するだけで、理論上完璧な精度の置換ができるはず。
# ただし、その完璧な精度の置換のためにはあらかじめ"世界语全部单词列表_约44700个(原pejvo.txt)_utf8转换_第二部分以后重点修正_追加2024年版PEJVO更新项目_最终版202501.txt"から"世界语全部词根_约11148个_202501.txt"を抽出しておく必要がある。

# 一旦辞書型を使う。(後で内容(value)を更新するため)
temporary_replacements_dict={}
with open("./files_needed_to_get_replacements_list_json_format/世界语全部词根_约11148个_202501.txt", 'r', encoding='utf-8') as file:
    # "世界语全部词根_约11148个_202501.txt"は"世界语全部单词列表_约44700个(原pejvo.txt)_utf8转换_第二部分以后重点修正_追加2024年版PEJVO更新项目_最终版202501.txt"から"世界语全部词根_约11148个_202501.txt"を抽出したエスペラントの全語根である。
    roots = file.readlines()
    for root in roots:
        root = root.strip()
        if not root.isdigit():# 混入していた数字の'10'と'7'を削除
            temporary_replacements_dict[root]=[root,len(root)]# 各エスペラント語根に対する'置換後の文字列'(この作業では元の置換対象の語根のまま)と、その置換優先順序として、'置換対象の語根の文字数'を設定。　置換優先順序の数字が大きい('置換対象の語根の文字数'が多い)ほど、先に置換されるようにする。

##上の作業に引き続き、"'単語の語尾だけをカットした、完全に語根分解された状態の全単語リスト'(result)を漢字置換するための、漢字置換リスト"を作成していく。　
##ここでは自分で作成したエスペラント語根の漢字化リストを反映させる。

for _, (E_root, hanzi_or_meaning) in input_csv_file.iterrows():
    if pd.notna(E_root) and pd.notna(hanzi_or_meaning) and '#' not in E_root:  # 条件を満たす行のみ処理
        temporary_replacements_dict[E_root] = [output_format(E_root, hanzi_or_meaning, format_type),len(E_root)]
            
# 辞書型をリスト型に戻した上で、文字数順に並び替え。
# "'PEJVO(世界语全部单词列表)'全部'について、词尾(a,i,u,e,o,n等)をcutし、comma(,)で隔てて词性と併せて记录した列表'(stem_with_part_of_speech_list)を文字列(漢字)置換するための、置換リスト"を置換優先順位の数字の大きさ順(ここでは文字数順)にソート。

temporary_replacements_list_1=[]
for old,new in temporary_replacements_dict.items():
    temporary_replacements_list_1.append((old,new[0],new[1]))
temporary_replacements_list_2 = sorted(temporary_replacements_list_1, key=lambda x: x[2], reverse=True)

# '置換リスト'の各置換に対してplaceholder(占位符)を追加し、リスト'temporary_replacements_list_final'として完成させる。
imported_placeholders = import_placeholders('./files_needed_to_get_replacements_list_json_format/占位符(placeholders)_$20987$-$499999$_全域替换用.txt')

temporary_replacements_list_final=[]
for kk in range(len(temporary_replacements_list_2)):
    temporary_replacements_list_final.append([temporary_replacements_list_2[kk][0],temporary_replacements_list_2[kk][1],imported_placeholders[kk]])

# 置換に用いる関数。正規表現、C++など様々な形式の置換を試したが、pythonでplaceholder(占位符)を用いる形式の置換が、最も処理が高速であった。(しかも大変シンプルでわかりやすい。)
def safe_replace(text, replacements):
    valid_replacements = {}
    # 置換対象(old)をplaceholderに一時的に置換
    for old, new, placeholder in replacements:
        if old in text:
            text = text.replace(old, placeholder)
            valid_replacements[placeholder] = new# 後で置換後の文字列(new)に置換し直す必要があるplaceholderを辞書(valid_replacements)に記録しておく。
    # placeholderを置換後の文字列(new)に置換)
    for placeholder, new in valid_replacements.items():
        text = text.replace(placeholder, new)
    return text


# このセルの処理が全体を通して一番時間がかかる(数十秒)
# 'PEJVO(世界语全部单词列表)'全部'について、词尾(a,i,u,e,o,n等)をcutし、comma(,)で隔てて词性と併せて记录した列表'(stem_with_part_of_speech_list)を実際にリスト'temporary_replacements_list_final'(一時的な置換リストの完成版)によって文字列(漢字)置換。　
# ここで作成される、"文字列(漢字)置換し終えたリスト(辞書型配列)"(pre_replacements_dict_1)こそが最終的な置換リスト(replacements_final_list)の大元になる。
# リスト'stem_with_part_of_speech_list'までは情報の損失は殆どないはず。

pre_replacements_dict_1={}
for j in stem_with_part_of_speech_list:# 20秒ほどかかる。　先にリストの要素を全て結合して、一つの文字列にしてから置換する方法を試しても(上述)、さほど高速化しなかった。
    if len(j)==2:# (j[0]がエスペラント語根、j[1]が品詞。)
        if len(j[0])>=2:# 2文字以上のエスペラント語根のみが対象  3で良いのでは(202412)
            if j[0] in pre_replacements_dict_1:
                if j[1] not in pre_replacements_dict_1[j[0]][1]:
                    pre_replacements_dict_1[j[0]] = [pre_replacements_dict_1[j[0]][0],pre_replacements_dict_1[j[0]][1] + ',' + j[1]]# 複数品詞の追加
            else:
                pre_replacements_dict_1[j[0]]=[safe_replace(j[0], temporary_replacements_list_final),j[1]]# 辞書型配列の追加法


keys_to_remove = ['domen', 'teren','posten']# 後でdomen/o,domen/a,domen/e等を追加する。　→確認済み(24/12)
for key in keys_to_remove:
    pre_replacements_dict_1.pop(key, None)  # 'None' はキーが存在しない場合に返すデフォルト

#  pre_replacements_dict_1→pre_replacements_dict_2 
pre_replacements_dict_2={}
for i,j in pre_replacements_dict_1.items():# (iが置換対象の単語、j[0]が置換後の文字列、j[1]が品詞。)
    if i==j[0]:# 置換しない単語
        pre_replacements_dict_2[i.replace('/', '')]=[j[0].replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"),j[1],len(i.replace('/', ''))*10000-3000]
    else:
        pre_replacements_dict_2[i.replace('/', '')]=[j[0].replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"),j[1],len(i.replace('/', ''))*10000]

### 基本的には動詞に対してのみ活用語尾を追加し、置換対象の単語の文字数を増やす(置換の優先順位を上げる。)
verb_suffix_2l={'as':'as', 'is':'is', 'os':'os', 'us':'us','at':'at','it':'it','ot':'ot', 'ad':'ad','iĝ':'iĝ','ig':'ig','ant':'ant','int':'int','ont':'ont'}
##接頭辞接尾時の追加については、主に動詞が対象である。
verb_suffix_2l_2={}
for original_verb_suffix,replaced_verb_suffix in verb_suffix_2l.items():
    verb_suffix_2l_2[original_verb_suffix]=safe_replace(replaced_verb_suffix, temporary_replacements_list_final)

pre_replacements_dict_3={}
overlap_1,overlap_2,overlap_3,overlap_4,overlap_5,overlap_6,overlap_7,overlap_8=[],[],[],[],[],[],[],[]
overlap_9,overlap_10,overlap_11,overlap_12,overlap_13,overlap_14,overlap_15,overlap_16=[],[],[],[],[],[],[],[]
overlap_2_2,overlap_2_3=[],[]
unchangeable_after_creation_list=[]
count_0,count_1,count_2,count_3,count_4,count_5=0,0,0,0,0,0
adj_1,adj_2,adj_3,adj_4=0,0,0,0
AN_replacement = safe_replace('an', temporary_replacements_list_final)
AN_treatment=[]

# pre_replacements_dict_3内での重複の検査をし、それを元に一連の修正を行う
pre_replacements_dict_2_copy = pre_replacements_dict_2.copy()
for i,j in pre_replacements_dict_2_copy.items():
    if i.endswith('an') and (AN_replacement in j[0]) and ("名词" in j[1]) and (i[:-2] in pre_replacements_dict_2_copy):
        AN_treatment.append([i,j[0]])
        pre_replacements_dict_2.pop(i, None)
        for k in ["o","a","e"]:
            if not i+k in pre_replacements_dict_2_copy:
                pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-2000]
    elif (j[1] == "名词") and (len(i)<=6) and not(j[2]==60000 or j[2]==50000 or j[2]==40000 or j[2]==30000 or j[2]==20000):
        for k in ["o"]:
            if not i+k in pre_replacements_dict_2_copy:
                pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-2000]
                count_0+=1
            else:
                overlap_1.append([i+k,pre_replacements_dict_2_copy[i+k][0],j[0]+k])
        pre_replacements_dict_2.pop(i, None)
        count_1+=1

for i,j in pre_replacements_dict_2.items():
    if j[2]==20000:
        if "名词" in j[1]:
            for k in ["o","on",'oj']:
                if not i+k in pre_replacements_dict_2:
                    pre_replacements_dict_3[' '+i+k]=[' '+j[0]+k,j[2]+(len(k)+1)*10000-5000]
                else:
                    overlap_2.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
        if "形容词" in j[1]:
            for k in ["a","aj",'an']:
                if not i+k in pre_replacements_dict_2:
                    pre_replacements_dict_3[' '+i+k]=[' '+j[0]+k,j[2]+(len(k)+1)*10000-5000]
                else:
                    pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-5000]
                    overlap_2_2.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
                    unchangeable_after_creation_list.append(i+k)
            adj_1+=1
        if "副词" in j[1]:
            for k in ["e"]:
                if not i+k in pre_replacements_dict_2:
                    pre_replacements_dict_3[' '+i+k]=[' '+j[0]+k,j[2]+(len(k)+1)*10000-5000]
                else:
                    pre_replacements_dict_3[' '+i+k]=[' '+j[0]+k,j[2]+(len(k)+1)*10000-5000]
                    overlap_2_3.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
        if "动词" in j[1]:
            for k1,k2 in verb_suffix_2l_2.items():
                if not i+k1 in pre_replacements_dict_2:
                    pre_replacements_dict_3[i+k1]=[j[0]+k2,j[2]+len(k1)*10000-3000]
                elif j[0]+k2 != pre_replacements_dict_2[i+k1][0]:
                    pre_replacements_dict_3[i+k1]=[j[0]+k2,j[2]+len(k1)*10000-3000]
                    overlap_3.append([i+k1,pre_replacements_dict_2[i+k1][0],j[0]+k2])
                    unchangeable_after_creation_list.append(i+k1)
            for k in ["u ","i ","u","i"]:
                if not i+k in pre_replacements_dict_2:
                    pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                elif j[0]+k != pre_replacements_dict_2[i+k][0]:
                    overlap_4.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
        count_2+=1
        continue

    else:
        if not i in unchangeable_after_creation_list:
            pre_replacements_dict_3[i]=[j[0],j[2]]
        if j[2]==60000 or j[2]==50000 or j[2]==40000 or j[2]==30000:
            if "名词" in j[1]:
                for k in ["o","on",'oj']:
                    if not i+k in pre_replacements_dict_2:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                    elif j[0]+k != pre_replacements_dict_2[i+k][0]:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                        overlap_5.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
                        unchangeable_after_creation_list.append(i+k)
            if "形容词" in j[1]:
                for k in ["a","aj",'an']:
                    if not i+k in pre_replacements_dict_2:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                    elif j[0]+k != pre_replacements_dict_2[i+k][0]:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                        overlap_6.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
                        unchangeable_after_creation_list.append(i+k)
            if "副词" in j[1]:
                for k in ["e"]:
                    if not i+k in pre_replacements_dict_2:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                    elif j[0]+k != pre_replacements_dict_2[i+k][0]:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                        overlap_7.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
                        unchangeable_after_creation_list.append(i+k)
            if "动词" in j[1]:
                for k1,k2 in verb_suffix_2l_2.items():
                    if not i+k1 in pre_replacements_dict_2:
                        pre_replacements_dict_3[i+k1]=[j[0]+k2,j[2]+len(k1)*10000-3000]
                    elif j[0]+k2 != pre_replacements_dict_2[i+k1][0]:
                        pre_replacements_dict_3[i+k1]=[j[0]+k2,j[2]+len(k1)*10000-3000]
                        overlap_8.append([i+k1,pre_replacements_dict_2[i+k1][0],j[0]+k2])
                        unchangeable_after_creation_list.append(i+k1)
                for k in ["u ","i ","u","i"]:
                    if not i+k in pre_replacements_dict_2:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                    elif j[0]+k != pre_replacements_dict_2[i+k][0]:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-3000]
                        overlap_9.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
                        unchangeable_after_creation_list.append(i+k)
            count_3+=1
        elif len(i)>=3 and len(i)<=6:
            if "名词" in j[1]:
                for k in ["o"]:
                    if not i+k in pre_replacements_dict_2:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-5000]
                    elif j[0]+k != pre_replacements_dict_2[i+k][0]:
                        overlap_10.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
            if "形容词" in j[1]:
                for k in ["a"]:
                    if not i+k in pre_replacements_dict_2:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-5000]
                    elif j[0]+k != pre_replacements_dict_2[i+k][0]:
                        overlap_11.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
            if "副词" in j[1]:
                for k in ["e"]:
                    if not i+k in pre_replacements_dict_2:
                        pre_replacements_dict_3[i+k]=[j[0]+k,j[2]+len(k)*10000-5000]
                    elif j[0]+k != pre_replacements_dict_2[i+k][0]:
                        overlap_12.append([i+k,pre_replacements_dict_2[i+k][0],j[0]+k])
            count_4+=1

AN=[['dietan', '/diet/an/', '/diet/an'], ['afrikan', '/afrik/an/', '/afrik/an'], ['movadan', '/mov/ad/an/', '/mov/ad/an'], ['akcian', '/akci/an/', '/akci/an'], ['montaran', '/mont/ar/an/', '/mont/ar/an'], ['amerikan', '/amerik/an/', '/amerik/an'], ['regnan', '/regn/an/', '/regn/an'], ['dezertan', '/dezert/an/', '/dezert/an'], ['asocian', '/asoci/an/', '/asoci/an'], ['insulan', '/insul/an/', '/insul/an'], ['azian', '/azi/an/', '/azi/an'], ['ŝtatan', '/ŝtat/an/', '/ŝtat/an'], ['doman', '/dom/an/', '/dom/an'], ['montan', '/mont/an/', '/mont/an'], ['familian', '/famili/an/', '/famili/an'], ['urban', '/urb/an/', '/urb/an'], ['popolan', '/popol/an/', '/popol/an'], ['dekan', '/dekan/', '/dek/an'], ['partian', '/parti/an/', '/parti/an'], ['lokan', '/lok/an/', '/lok/an'], ['ŝipan', '/ŝip/an/', '/ŝip/an'], ['eklezian', '/eklezi/an/', '/eklezi/an'], ['landan', '/land/an/', '/land/an'], ['orientan', '/orient/an/', '/orient/an'], ['lernejan', '/lern/ej/an/', '/lern/ej/an'], ['enlandan', '/en/land/an/', '/en/land/an'], ['kalkan', '/kalkan/', '/kalk/an'], ['estraran', '/estr/ar/an/', '/estr/ar/an'], ['etnan', '/etn/an/', '/etn/an'], ['eŭropan', '/eŭrop/an/', '/eŭrop/an'], ['fazan', '/fazan/', '/faz/an'], ['polican', '/polic/an/', '/polic/an'], ['socian', '/soci/an/', '/soci/an'], ['societan', '/societ/an/', '/societ/an'], ['grupan', '/grup/an/', '/grup/an'], ['ligan', '/lig/an/', '/lig/an'], ['nacian', '/naci/an/', '/naci/an'], ['koran', '/koran/', '/kor/an'], ['religian', '/religi/an/', '/religi/an'], ['kuban', '/kub/an/', '/kub/an'], ['majoran', '/major/an/', '/major/an'], ['nordan', '/nord/an/', '/nord/an'], ['paran', 'paran', '/par/an'], ['parizan', '/pariz/an/', '/pariz/an'], ['parokan', '/parok/an/', '/parok/an'], ['podian', '/podi/an/', '/podi/an'], ['rusian', '/rus/i/an/', '/rus/ian'], ['satan', '/satan/', '/sat/an'], ['sektan', '/sekt/an/', '/sekt/an'], ['senatan', '/senat/an/', '/senat/an'], ['skisman', '/skism/an/', '/skism/an'], ['sudan', 'sudan', '/sud/an'], ['utopian', '/utopi/an/', '/utopi/an'], ['vilaĝan', '/vilaĝ/an/', '/vilaĝ/an'], ['arĝentan', '/arĝent/an/', '/arĝent/an']]
ON=[['duon', '/du/on/', '/du/on'], ['okon', '/ok/on/', '/ok/on'], ['nombron', '/nombr/on/', '/nombr/on'], ['patron', '/patron/', '/patr/on'], ['karbon', '/karbon/', '/karb/on'], ['ciklon', '/ciklon/', '/cikl/on'], ['aldon', '/al/don/', '/ald/on'], ['balon', '/balon/', '/bal/on'], ['baron', '/baron/', '/bar/on'], ['baston', '/baston/', '/bast/on'], ['magneton', '/magnet/on/', '/magnet/on'], ['beton', 'beton', '/bet/on'], ['bombon', '/bombon/', '/bomb/on'], ['breton', 'breton', '/bret/on'], ['burĝon', '/burĝon/', '/burĝ/on'], ['centon', '/cent/on/', '/cent/on'], ['milon', '/mil/on/', '/mil/on'], ['kanton', '/kanton/', '/kant/on'], ['citron', '/citron/', '/citr/on'], ['platon', 'platon', '/plat/on'], ['dekon', '/dek/on/', '/dek/on'], ['kvaron', '/kvar/on/', '/kvar/on'], ['kvinon', '/kvin/on/', '/kvin/on'], ['seson', '/ses/on/', '/ses/on'], ['trion', '/tri/on/', '/tri/on'], ['karton', '/karton/', '/kart/on'], ['foton', '/fot/on/', '/fot/on'], ['peron', '/peron/', '/per/on'], ['elektron', '/elektr/on/', '/elektr/on'], ['drakon', 'drakon', '/drak/on'], ['mondon', '/mon/don/', '/mond/on'], ['pension', '/pension/', '/pensi/on'], ['ordon', '/ordon/', '/ord/on'], ['eskadron', 'eskadron', '/eskadr/on'], ['senton', '/sen/ton/', '/sent/on'], ['eston', 'eston', '/est/on'], ['fanfaron', '/fanfaron/', '/fanfar/on'], ['feston', '/feston/', '/fest/on'], ['flegmon', 'flegmon', '/flegm/on'], ['fronton', '/fronton/', '/front/on'], ['galon', '/galon/', '/gal/on'], ['mason', '/mason/', '/mas/on'], ['helikon', 'helikon', '/helik/on'], ['kanon', '/kanon/', '/kan/on'], ['kapon', '/kapon/', '/kap/on'], ['kokon', '/kokon/', '/kok/on'], ['kolon', '/kolon/', '/kol/on'], ['komision', '/komision/', '/komisi/on'], ['salon', '/salon/', '/sal/on'], ['ponton', '/ponton/', '/pont/on'], ['koton', '/koton/', '/kot/on'], ['kripton', 'kripton', '/kript/on'], ['kupon', '/kupon/', '/kup/on'], ['lakon', 'lakon', '/lak/on'], ['ludon', '/lu/don/', '/lud/on'], ['melon', '/melon/', '/mel/on'], ['menton', '/menton/', '/ment/on'], ['milion', '/milion/', '/mili/on'], ['milionon', '/milion/on/', '/milion/on'], ['naŭon', '/naŭ/on/', '/naŭ/on'], ['violon', '/violon/', '/viol/on'], ['trombon', '/trombon/', '/tromb/on'], ['senson', '/sen/son/', '/sens/on'], ['sepon', '/sep/on/', '/sep/on'], ['skadron', 'skadron', '/skadr/on'], ['stadion', '/stadion/', '/stadi/on'], ['tetraon', 'tetraon', '/tetra/on'], ['timon', '/timon/', '/tim/on'], ['valon', 'valon', '/val/on']]

for an in AN:
    if an[1].endswith("/an/"):
        i2=an[1]
        i3 = re.sub(r"/an/$", "", i2)
        i4=i3+"/an/o"
        i5=i3+"/an/a"
        i6=i3+"/an/e"
        i7=i3+"/a/n/"
        pre_replacements_dict_3[i4.replace('/', '')]=[safe_replace(i4,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i4.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i5.replace('/', '')]=[safe_replace(i5,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i5.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i6.replace('/', '')]=[safe_replace(i6,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i6.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i7.replace('/', '')]=[safe_replace(i7,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i7.replace('/', ''))-1)*10000+3000]

    else:
        i2=an[1]
        i2_2 = re.sub(r"an$", "", i2)
        i3 = re.sub(r"an/$", "", i2_2)
        i4=i3+"an/o"
        i5=i3+"an/a"
        i6=i3+"an/e"
        i7=i3+"/a/n/"
        pre_replacements_dict_3[i4.replace('/', '')]=[safe_replace(i4,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i4.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i5.replace('/', '')]=[safe_replace(i5,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i5.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i6.replace('/', '')]=[safe_replace(i6,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i6.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i7.replace('/', '')]=[safe_replace(i7,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i7.replace('/', ''))-1)*10000+3000]

for on in ON:
    if on[1].endswith("/on/"):
        i2=on[1]
        i3 = re.sub(r"/on/$", "", i2)
        i4=i3+"/on/o"
        i5=i3+"/on/a"
        i6=i3+"/on/e"
        i7=i3+"/o/n/"
        pre_replacements_dict_3[i4.replace('/', '')]=[safe_replace(i4,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i4.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i5.replace('/', '')]=[safe_replace(i5,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i5.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i6.replace('/', '')]=[safe_replace(i6,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i6.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i7.replace('/', '')]=[safe_replace(i7,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i7.replace('/', ''))-1)*10000+3000]

    else:
        i2=on[1]
        i2_2 = re.sub(r"on$", "", i2)
        i3 = re.sub(r"on/$", "", i2_2)
        i4=i3+"on/o"
        i5=i3+"on/a"
        i6=i3+"on/e"
        i7=i3+"/o/n/"
        pre_replacements_dict_3[i4.replace('/', '')]=[safe_replace(i4,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i4.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i5.replace('/', '')]=[safe_replace(i5,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i5.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i6.replace('/', '')]=[safe_replace(i6,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i6.replace('/', ''))-1)*10000+3000]
        pre_replacements_dict_3[i7.replace('/', '')]=[safe_replace(i7,temporary_replacements_list_final).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), (len(i7.replace('/', ''))-1)*10000+3000]

# 外部ファイルを読み込む形式に変えた。行われている処理は全く同じ。
for i in change_dec:
    if len(i)==3:
        try:
            if i[1]==0:
                num_char_or=len(i[0].replace('/', ''))*10000
            else:
                num_char_or=i[1]
            if "动词词尾1" in i[2]:
                for k1,k2 in verb_suffix_2l_2.items():
                    pre_replacements_dict_3[(i[0]+k1).replace('/', '')]=[safe_replace(i[0],temporary_replacements_list_3).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>")+k2, num_char_or+len(k1)*10000]
                i[2].remove("动词词尾1")
            if "动词词尾2" in i[2]:
                for k in ["u ","i ","u","i"]:
                    pre_replacements_dict_3[(i[0]+k).replace('/', '')]=[safe_replace(i[0],temporary_replacements_list_3).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>")+k, num_char_or+len(k)*10000]
                i[2].remove("动词词尾2")
            if len(i[2])>=1:
                for j_ in i[2]:
                    pre_replacements_dict_3[(i[0]+'/'+j_).replace('/', '')]=[safe_replace((i[0]+'/'+j_),temporary_replacements_list_3).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), num_char_or+len(j_)*10000]
            else:
                pre_replacements_dict_3[i[0].replace('/', '')]=[safe_replace(i[0],temporary_replacements_list_3).replace("</rt></ruby>","%%%").replace('/', '').replace("%%%","</rt></ruby>"), num_char_or]
        except:
            continue


# 辞書型をリスト型に戻す。置換優先順位の数字の大きさ順にソートするため。
pre_replacements_list_1=[]
for old,new in  pre_replacements_dict_3.items():
    if isinstance(new[1], int):
        pre_replacements_list_1.append((old,new[0],new[1]))

pre_replacements_list_2= sorted(pre_replacements_list_1, key=lambda x: x[2], reverse=True)# (置換優先順位の数字の大きさ順にソート!)

# 'エスペラント語根'、'置換後文字列'、'placeholder(占位符)'の順に並べ、最終的な文字列(漢字)置換に用いる"replacements"リストの元を作成。
pre_replacements_list_3=[]
for kk in range(len(pre_replacements_list_2)):
    if len(pre_replacements_list_2[kk][0])>=3:# 3文字以上でいいのではないか(202412)  la対策として考案された。
        pre_replacements_list_3.append((pre_replacements_list_2[kk][0],pre_replacements_list_2[kk][1],imported_placeholders[kk]))

##'大文字'、'小文字'、'文頭だけ大文字'のケースに対応。
pre_replacements_list_4=[]
if format_type in ('HTML格式_Ruby文字_大小调整','HTML格式_Ruby文字_大小调整_汉字替换','HTML格式','HTML格式_汉字替换'):
    for old,new,place_holder in pre_replacements_list_3:
        pre_replacements_list_4.append((old,new,place_holder))
        pre_replacements_list_4.append((old.upper(),new.upper(),place_holder[:-1]+'up$'))
        if old[0]==' ':
            pre_replacements_list_4.append((old[0] + old[1:].capitalize() ,new[0] + capitalize_ruby_and_rt(new[1:]),place_holder[:-1]+'cap$'))
        else:
            pre_replacements_list_4.append((old.capitalize(),capitalize_ruby_and_rt(new),place_holder[:-1]+'cap$'))
elif format_type in ('括弧(号)格式', '括弧(号)格式_汉字替换'):
    for old,new,place_holder in pre_replacements_list_3:
        pre_replacements_list_4.append((old,new,place_holder))
        pre_replacements_list_4.append((old.upper(),new.upper(),place_holder[:-1]+'up$'))
        if old[0]==' ':
            pre_replacements_list_4.append((old[0] + old[1:].capitalize(),new[0] + new[1:].capitalize(),place_holder[:-1]+'cap$'))
        else:
            pre_replacements_list_4.append((old.capitalize(),new.capitalize(),place_holder[:-1]+'cap$'))
elif format_type in ('替换后文字列のみ(仅)保留(简单替换)'):
    for old,new,place_holder in pre_replacements_list_3:
        pre_replacements_list_4.append((old,new,place_holder))
        pre_replacements_list_4.append((old.upper(),new.upper(),place_holder[:-1]+'up$'))
        if old[0]==' ':
            pre_replacements_list_4.append((old[0] + old[1:].capitalize() ,new[0] + new[1:].capitalize() ,place_holder[:-1]+'cap$'))
        else:
            pre_replacements_list_4.append((old.capitalize(),new.capitalize(),place_holder[:-1]+'cap$'))


replacements_final_list=[]
for old, new, place_holder in pre_replacements_list_4:
    # 新しい変数で空白を追加した内容を保持
    modified_placeholder = place_holder
    if old.startswith(' '):
        modified_placeholder = ' ' + modified_placeholder  # 置換対象の文字列の語頭が空白の場合、placeholderの語頭にも空白を追加する。
        if not new.startswith(' '):
            new = ' ' + new
    if old.endswith(' '):
        modified_placeholder = modified_placeholder + ' '  # 置換対象の文字列の語末が空白の場合、placeholderの語末にも空白を追加する。
        if not new.endswith(' '):
            new = new + ' '
    # 結果をリストに追加
    replacements_final_list.append((old, new, modified_placeholder))

# with open("./files_needed_to_get_replacements_list_json_format/最终的な替换用のリスト(列表)型配列(replacements_final_list)_anytype.json", "w", encoding="utf-8") as g:
#     json.dump(replacements_final_list, g, ensure_ascii=False, indent=2)

suffix_2char_roots=['ad', 'ag', 'am', 'ar', 'as', 'at', 'av', 'di', 'ec', 'eg', 'ej', 'em', 'er', 'et', 'id', 'ig', 'il', 'in', 'ir', 'is', 'it', 'lu', 'nj', 'op', 'or', 'os', 'ot', 'ov', 'pi', 'te', 'uj', 'ul', 'um', 'us', 'uz','ĝu','aĵ','iĝ','aĉ','aĝ','ŝu','eĥ']
prefix_2char_roots=['al', 'am', 'av', 'bo', 'di', 'du', 'ek', 'el', 'en', 'fi', 'ge', 'ir', 'lu', 'ne', 'ok', 'or', 'ov', 'pi', 're', 'te', 'uz','ĝu','aĉ','aĝ','ŝu','eĥ']
standalone_2char_roots=['al', 'ci', 'da', 'de', 'di', 'do', 'du', 'el', 'en', 'fi', 'ha', 'he', 'ho', 'ia', 'ie', 'io', 'iu', 'ja', 'je', 'ju','ke', 'la', 'li', 'mi', 'ne', 'ni', 'nu', 'ok', 'ol', 'po', 'se', 'si', 've', 'vi','ŭa','aŭ','ĉe','ĝi','ŝi','ĉu']
# an,onはなしにする。

imported_placeholders_for_2char = import_placeholders('./files_needed_to_get_replacements_list_json_format/占位符(placeholders)_$13246$-$19834$_二文字词根替换用.txt')# 文字列(漢字)置換時に用いる"placeholder"ファイルを予め読み込んでおく。

replacements_list_for_suffix_2char_roots=[]
for i in range(len(suffix_2char_roots)):
    replacements_list_for_suffix_2char_roots.append(["$"+suffix_2char_roots[i],"$"+safe_replace(suffix_2char_roots[i],temporary_replacements_list_final),"$"+imported_placeholders_for_2char[i]])
    replacements_list_for_suffix_2char_roots.append(["$"+suffix_2char_roots[i].upper(),"$"+safe_replace(suffix_2char_roots[i],temporary_replacements_list_final).upper(),"$"+imported_placeholders_for_2char[i][:-1]+'up$'])
    replacements_list_for_suffix_2char_roots.append(["$"+suffix_2char_roots[i].capitalize(),"$"+safe_replace(suffix_2char_roots[i],temporary_replacements_list_final).capitalize(),"$"+imported_placeholders_for_2char[i][:-1]+'cap$'])

replacements_list_for_prefix_2char_roots=[]
for i in range(len(prefix_2char_roots)):
    replacements_list_for_prefix_2char_roots.append([prefix_2char_roots[i]+"$",safe_replace(prefix_2char_roots[i],temporary_replacements_list_final)+"$",imported_placeholders_for_2char[i+1000]+"$"])
    replacements_list_for_prefix_2char_roots.append([prefix_2char_roots[i].upper()+"$",safe_replace(prefix_2char_roots[i],temporary_replacements_list_final).upper()+"$",imported_placeholders_for_2char[i+1000][:-1]+'up$'+"$"])
    replacements_list_for_prefix_2char_roots.append([prefix_2char_roots[i].capitalize()+"$",safe_replace(prefix_2char_roots[i],temporary_replacements_list_final).capitalize()+"$",imported_placeholders_for_2char[i+1000][:-1]+'cap$'+"$"])

replacements_list_for_standalone_2char_roots=[]
for i in range(len(standalone_2char_roots)):
    replacements_list_for_standalone_2char_roots.append([" "+standalone_2char_roots[i]+" "," "+safe_replace(standalone_2char_roots[i],temporary_replacements_list_final)+" "," "+imported_placeholders_for_2char[i+2000]+" "])
    replacements_list_for_standalone_2char_roots.append([" "+standalone_2char_roots[i].upper()+" "," "+safe_replace(standalone_2char_roots[i],temporary_replacements_list_final).upper()+" "," "+imported_placeholders_for_2char[i+2000][:-1]+'up$'+" "])
    replacements_list_for_standalone_2char_roots.append([" "+standalone_2char_roots[i].capitalize()+" "," "+safe_replace(standalone_2char_roots[i],temporary_replacements_list_final).capitalize()+" "," "+imported_placeholders_for_2char[i+2000][:-1]+'cap$'+" "])

replacements_list_for_2char = replacements_list_for_standalone_2char_roots+replacements_list_for_suffix_2char_roots+replacements_list_for_prefix_2char_roots


# 局所的な文字列(漢字)置換には、最初の"input_csv_file"のみを使って作成した置換リストを用いる。

pre_replacements_list_for_localized_string_1=[]
for _, (E_root, hanzi_or_meaning) in input_csv_file.iterrows():
    if pd.notna(E_root) and pd.notna(hanzi_or_meaning) and '#' not in E_root:  # 条件を満たす行のみ処理
        pre_replacements_list_for_localized_string_1.append([E_root,output_format(E_root, hanzi_or_meaning, format_type),len(E_root)])
        pre_replacements_list_for_localized_string_1.append([E_root.upper(),output_format(E_root.upper(), hanzi_or_meaning.upper(), format_type),len(E_root)])
        pre_replacements_list_for_localized_string_1.append([E_root.capitalize(),output_format(E_root.capitalize(), hanzi_or_meaning.capitalize(), format_type),len(E_root)])

pre_replacements_list_for_localized_string_2 = sorted(pre_replacements_list_for_localized_string_1, key=lambda x: x[2], reverse=True)

imported_placeholders = import_placeholders('./files_needed_to_get_replacements_list_json_format/占位符(placeholders)_@20374@-@97648@_局部文字列替换用.txt')
replacements_list_for_localized_string=[]
for kk in range(len(pre_replacements_list_for_localized_string_2)):
    replacements_list_for_localized_string.append([pre_replacements_list_for_localized_string_2[kk][0],pre_replacements_list_for_localized_string_2[kk][1],imported_placeholders[kk]])


    
# --- 結合する処理 ---
combined_data = {}

# キー名はお好みに変更可
combined_data["最终的な替换用のリスト(列表)型配列(replacements_final_list)"] = replacements_final_list
combined_data["二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)"] = replacements_list_for_2char
combined_data["局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)"] = replacements_list_for_localized_string


# JSON文字列に変換
download_data = json.dumps(combined_data, ensure_ascii=False, indent=2)

# --- ダウンロードボタン ---
st.download_button(
    label="Download 最终的な替换用リスト(列表)(合并3个JSON文件)",
    data=download_data,          
    file_name="最终的な替换用リスト(列表)(合并3个JSON文件).json",
    mime='application/json'
)
