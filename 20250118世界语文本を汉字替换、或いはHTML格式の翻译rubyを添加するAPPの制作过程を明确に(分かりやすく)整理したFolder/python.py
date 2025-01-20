import json
import re
import multiprocessing
from typing import List, Tuple, Dict

class EsperantoTextReplacer:
    """
    エスペラント文字列(語根)を、ルビや漢字などに置換するためのクラス。

    以下のような多段階の置換手法をまとめて実装している:
      1. `% ～ %` に囲まれた部分を「非置換対象」としてスキップ(=保護)する処理
      2. `@ ～ @` に囲まれた部分を局所的に置換する処理
      3. 一般的な語根をまとめて置換する処理
      4. 上記置換後に再度スキップ部分や局所置換部分を元に戻す
      5. 2文字語根に対する特別処理
      6. HTML整形やマルチプロセス並列実行など

    Attributes:
        placeholders_for_skipping_replacements (List[str]):
            `% ～ %` で保護したい文字列部分を一時退避するためのプレースホルダ一覧
        placeholders_for_localized_replacement (List[str]):
            `@ ～ @` で局所置換(=一時的に手動or特殊変換したい箇所)を退避するためのプレースホルダ一覧
        replacements_list_for_localized_string (List[List[str]]):
            局所文字列置換に用いるリスト( `[old,new,placeholder]` 形式 )
        replacements_final_list (List[Tuple[str, str, str]]):
            通常の(全体向け)置換ルールリスト。 `[ (旧, 新, 占位符), ... ]`
        replacements_list_for_2char (List[Tuple[str, str, str]]):
            2文字語根専用の追加置換ルールリスト。 `[ (旧, 新, 占位符), ... ]`

    Note:
        ここで示すクラスは一例・モックアップです。実際には、
        - ファイル読み込み( JSON や CSV )部
        - マルチプロセス処理の有無
        - HTML タグ挿入の可否
        - 置換パターンに関する辞書の中身
        などを、実際の要件や既存コードの状況に合わせて書き換えてください。
    """

    def __init__(
        self,
        placeholders_for_skipping_replacements: List[str],
        placeholders_for_localized_replacement: List[str],
        replacements_list_for_localized_string: List[List[str]],
        replacements_final_list: List[Tuple[str, str, str]],
        replacements_list_for_2char: List[Tuple[str, str, str]],
        format_type: str = "HTML格式_Ruby文字_大小调整"
    ):
        """
        コンストラクタ (初期化)

        Args:
            placeholders_for_skipping_replacements (List[str]):
                `% ～ %` 保護用のプレースホルダ。
            placeholders_for_localized_replacement (List[str]):
                `@ ～ @` 局所変換用のプレースホルダ。
            replacements_list_for_localized_string (List[List[str]]):
                局所文字列( `@...@` )内の置換に使うリスト。
            replacements_final_list (List[Tuple[str, str, str]]):
                全体向けの最終置換ルール (旧,新,placeholder)。
            replacements_list_for_2char (List[Tuple[str, str, str]]):
                2文字語根向けの置換ルール (旧,新,placeholder)。
            format_type (str, optional):
                出力形式を表す文字列 (例: "HTML格式_Ruby文字_大小调整" 等)。

        Example:
            >>> replacer = EsperantoTextReplacer(
            ...     placeholders_for_skipping_replacements=["%PLACEHOLDER1%", "%PLACEHOLDER2%", ...],
            ...     placeholders_for_localized_replacement=["@LOC1@", "@LOC2@", ...],
            ...     replacements_list_for_localized_string=[...],
            ...     replacements_final_list=[("abc", "あべし", "PH_0001"), ...],
            ...     replacements_list_for_2char=[("al$", "アル$", "PH_2C_0001"), ...],
            ...     format_type="HTML格式_Ruby文字_大小调整"
            ... )
        """
        self.placeholders_for_skipping_replacements = placeholders_for_skipping_replacements
        self.placeholders_for_localized_replacement = placeholders_for_localized_replacement
        self.replacements_list_for_localized_string = replacements_list_for_localized_string
        self.replacements_final_list = replacements_final_list
        self.replacements_list_for_2char = replacements_list_for_2char
        self.format_type = format_type

        # HTML形式で使う簡易CSSなど(必要な場合のみ)
        if self.format_type in (
            "HTML格式_Ruby文字_大小调整", 
            "HTML格式_Ruby文字_大小调整_汉字替换"
        ):
            self.ruby_style_head = """<style>
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
  left: 50%;
  transform: translateX(-50%);
  line-height: 2.1;
  color: blue; 
}
rt.ruby-XS_S_S { top: -0.20em; }
rt.ruby-S_S_S  { top: -0.30em; }
rt.ruby-M_M_M  { top: -0.40em; }
rt.ruby-L_L_L  { top: -0.50em; }
rt.ruby-XL_L_L { top: -0.65em; }
rt.ruby-XXL_L_L{ top: -0.80em; }
</style>
<p class="text-M_M_M">
"""
            self.ruby_style_tail = "<br>\n</p>"
        elif self.format_type in ("HTML格式", "HTML格式_汉字替换"):
            self.ruby_style_head = """<style>
ruby rt {
  color: blue;
}
</style>
"""
            self.ruby_style_tail = "<br>"
        else:
            self.ruby_style_head = ""
            self.ruby_style_tail = ""

    # --------------------------------------------------------
    # 各種補助メソッド (docstring 付き)
    # --------------------------------------------------------
    @staticmethod
    def unify_halfwidth_spaces(text: str) -> str:
        """
        半角スペースと視覚的に紛らわしい特殊空白文字を、標準的なASCII半角スペース (U+0020) に正規化する。

        ただし全角スペース(U+3000)は変更しない。

        Args:
            text (str): 入力文字列

        Returns:
            str: 変換後の文字列

        Example:
            >>> s = "Hello\u00A0World"  # U+00A0 (ノーブレークスペース)
            >>> EsperantoTextReplacer.unify_halfwidth_spaces(s)
            'Hello World'
        """
        pattern = r"[\u00A0\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A]"
        return re.sub(pattern, " ", text)

    @staticmethod
    def replace_esperanto_chars(text: str, letter_dictionary: Dict[str, str]) -> str:
        """
        与えられた辞書(letter_dictionary)を用いて、text 内のエスペラント文字を一括置換する。

        Args:
            text (str): 対象文字列
            letter_dictionary (dict): 置換用辞書 (例: hat_to_circumflex など)

        Returns:
            str: 置換後の文字列
        """
        for esperanto_char, replaced_char in letter_dictionary.items():
            text = text.replace(esperanto_char, replaced_char)
        return text

    @staticmethod
    def find_strings_in_text(text: str) -> List[str]:
        """
        % ～ % で囲まれた文字列を抽出する (置換skip対象の保護用)

        Args:
            text (str): 入力テキスト
        Returns:
            List[str]: % ～ % に囲まれていた部分の一覧
        """
        pattern = re.compile(r'%(.{1,50}?)%')
        matches = []
        used_indices = set()
        for match in pattern.finditer(text):
            start, end = match.span()
            # 重複を避ける
            if start not in used_indices and (end - 2) not in used_indices:
                matches.append(match.group(1))
                used_indices.update(range(start, end))
        return matches

    def create_replacements_list_for_intact_parts(
        self, text: str, placeholders: List[str]
    ) -> List[Tuple[str, str]]:
        """
        テキスト中の '%...%' 部分を抽出し、対応するプレースホルダを割り振る。
        (置換対象から保護したい箇所を一時退避するための置換リストを生成)

        Args:
            text (str): 入力テキスト
            placeholders (List[str]): プレースホルダ一覧

        Returns:
            List[Tuple[str,str]]:
                [ (元文字列('%含む'), 割り当てたプレースホルダ), ... ]

        Note:
            この処理自体は「保護用置換を行う前」に呼び出し、
            返り値リストを使って実際に text.replace(...,...) する。
        """
        matched_segments = self.find_strings_in_text(text)
        replacements_list = []
        for i, match_str in enumerate(matched_segments):
            if i < len(placeholders):
                # "%中身%" を key, placeholder を val とする
                key_str = f"%{match_str}%"
                placeholder_str = placeholders[i]
                replacements_list.append((key_str, placeholder_str))
            else:
                break
        return replacements_list

    @staticmethod
    def find_strings_in_text_for_localized_replacement(text: str) -> List[str]:
        """
        @ ～ @ で囲まれた文字列を抽出する (局所的に別置換を適用したい箇所)

        Args:
            text (str): 入力テキスト

        Returns:
            List[str]: 抽出された部分(中身)のリスト
        """
        pattern = re.compile(r'@(.{1,18}?)@')
        matches = []
        used_indices = set()
        for match in pattern.finditer(text):
            start, end = match.span()
            if start not in used_indices and (end - 2) not in used_indices:
                matches.append(match.group(1))
                used_indices.update(range(start, end))
        return matches

    def create_replacements_list_for_localized_replacement(
        self, text: str
    ) -> List[Tuple[str, str, str]]:
        """
        テキスト中の `@ ～ @` 部分を抽出し、self.placeholders_for_localized_replacement と
        self.replacements_list_for_localized_string を使ってローカル置換リストを生成する。

        1. `@..@` 区間を抽出
        2. その中身を safe_replace() してローカル用置換
        3. `@..@` 全体 -> "ローカルプレースホルダ" というマッピングを返す

        Returns:
            List[Tuple[str, str, str]]:
              [ ( "@中身@",  割り当てた placeholder, 置換済み中身 ), ... ]

        Note:
            その後、実際のテキストから `@..@` を `placeholder` に置き換えた上で
            変換終了後に `placeholder -> (置換後文字列)` を再度戻すようにする。
        """
        matches = self.find_strings_in_text_for_localized_replacement(text)
        results = []
        for i, match_str in enumerate(matches):
            if i < len(self.placeholders_for_localized_replacement):
                placeholder_str = self.placeholders_for_localized_replacement[i]
                # ローカル中身を safe_replace してみる
                replaced_mid = self.safe_replace_local(
                    match_str, self.replacements_list_for_localized_string
                )
                results.append(
                    (f"@{match_str}@", placeholder_str, replaced_mid)
                )
            else:
                break
        return results

    @staticmethod
    def safe_replace_local(text: str, replacements: List[List[str]]) -> str:
        """
        ごく簡易な置換。局所的処理用。

        Args:
            text (str): 対象文字列
            replacements (List[List[str]]):
                局所用の置換リスト [ [old,new,文字数], ... ] を想定

        Returns:
            str: 全置換後の文字列 (placeholder は使わない簡易版)
        """
        # 文字数が多い順にやりたい場合は適宜 sort
        # ここでは一括置換のみにする
        for old_, new_, _len_ in replacements:
            text = text.replace(old_, new_)
        return text

    @staticmethod
    def safe_replace_global(text: str, replacements: List[Tuple[str, str, str]]) -> str:
        """
        もともとの safe_replace 形式:
          - (旧,新,placeholder) のタプルリストで順番に置換
          - 後で placeholder -> 新文字列 に戻す
        """
        valid_replacements = {}
        # old -> placeholder
        for old, new, placeholder in replacements:
            if old in text:
                text = text.replace(old, placeholder)
                valid_replacements[placeholder] = new
        # placeholder -> new
        for placeholder, new in valid_replacements.items():
            text = text.replace(placeholder, new)
        return text

    def enhanced_safe_replace_func_expanded_for_2char_roots(
        self, text: str
    ) -> str:
        """
        2文字語根を含む置換を拡張した safe_replace 処理。

        1. 通常の replacements_final_list で置換
        2. 追加で 2文字語根 (self.replacements_list_for_2char) の置換処理

        Args:
            text (str): 変換対象文字列

        Returns:
            str: 変換後の文字列
        """
        # --- まず (旧,新,placeholder) 形式の replacements_final_list を適用 ---
        text = self.safe_replace_global(text, self.replacements_final_list)

        # --- 次に 2文字語根向けの replacements_list_for_2char を適用 ---
        # (本来は段階的に placeholder→最終形 の2段階などあるが簡略化)
        text = self.safe_replace_global(text, self.replacements_list_for_2char)
        return text

    @staticmethod
    def process_segment(
        lines: List[str],
        replacer_obj: "EsperantoTextReplacer"
    ) -> str:
        """
        マルチプロセス並列化のために、
        与えられた行集合(lines)を結合→置換→連結するための処理関数。

        Args:
            lines (List[str]): 行のリスト
            replacer_obj (EsperantoTextReplacer): 置換を行うインスタンス

        Returns:
            str: 処理後文字列
        """
        segment = '\n'.join(lines)
        segment = replacer_obj.enhanced_safe_replace_func_expanded_for_2char_roots(segment)
        return segment

    def parallel_process(
        self, text: str, num_processes: int
    ) -> str:
        """
        テキストを行単位に分割し、複数プロセスで並列に置換処理を行う。

        Args:
            text (str): 置換対象文字列
            num_processes (int): プロセス数

        Returns:
            str: 置換後の文字列 (行を再結合したもの)
        """
        lines = text.split('\n')
        num_lines = len(lines)
        if num_processes <= 1:
            # 並列化しない
            return self.enhanced_safe_replace_func_expanded_for_2char_roots(text)

        lines_per_process = num_lines // num_processes
        ranges = [
            (i * lines_per_process, (i + 1) * lines_per_process)
            for i in range(num_processes)
        ]
        # 最後のプロセスが残り全てを処理
        start_last, _ = ranges[-1]
        ranges[-1] = (start_last, num_lines)

        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.starmap(
                self.process_segment,
                [(lines[start:end], self) for (start, end) in ranges]
            )

        return '\n'.join(results)

    # --------------------------------------------------------
    # 実際のメイン処理
    # --------------------------------------------------------
    def run_replacement_pipeline(
        self,
        text: str,
        skip_protect: bool = True,
        localized_replace: bool = True,
        use_parallel: bool = False,
        num_processes: int = 4
    ) -> str:
        """
        スキップ保護(`%...%`), 局所置換(`@...@`), 全体置換, 2文字語根置換, 復元, 
        さらに HTML 整形(オプション)など、必要な置換パイプラインを一気に実行する。

        Args:
            text (str): 入力テキスト
            skip_protect (bool): `%...%` 保護処理を行うか
            localized_replace (bool): `@...@` 局所置換を行うか
            use_parallel (bool): マルチプロセス並列実行するかどうか
            num_processes (int): 並列時のプロセス数

        Returns:
            str: 処理後のテキスト
        """
        # 半角空白を正規化 (全角スペースはそのまま)
        text = self.unify_halfwidth_spaces(text)

        # (必要に応じて) `%...%` スキップ保護
        replacements_skip: List[Tuple[str, str]] = []
        if skip_protect:
            replacements_skip = self.create_replacements_list_for_intact_parts(
                text, self.placeholders_for_skipping_replacements
            )
            # 実際に text.replace して保護
            for original, placeholder_ in replacements_skip:
                text = text.replace(original, placeholder_)

        # (必要に応じて) `@...@` 局所変換
        replacements_local: List[Tuple[str, str, str]] = []
        if localized_replace:
            replacements_local = self.create_replacements_list_for_localized_replacement(text)
            for original, placeholder_, replaced_content in replacements_local:
                text = text.replace(original, placeholder_)

        # 全体置換(＋ 2文字語根)
        if use_parallel and num_processes > 1:
            text = self.parallel_process(text, num_processes)
        else:
            text = self.enhanced_safe_replace_func_expanded_for_2char_roots(text)

        # 局所置換を元に戻す
        #  (placeholder_ -> replaced_content)
        for original, placeholder_, replaced_content in replacements_local:
            # ここでは replaced_content 内の `@` を消す など
            text = text.replace(placeholder_, replaced_content.replace("@", ""))

        # スキップ保護を元に戻す
        for original, placeholder_ in replacements_skip:
            text = text.replace(placeholder_, original.replace("%", ""))

        # HTML 整形(改行→<br>など)
        if self.format_type in (
            "HTML格式_Ruby文字_大小调整",
            "HTML格式_Ruby文字_大小调整_汉字替换",
            "HTML格式",
            "HTML格式_汉字替换",
        ):
            text = text.replace("\n", "<br>\n")
            text = re.sub(r"   ", "&nbsp;&nbsp;&nbsp;", text)
            text = re.sub(r"  ", "&nbsp;&nbsp;", text)

        # 必要なら <style> など追加
        text = self.ruby_style_head + text + self.ruby_style_tail

        return text


