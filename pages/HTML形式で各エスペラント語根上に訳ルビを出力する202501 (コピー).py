import streamlit as st
import re
import io
from PIL import Image
import pandas as pd
import json

# html形式におけるルビサイズの変更形式
ruby_style_head="""<style>
.text-S_S_S {font-size: 12px;}
.text-M_M_M {font-size: 16px;}
.text-L_L_L {font-size: 20px;}
.text-X_X_X {font-size: 24px;}
.ruby-XS_S_S { font-size: 0.30em; } /* Extra Small */
.ruby-S_S_S  { font-size: 0.40em; } /* Small */
.ruby-M_M_M  { font-size: 0.50em; } /* Medium */
.ruby-L_L_L  { font-size: 0.60em; } /* Large */
.ruby-XL_L_L { font-size: 0.70em; } /* Extra Large */
.ruby-XXL_L_L { font-size: 0.80em; } /* Double Extra Large */

ruby {
  display: inline-block;
  position: relative; /* 相対位置 */
  white-space: nowrap; /* 改行防止 */
  line-height: 1.9;
}
rt {
  position: absolute;
  top: -0.75em;
  left: 50%; /* 左端を親要素の中央に合わせる */
  transform: translateX(-50%); /* 中央に揃える */
  line-height: 2.1;
  color: blue; 
}
rt.ruby-XS_S_S { top: -0.20em; } /* ルビサイズに応じて、ルビを表示する高さを変える。 */
rt.ruby-S_S_S  { top: -0.30em; }
rt.ruby-M_M_M  { top: -0.40em; }
rt.ruby-L_L_L  { top: -0.50em; }
rt.ruby-XL_L_L { top: -0.65em; }
rt.ruby-XXL_L_L{ top: -0.80em; }

</style>
<p class="text-M_M_M">
"""
ruby_style_tail = "<br>\n</p>"

# 字上符付き文字の表記形式変換用の辞書型配列
x_to_circumflex = {'cx': 'ĉ', 'gx': 'ĝ', 'hx': 'ĥ', 'jx': 'ĵ', 'sx': 'ŝ', 'ux': 'ŭ','Cx': 'Ĉ', 'Gx': 'Ĝ', 'Hx': 'Ĥ', 'Jx': 'Ĵ', 'Sx': 'Ŝ', 'Ux': 'Ŭ'}
circumflex_to_x = {'ĉ': 'cx', 'ĝ': 'gx', 'ĥ': 'hx', 'ĵ': 'jx', 'ŝ': 'sx', 'ŭ': 'ux','Ĉ': 'Cx', 'Ĝ': 'Gx', 'Ĥ': 'Hx', 'Ĵ': 'Jx', 'Ŝ': 'Sx', 'Ŭ': 'Ux'}
x_to_hat = {'cx': 'c^', 'gx': 'g^', 'hx': 'h^', 'jx': 'j^', 'sx': 's^', 'ux': 'u^','Cx': 'C^', 'Gx': 'G^', 'Hx': 'H^', 'Jx': 'J^', 'Sx': 'S^', 'Ux': 'U^'}
hat_to_x = {'c^': 'cx', 'g^': 'gx', 'h^': 'hx', 'j^': 'jx', 's^': 'sx', 'u^': 'ux','C^': 'Cx', 'G^': 'Gx', 'H^': 'Hx', 'J^': 'Jx', 'S^': 'Sx', 'U^': 'Ux'}
hat_to_circumflex = {'c^': 'ĉ', 'g^': 'ĝ', 'h^': 'ĥ', 'j^': 'ĵ', 's^': 'ŝ', 'u^': 'ŭ','C^': 'Ĉ', 'G^': 'Gx', 'H^': 'Hx', 'J^': 'Jx', 'S^': 'Sx', 'U^': 'Ŭ'}
circumflex_to_hat = {'ĉ': 'c^', 'ĝ': 'g^', 'ĥ': 'h^', 'ĵ': 'j^', 'ŝ': 's^', 'ŭ': 'u^','Ĉ': 'C^', 'Ĝ': 'G^', 'Ĥ': 'H^', 'Ĵ': 'J^', 'Ŝ': 'S^', 'Ŭ': 'U^'}

# 字上符付き文字の表記形式変換用の関数
def replace_esperanto_chars(text, letter_dictionary):
    for esperanto_char, x_char in letter_dictionary.items():
        text = text.replace(esperanto_char, x_char)
    return text