# ------------------------------
# 以下は、もしこのファイルがスクリプトとして直接実行されたときの動作例
# python esperanto_text_replacer.py
# のように実行すると、簡単な動作デモを行う。
# ------------------------------
if __name__ == "__main__":
    # 例: CSVやJSONなどから読み込んでセットアップするイメージ
    # ここではモックとして簡単に定義
    placeholders_for_skip = ["%SKIP_0001%", "%SKIP_0002%", "%SKIP_0003%"]
    placeholders_for_local = ["@LOC_0001@", "@LOC_0002@", "@LOC_0003@", "@LOC_0004@"]
    replacements_local = [
        # [old, new, length]
        ["Esperanto", "<ruby>Esperanto<rt>世界語</rt></ruby>", 9],
        ["Zamenhof", "<ruby>Zamenhof<rt>ザメンホフ</rt></ruby>", 8],
    ]
    final_list = [
        ("kaj", "<ruby>kaj<rt>そして</rt></ruby>", "PLACE_0001"),
        ("Hello", "Saluton", "PLACE_0002"),
    ]
    two_char_list = [
        (" al$", " <ruby>al<rt>～の方へ</rt></ruby>$", "2C_PLACE_0001"),
        (" bo$", " <ruby>bo<rt>義理の</rt></ruby>$", "2C_PLACE_0002"),
    ]

    # クラスのインスタンス化
    replacer = EsperantoTextReplacer(
        placeholders_for_skipping_replacements=placeholders_for_skip,
        placeholders_for_localized_replacement=placeholders_for_local,
        replacements_list_for_localized_string=replacements_local,
        replacements_final_list=final_list,
        replacements_list_for_2char=two_char_list,
        format_type="HTML格式_Ruby文字_大小调整"
    )

    # デモ用の入力文字列 (本来はファイル読み込みや標準入力など)
    sample_text = """Hello, %これだけは置換しないでほしい% Esperanto world!
@Zamenhof@ is the initiator of Esperanto.
Mi iras al la parko. kaj finas.
ここで @Esperanto@ をローカル変換したい。"""

    # 実行
    replaced_result = replacer.run_replacement_pipeline(
        sample_text,
        skip_protect=True,
        localized_replace=True,
        use_parallel=False,
        num_processes=2
    )

    # 結果表示
    print("======== [置換前] ========")
    print(sample_text)
    print("======== [置換後] ========")
    print(replaced_result)