def unify_halfwidth_spaces(text):
    """全角スペース(U+3000)は変更せず、半角スペースと視覚的に区別がつきにくい空白文字を
       ASCII半角スペース(U+0020)に統一する。連続した空白は1文字ずつ置換する。"""
    pattern = r"[\u00A0\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A]"
    return re.sub(pattern, " ", text)

def safe_replace(text, replacements):
    valid_replacements = {}
    for old, new, placeholder in replacements:
        if old in text:
            text = text.replace(old, placeholder)
            valid_replacements[placeholder] = new
    for placeholder, new in valid_replacements.items():
        text = text.replace(placeholder, new)
    return text

def enhanced_safe_replace_func_expanded_for_2char_roots(text, replacements, imported_data_replacements_list_for_2char):
    valid_replacements = {}
    for old, new, placeholder in replacements:
        if old in text:
            text = text.replace(old, placeholder)
            valid_replacements[placeholder] = new

    valid_replacements_for_2char_roots = {}
    for old, new, placeholder in imported_data_replacements_list_for_2char:
        if old in text:
            text = text.replace(old, placeholder)
            valid_replacements_for_2char_roots[placeholder] = new

    valid_replacements_for_2char_roots_2 = {}
    for old, new, placeholder in imported_data_replacements_list_for_2char:
        if old in text:
            place_holder_second = "!"+placeholder+"!"
            text = text.replace(old, place_holder_second)
            valid_replacements_for_2char_roots_2[place_holder_second] = new

    for place_holder_second, new in reversed(valid_replacements_for_2char_roots_2.items()):
        text = text.replace(place_holder_second, new)

    for placeholder, new in reversed(valid_replacements_for_2char_roots.items()):
        text = text.replace(placeholder, new)

    for placeholder, new in valid_replacements.items():
        text = text.replace(placeholder, new)
    return text

def find_strings_in_text(text):
    pattern = re.compile(r'%(.{1,50}?)%')
    matches = []
    used_indices = set()

    for match in pattern.finditer(text):
        start, end = match.span()
        if start not in used_indices and end-2 not in used_indices:
            matches.append(match.group(1))
            used_indices.update(range(start, end))
    return matches

def create_replacements_list_for_intact_parts(text, placeholders):
    matches = find_strings_in_text(text)
    replacements_list_for_intact_parts = []
    for i, match in enumerate(matches):
        if i < len(placeholders):
            replacements_list_for_intact_parts.append([f"%{match}%", placeholders[i]])
        else:
            break
    return replacements_list_for_intact_parts

def import_placeholders(filename):
    with open(filename, 'r') as file:
        placeholders = [line.strip() for line in file if line.strip()]
    return placeholders

def find_strings_in_text_for_localized_replacement(text):
    pattern = re.compile(r'@(.{1,18}?)@')
    matches = []
    used_indices = set()

    for match in pattern.finditer(text):
        start, end = match.span()
        if start not in used_indices and end-2 not in used_indices:
            matches.append(match.group(1))
            used_indices.update(range(start, end))
    return matches

def create_replacements_list_for_localized_replacement(text, placeholders, replacements_list_for_localized_string):
    matches = find_strings_in_text_for_localized_replacement(text)
    tmp_replacements_list_for_localized_string = []
    for i, match in enumerate(matches):
        if i < len(placeholders):
            replaced_match = safe_replace(match, replacements_list_for_localized_string)
            tmp_replacements_list_for_localized_string.append([f"@{match}@", placeholders[i], replaced_match])
        else:
            break
    return tmp_replacements_list_for_localized_string

placeholders_for_skipping_replacements = import_placeholders('./files_needed_to_get_replacements_list_json_format/占位符(placeholders)_%1854%-%4934%_文字列替换skip用.txt')
placeholders_for_localized_replacement = import_placeholders('./files_needed_to_get_replacements_list_json_format/占位符(placeholders)_@5134@-@9728@_局部文字列替换结果捕捉用.txt')

st.title("エスペラント語根の上にHTML形式で日本語翻訳ルビを出力")

selected_option = st.radio(
    "Select JSON source (置換用JSONの読み込み先)",
    ("Use default JSON", "Upload custom JSON")
)

replacements_final_list = None
replacements_list_for_localized_string = None
imported_data_replacements_list_for_2char = None

if selected_option == "Use default JSON":
    default_json_path = "./files_needed_to_get_replacements_list_json_format/最终的な替换用リスト(列表)(合并3个JSON文件).json"
    try:
        with open(default_json_path, 'r', encoding='utf-8') as g:
            combined_data = json.load(g)
            replacements_final_list = combined_data.get("最终的な替换用のリスト(列表)型配列(replacements_final_list)", None)
            replacements_list_for_localized_string = combined_data.get("局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)", None)
            imported_data_replacements_list_for_2char = combined_data.get("二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)", None)
        st.success("Default JSON successfully loaded.")
    except Exception as e:
        st.error(f"Failed to load default JSON: {e}")
        st.stop()
else:
    uploaded_file = st.file_uploader("Upload your custom JSON file (合并3个JSON文件).json 形式)", type="json")
    if uploaded_file is not None:
        try:
            combined_data = json.load(uploaded_file)
            replacements_final_list = combined_data.get("最终的な替换用のリスト(列表)型配列(replacements_final_list)", None)
            replacements_list_for_localized_string = combined_data.get("局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)", None)
            imported_data_replacements_list_for_2char = combined_data.get("二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)", None)
            st.success("Custom JSON successfully loaded.")
        except Exception as e:
            st.error(f"Failed to parse uploaded JSON: {e}")
            st.stop()
    else:
        st.warning("You must upload a valid JSON file or select 'Use default JSON'.")
        st.stop()

text1 = ""
with st.form(key='profile_form'):
    letter_type = st.radio('出力文字形式', ('上付き文字', 'x 形式', '^ 形式'))
    text0 = st.text_area("世界語の文章")
    st.markdown("""「%」で前後を囲む（「%<50文字以内の文字列>%」形式）と、「%」で囲まれた部分は文字列(漢字)置換せず、元のまま保持することができます。""")
    st.markdown("""また、「@」で前後を囲む（「@<18文字以内の文字列>@」形式）と、「@」で囲まれた部分を局所的に文字列(漢字)置換します。""")

    submit_btn = st.form_submit_button('送信')
    cancel_btn = st.form_submit_button('キャンセル')
    if submit_btn:
        text1 = unify_halfwidth_spaces(text0)
        text1 = replace_esperanto_chars(text1, hat_to_circumflex)

        replacements_list_for_intact_parts = create_replacements_list_for_intact_parts(text1, placeholders_for_skipping_replacements)
        sorted_replacements_list_for_intact_parts = sorted(replacements_list_for_intact_parts, key=lambda x: len(x[0]), reverse=True)
        for original, place_holder_ in sorted_replacements_list_for_intact_parts:
            text1 = text1.replace(original, place_holder_)

        tmp_replacements_list_for_localized_string_2 = create_replacements_list_for_localized_replacement(text1, placeholders_for_localized_replacement, replacements_list_for_localized_string)
        sorted_replacements_list_for_localized_string = sorted(tmp_replacements_list_for_localized_string_2, key=lambda x: len(x[0]), reverse=True)
        for original, place_holder_, replaced_original in sorted_replacements_list_for_localized_string:
            text1 = text1.replace(original, place_holder_)

        text1 = enhanced_safe_replace_func_expanded_for_2char_roots(text1, replacements_final_list, imported_data_replacements_list_for_2char)

        for original, place_holder_, replaced_original in sorted_replacements_list_for_localized_string:
            text1 = text1.replace(place_holder_, replaced_original.replace("@",""))

        for original, place_holder_ in sorted_replacements_list_for_intact_parts:
            text1 = text1.replace(place_holder_, original.replace("%",""))

        if letter_type == '上付き文字':
            text1 = replace_esperanto_chars(text1, x_to_circumflex)
        elif letter_type == '^ 形式':
            text1 = replace_esperanto_chars(text1, x_to_hat)

        text1 = text1.replace("\n", "<br>\n")
        text1 = re.sub(r"   ", "&nbsp;&nbsp;&nbsp;", text1)
        text1 = re.sub(r"  ", "&nbsp;&nbsp;", text1)

        text1 = ruby_style_head + text1 + ruby_style_tail
        st.text_area("转换后的文本预览", text1, height=300)

if text1:
    to_download = io.BytesIO(text1.encode('utf-8'))
    to_download.seek(0)
    st.download_button(
        label="テキストをダウンロード",
        data=to_download,
        file_name="processed_text.html",
        mime="text/plain"
    )

st.title("アプリのGitHubリポジトリ")
st.markdown("https://github.com/Takatakatake/Esperanto_kanjika_20240310/tree/main")
