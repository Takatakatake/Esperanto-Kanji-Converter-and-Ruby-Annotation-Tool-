# エスペラント文の文字列(漢字)置換ツール: 技術解説書

## はじめに

本解説書は、エスペラント文の文字列置換および漢字変換を行うStreamlitアプリケーションの技術的な仕組みを理解したい中級プログラマー向けに書かれています。このアプリは単なるテキスト置換ツールではなく、エスペラント語の構造を考慮した高度な処理システムを実装しており、その仕組みはエンジニアにとって大変興味深いものです。

本書では以下の点について詳細に解説します：

1. システムアーキテクチャの全体像
2. コードモジュールの相互関係
3. 核となるアルゴリズムと処理フロー
4. 重要な技術的工夫と実装パターン
5. データフローと状態管理の方法
6. 並列処理の実装方法

## 1. システムアーキテクチャの全体像

### 1.1 プロジェクト構成

このアプリケーションは以下の4つの主要ファイルで構成されています：

1. **main.py** - アプリケーションのメインエントリーポイント。Streamlitのインターフェースと置換処理の実行を担当。
2. **エスペラント文(漢字)置換用のJSONファイル生成ページ.py** - 置換ルールを定義するJSONファイルを生成するページ。
3. **esp_text_replacement_module.py** - エスペラント文の置換処理を行うコア機能を提供するモジュール。
4. **esp_replacement_json_make_module.py** - JSONファイル生成のためのユーティリティを提供するモジュール。

### 1.2 アーキテクチャの特徴

このアプリケーションは以下の特徴を持つアーキテクチャで設計されています：

1. **モジュラー設計**: 機能ごとに分離されたモジュール構造で、保守性と再利用性を高めています。
2. **関数型アプローチ**: 多くの処理が純粋関数として実装され、副作用を最小限に抑えています。
3. **パイプライン処理**: テキスト処理が複数の変換ステップを順番に適用するパイプラインとして実装されています。
4. **並列処理対応**: 大量のテキスト処理を効率化するために、マルチプロセッシング機能を実装しています。
5. **キャッシング**: Streamlitの`@st.cache_data`デコレータを使用して、JSONファイルの読み込みなど計算コストの高い処理の結果をキャッシュしています。

### 1.3 データフロー概要

アプリの主要なデータフローは以下の通りです：

1. ユーザーがエスペラント文をテキストエリアに入力、またはファイルとしてアップロード
2. 置換ルールが含まれるJSONファイルを読み込み（デフォルトまたはアップロード）
3. 入力テキストと置換ルールがエスペラント文置換エンジンに渡される
4. 一連の変換処理が適用され、出力形式に応じたテキストが生成
5. 結果がStreamlitインターフェースに表示され、ダウンロード可能なファイルとして提供

## 2. コードモジュールの詳細解析

各モジュールの役割と主要な機能を詳しく見ていきましょう。

### 2.1 main.py

この中心となるファイルは、Streamlitアプリケーションのエントリーポイントであり、以下の主要機能を持ちます：

#### 重要な機能とコンポーネント：

1. **Streamlitインターフェースの構築**:
   - ページ設定とレイアウト
   - ユーザー入力フォーム（テキストエリア、ファイルアップローダー、設定オプション）
   - 結果表示コンポーネント（タブによる分離表示）

2. **JSONデータ読み込み処理**:
   ```python
   @st.cache_data
   def load_replacements_lists(json_path: str) -> Tuple[List, List, List]:
   ```
   - `@st.cache_data`デコレータを使用してキャッシング
   - JSONから3種類の置換リストを取得（全域置換リスト、局所置換リスト、2文字語根置換リスト）

3. **テキスト処理の分岐**:
   ```python
   if use_parallel:
       processed_text = parallel_process(...)
   else:
       processed_text = orchestrate_comprehensive_esperanto_text_replacement(...)
   ```
   - 並列処理と単一プロセス処理の切り替え

4. **セッション状態の管理**:
   ```python
   initial_text = st.session_state.get("text0_value", "")
   st.session_state["text0_value"] = text0
   ```
   - テキスト入力の状態保持

5. **巨大テキスト対策**:
   ```python
   MAX_PREVIEW_LINES = 250
   lines = processed_text.splitlines()
   if len(lines) > MAX_PREVIEW_LINES:
       # 一部省略表示のロジック
   ```
   - 大量テキスト処理時のUIパフォーマンス対策

#### 処理フロー：

1. JSONファイルからの置換ルールの読み込み
2. ユーザー入力の取得（テキスト入力またはファイルアップロード）
3. 設定に基づいた処理方法の決定（並列・非並列）
4. `parallel_process`または`orchestrate_comprehensive_esperanto_text_replacement`による処理実行
5. 出力文字形式（上付き文字、x形式、^形式）への変換
6. 必要に応じたHTMLヘッダー・フッターの追加
7. 結果の表示とダウンロードオプションの提供

### 2.2 エスペラント文(漢字)置換用のJSONファイル生成ページ.py

このファイルは、エスペラント文置換処理で使用する置換ルールのJSONファイルを生成するStreamlitページを実装しています。

#### 重要な機能とコンポーネント：

1. **設定変数と定数**:
   ```python
   verb_suffix_2l = {'as':'as', 'is':'is', 'os':'os', ...}
   AN = [['dietan', '/diet/an/', '/diet/an'], ...]
   ON = [['duon', '/du/on/', '/du/on'], ...]
   ```
   - 動詞接尾辞、特殊語根（接尾辞）のリスト定義

2. **Streamlitインターフェース**:
   - ファイルアップロード（CSV、JSON）と設定オプション
   - 結果のダウンロード機能

3. **複数の置換リスト生成**:
   ```python
   # 主要な置換リスト生成フロー
   replacements_final_list = []
   replacements_list_for_localized_string = []
   replacements_list_for_2char = []
   ```
   - 3種類の置換リストを構築
   - 各置換リストには「元の文字列」→「置換後の文字列」→「プレースホルダー」の対応を格納

4. **並列・非並列の切り替え**:
   ```python
   if use_parallel:
       pre_replacements_dict_1 = parallel_build_pre_replacements_dict(...)
   else:
       # 非並列処理と進捗表示
   ```
   - 並列処理機能と進捗表示の実装

#### 処理フロー：

1. CSVからエスペラント語根と日本語訳/漢字の対応を読み込み
2. JSONから語根分解法設定を読み込み
3. プレースホルダーファイルの読み込み
4. エスペラント語根の置換処理と優先順位付け
   - 文字数の多い順に優先的に置換
   - 品詞ごとに接尾辞を考慮
5. 接尾辞・接頭辞の処理（2文字語根の特殊処理）
6. 置換リストを大文字・小文字・文頭大文字の3パターンに拡張
7. 3種類の置換リストをまとめたJSONファイルの生成

### 2.3 esp_text_replacement_module.py

このモジュールは、エスペラント文の置換処理の核となる機能を提供します。

#### 重要な機能とコンポーネント：

1. **エスペラント文字変換辞書**:
   ```python
   x_to_circumflex = {'cx': 'ĉ', 'gx': 'ĝ', ...}
   circumflex_to_x = {'ĉ': 'cx', 'ĝ': 'gx', ...}
   ```
   - 各種表記法の相互変換用辞書

2. **基本文字変換関数**:
   ```python
   def replace_esperanto_chars(text, char_dict: Dict[str, str]) -> str:
   def convert_to_circumflex(text: str) -> str:
   ```
   - 文字置換関数

3. **プレースホルダー処理**:
   ```python
   def safe_replace(text: str, replacements: List[Tuple[str, str, str]]) -> str:
   ```
   - 2段階置換（元テキスト→プレースホルダー→置換後テキスト）

4. **特殊マーカー処理**:
   ```python
   def find_percent_enclosed_strings_for_skipping_replacement(text: str) -> List[str]:
   def find_at_enclosed_strings_for_localized_replacement(text: str) -> List[str]:
   ```
   - %...%（置換スキップ）と@...@（局所置換）の処理

5. **メイン置換関数**:
   ```python
   def orchestrate_comprehensive_esperanto_text_replacement(...) -> str:
   ```
   - 複数の置換処理を統合するオーケストレーター

6. **並列処理機能**:
   ```python
   def parallel_process(...) -> str:
   def process_segment(...) -> str:
   ```
   - マルチプロセッシングによる並列処理

#### 処理フロー（orchestrate_comprehensive_esperanto_text_replacement）：

1. テキストの正規化と字上符形式への変換
2. %...%で囲まれた部分をプレースホルダーで一時置換
3. @...@で囲まれた部分の局所置換処理
4. 全域的な置換処理
5. 2文字語根の置換（2回繰り返し）
6. プレースホルダーの復元
7. 出力形式に応じた後処理

### 2.4 esp_replacement_json_make_module.py

このモジュールは主にJSONファイル生成のためのユーティリティを提供し、以下の機能を含みます：

#### 重要な機能とコンポーネント：

1. **文字変換辞書**（esp_text_replacement_module.pyと重複）

2. **文字幅測定関数**:
   ```python
   def measure_text_width_Arial16(text, char_widths_dict: Dict[str, int]) -> int:
   def insert_br_at_half_width(text, char_widths_dict: Dict[str, int]) -> str:
   ```
   - Arialフォントでの文字幅計算と改行挿入

3. **出力フォーマット処理**:
   ```python
   def output_format(main_text, ruby_content, format_type, char_widths_dict):
   ```
   - 様々な出力形式（HTML、括弧形式等）への変換

4. **ルビ文字の大文字化処理**:
   ```python
   def capitalize_ruby_and_rt(text: str) -> str:
   ```
   - HTMLルビタグ内の文字を大文字化

5. **並列処理関数**:
   ```python
   def process_chunk_for_pre_replacements(...) -> Dict[str, List[str]]:
   def parallel_build_pre_replacements_dict(...) -> Dict[str, List[str]]:
   ```
   - JSON生成時の並列処理

6. **冗長ルビ除去**:
   ```python
   def remove_redundant_ruby_if_identical(text: str) -> str:
   ```
   - 親文字列とルビ文字列が同一の場合にルビを削除

## 3. 核となるアルゴリズムと処理フロー

このセクションでは、アプリの中核となる処理アルゴリズムを詳細に解説します。

### 3.1 エスペラント文置換のコアアルゴリズム

置換処理の中心となるのは`orchestrate_comprehensive_esperanto_text_replacement`関数です。以下がその処理フローです：

1. **前処理**:
   - 空白文字の正規化
   - エスペラント特殊文字の字上符形式への統一

2. **保護処理**:
   - %...%で囲まれた部分をプレースホルダーに置換して保護

3. **局所置換**:
   - @...@で囲まれた部分を検出
   - その内部だけに置換リストを適用
   - 結果をプレースホルダーで保護

4. **全域置換**:
   - 文字数の長い単語から優先的に置換
   - 各置換対象をプレースホルダーに置換
   - 有効な置換のマッピングを保持

5. **2文字語根置換**:
   - 2文字語根のパターンを2回連続で置換
   - 最初の置換で生成された新しいパターンも対象に

6. **復元処理**:
   - プレースホルダーを置換後の文字列に戻す
   - 局所置換とスキップ部分を復元

7. **後処理**:
   - HTML形式の場合、改行タグ挿入や空白変換を実施

### 3.2 置換優先順位のアルゴリズム

効果的な置換を行うためには、単語の置換順序が重要です。このアプリでは以下の戦略を採用しています：

1. **文字数ベースの優先順位**:
   ```python
   # エスペラント単語の長さに基づく優先順位付け
   replacement_priority_by_length = len(esperanto_Word_before_replacement) * 10000
   ```
   - 長い単語ほど高い優先順位を持つ（短い単語の一部として誤認識されるのを防ぐ）

2. **品詞別の処理**:
   ```python
   # 動詞の場合、活用形への対応を追加
   if "动词" in j[1]:
       for k1, k2 in verb_suffix_2l_2.items():
           pre_replacements_dict_3[i+k1] = [j[0]+k2, j[2]+len(k1)*10000-3000]
   ```
   - 品詞に応じた接尾辞パターンの追加（名詞、形容詞、副詞、動詞）

3. **優先順位の微調整**:
   ```python
   # 既存でないものは優先順位を下げる
   pre_replacements_dict_3[i+k] = [j[0]+k, j[2]+len(k)*10000-5000]
   ```
   - 既存単語と派生形で優先順位を調整

4. **ソート処理**:
   ```python
   pre_replacements_list_2 = sorted(pre_replacements_list_1, key=lambda x: x[2], reverse=True)
   ```
   - 優先順位に従ってソート

### 3.3 二段階置換と競合回避のプレースホルダーアルゴリズム

競合を避けるための二段階置換は特に重要な技術です：

1. **プレースホルダー変換**:
   ```python
   def safe_replace(text: str, replacements: List[Tuple[str, str, str]]) -> str:
       valid_replacements = {}
       # まず old→placeholder
       for old, new, placeholder in replacements:
           if old in text:
               text = text.replace(old, placeholder)
               valid_replacements[placeholder] = new
       # 次に placeholder→new
       for placeholder, new in valid_replacements.items():
           text = text.replace(placeholder, new)
       return text
   ```
   - 一時的なプレースホルダーを使用して二段階で置換
   - 既に置換された部分が他の置換ルールで上書きされるのを防止

2. **占位符（プレースホルダー）の種類**:
   - 全域置換用（`$20987$-$499999$`）
   - 二文字語根置換用（`$13246$-$19834$`）
   - 局所置換用（`@20374@-@97648@`）
   - 置換スキップ用（`%1854%-%4934%`）

各プレースホルダーの範囲が重ならないように設計されています。

## 4. 技術的工夫とコードパターン

アプリケーション全体を通じて、いくつかの興味深い技術的工夫とパターンが見られます。

### 4.1 正規表現を使用したパターン検出

```python
# '%' で囲まれた箇所をスキップするための正規表現
PERCENT_PATTERN = re.compile(r'%(.{1,50}?)%')

# '@' で囲まれた箇所を局所置換するための正規表現
AT_PATTERN = re.compile(r'@(.{1,18}?)@')
```

特殊マーカー（%...%と@...@）を検出するために非貪欲（non-greedy）マッチングを使用し、最大文字数を制限しています。

### 4.2 マルチレベルの置換戦略

アプリは複数の置換レベルを持っています：

1. **グローバル置換** - すべてのテキストに適用
2. **ローカル置換** - @...@で囲まれた部分だけに適用
3. **保護領域** - %...%で囲まれた部分は置換から保護

これにより非常に柔軟なテキスト処理が可能になります。

### 4.3 キャッシングによるパフォーマンス最適化

```python
@st.cache_data
def load_replacements_lists(json_path: str) -> Tuple[List, List, List]:
```

Streamlitの`@st.cache_data`デコレータを使用して、JSONファイル読み込みの結果をキャッシュしています。これにより：

- 同じJSONに対する複数回の読み込み処理を回避
- レスポンス時間の短縮
- サーバーリソースの効率的な使用

### 4.4 単一責任原則の適用

各モジュールとクラスが明確に定義された責任を持っています：

- **main.py** - UIと処理フローの制御
- **esp_text_replacement_module.py** - テキスト置換ロジック
- **esp_replacement_json_make_module.py** - JSON生成ユーティリティ

### 4.5 ルビサイズの自動調整アルゴリズム

```python
def output_format(main_text, ruby_content, format_type, char_widths_dict):
    # HTML格式_Ruby文字_大小调整 の場合
    width_ruby = measure_text_width_Arial16(ruby_content, char_widths_dict)
    width_main = measure_text_width_Arial16(main_text, char_widths_dict)
    ratio_1 = width_ruby / width_main
    if ratio_1 > 6:
        return f'<ruby>{main_text}<rt class="XXXS_S">{insert_br_at_third_width(ruby_content, char_widths_dict)}</rt></ruby>'
    elif ratio_1 > (9/3):
        # ... 以下、比率に応じたサイズクラスの決定
```

1. 親文字とルビ文字の幅の比率を計算
2. 比率に基づいてルビのサイズクラスを決定
3. 長いルビに対しては自動的に改行を挿入

### 4.6 タイプヒントの活用

```python
def load_replacements_lists(json_path: str) -> Tuple[List, List, List]:
def safe_replace(text: str, replacements: List[Tuple[str, str, str]]) -> str:
```

Pythonの型ヒントを活用して、関数の入出力の型を明示し、コードの可読性と安全性を向上させています。

## 5. 並列処理の実装

大量のテキスト処理を効率化するために、アプリではPythonのmultiprocessingモジュールを活用した並列処理を実装しています。

### 5.1 並列処理の設計

```python
def parallel_process(
    text: str,
    num_processes: int,
    placeholders_for_skipping_replacements: List[str],
    replacements_list_for_localized_string: List[Tuple[str, str, str]],
    placeholders_for_localized_replacement: List[str],
    replacements_final_list: List[Tuple[str, str, str]],
    replacements_list_for_2char: List[Tuple[str, str, str]],
    format_type: str
) -> str:
```

並列処理のアプローチ：

1. テキストを行単位で分割
2. 分割されたチャンクをプロセス数に応じて配分
3. 各プロセスで`process_segment`関数を実行
4. 結果を結合して返す

### 5.2 プロセス起動方法

```python
try:
    multiprocessing.set_start_method("spawn")
except RuntimeError:
    pass  # すでに start method が設定済みの場合はここで無視する
```

Streamlitで`multiprocessing`を使用する際の注意点として、PicklingErrorを避けるために明示的に'spawn'モードを設定しています。

### 5.3 処理の最適化

```python
if num_processes <= 1 or num_lines <= 1:
    # 並列化しても意味がない場合は単一プロセスで処理
    return orchestrate_comprehensive_esperanto_text_replacement(...)
```

並列化のオーバーヘッドを考慮して、テキストが短い場合や並列プロセス数が1以下の場合は単一プロセスで処理するように最適化されています。

### 5.4 プールの使用

```python
with multiprocessing.Pool(processes=num_processes) as pool:
    results = pool.starmap(
        process_segment,
        [
            (
                lines[start:end],
                placeholders_for_skipping_replacements,
                # ... その他の引数
            )
            for (start, end) in ranges
        ]
    )
```

`multiprocessing.Pool`を使用して、プロセスプールを作成し、`starmap`メソッドを使って複数の引数と共に関数を並列実行しています。

## 6. 高度なHTMLルビ処理

アプリケーションでは、エスペラント文にルビを振るための高度なHTML処理を行っています。

### 6.1 ルビスタイルの調整

```python
# html形式におけるルビサイズの変更形式
ruby_style_head="""<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大多数の环境中で正常に运行するRuby显示功能</title>
    <style>
    html, body {
      -webkit-text-size-adjust: 100%;
      -moz-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
      text-size-adjust: 100%;
    }
```

様々なブラウザ環境でルビ表示が適切に機能するよう、詳細なCSSスタイルを定義しています。

### 6.2 ルビサイズクラス

```python
rt.XXXS_S {
  --ruby-font-size: 0.3em;
  margin-top: -8.3em !important;/* ルビの高さ位置はここで調節する。 */
  transform: translateY(-0em) !important;
}    
rt.XXS_S {
  --ruby-font-size: 0.3em;
  margin-top: -7.2em !important;/* ルビの高さ位置はここで調節する。 */
  transform: translateY(-0em) !important;
}
```

ルビの文字量に応じて8種類のサイズクラスを定義し、適切なサイズと位置になるよう調整しています。

### 6.3 冗長なルビの除去

```python
def remove_redundant_ruby_if_identical(text: str) -> str:
    """
    <ruby>xxx<rt class="XXL_L">xxx</rt></ruby> のように、
    親文字列とルビ文字列が完全に同一の場合に <ruby> を取り除く
    """
    def replacer(match: re.Match) -> str:
        group1 = match.group(1)
        group2 = match.group(2)
        if group1 == group2:
            return group1
        else:
            return match.group(0)
    replaced_text = IDENTICAL_RUBY_PATTERN.sub(replacer, text)
    return replaced_text
```

親文字列とルビ文字列が完全に同じ場合に、冗長なルビタグを削除してシンプルな表示にします。

## 7. JSON生成プロセスの実装

置換ルールを定義するJSONファイルの生成は、アプリの重要な機能の一つです。

### 7.1 置換リストの構築

```python
# 置換ルールとして使うリスト3種を作成
replacements_final_list = []        # 全域置換用
replacements_list_for_localized_string = []  # 局所置換用
replacements_list_for_2char = []    # 2文字語根置換用
```

### 7.2 CSVからのデータ読み込み

```python
for *, (E*root, hanzi_or_meaning) in CSV_data_imported.iterrows():
    if pd.notna(E_root) and pd.notna(hanzi_or_meaning) and '#' not in E_root and (E_root != '') and (hanzi_or_meaning != ''):
        temporary_replacements_dict[E_root] = [output_format(E_root, hanzi_or_meaning, format_type, char_widths_dict), len(E_root)]
```

CSVからエスペラント語根と対応する訳/漢字を読み込み、指定された出力形式でフォーマットします。

### 7.3 品詞別の処理

```python
if "名词" in j[1]:
    for k in ["o", "on", 'oj']:
        if not i+k in pre_replacements_dict_2:
            pre_replacements_dict_3[i+k] = [j[0]+k, j[2]+len(k)*10000-3000]
```

エスペラント語の品詞ごとに適切な接尾辞パターンを追加しています：
- 名詞: o, on, oj
- 形容詞: a, aj, an
- 副詞: e
- 動詞: as, is, os, us, at, it, ot, など

### 7.4 JSONファイルの最終構造

```python
combined_data = {}
combined_data["全域替换用のリスト(列表)型配列(replacements_final_list)"] = replacements_final_list
combined_data["二文字词根替换用のリスト(列表)型配列(replacements_list_for_2char)"] = replacements_list_for_2char
combined_data["局部文字替换用のリスト(列表)型配列(replacements_list_for_localized_string)"] = replacements_list_for_localized_string
```

最終的に3種類の置換リストを1つのJSONオブジェクトに統合し、ダウンロード可能なJSONファイルとして提供します。この構造は`main.py`の`load_replacements_lists`関数で解析され、アプリケーションの置換エンジンに供給されます。

### 7.5 大文字・小文字・文頭大文字の処理

```python
for old, new, place_holder in pre_replacements_list_3:
    pre_replacements_list_4.append((old, new, place_holder))
    pre_replacements_list_4.append((old.upper(), new.upper(), place_holder[:-1]+'up$'))
    if old[0] == ' ':
        pre_replacements_list_4.append((old[0] + old[1:].capitalize(), new[0] + capitalize_ruby_and_rt(new[1:]), place_holder[:-1]+'cap$'))
    else:
        pre_replacements_list_4.append((old.capitalize(), capitalize_ruby_and_rt(new), place_holder[:-1]+'cap$'))
```

各置換ルールに対して、以下の3つのバリエーションを作成しています：
1. 通常形（すべて小文字）
2. すべて大文字形（UPPER CASE）
3. 文頭大文字形（Capitalized）

これにより、文章中のどの位置に現れても適切に置換できるようになります。

## 8. エスペラント語の構造的な処理

このアプリケーションが一般的なテキスト置換ツールと大きく異なるのは、エスペラント語の言語的特性を考慮した構造的な処理を行っている点です。

### 8.1 エスペラント語の形態素解析的アプローチ

エスペラント語は語根と接尾辞が明確に分離できる構成的な言語です。アプリはこの特性を活用し、以下のような処理を行っています：

```python
# 動詞の基本形に対して、活用形を自動生成
if "动词" in j[1]:
    for k1, k2 in verb_suffix_2l_2.items():
        pre_replacements_dict_3[i+k1] = [j[0]+k2, j[2]+len(k1)*10000-3000]
```

例えば、`paroli`（話す）という動詞から以下の形式を自動生成します：
- `parolas`（話す、現在形）
- `parolis`（話した、過去形）
- `parolos`（話すだろう、未来形）
- `parolu`（話せ、命令形）
など

### 8.2 品詞ごとの接尾辞処理

エスペラント語の品詞は語尾で判別できます。このアプリはこの特性を利用して、品詞ごとに適切な語尾パターンを追加しています：

```python
# 名詞（-o, -on, -oj, -ojn）
if "名词" in j[1]:
    for k in ["o", "on", 'oj']:
        # ...

# 形容詞（-a, -an, -aj, -ajn）
if "形容词" in j[1]:
    for k in ["a", "aj", 'an']:
        # ...

# 副詞（-e）
if "副词" in j[1]:
    for k in ["e"]:
        # ...
```

これにより、基本語根から文法的に正しい変化形を自動生成し、置換の対象にしています。

### 8.3 特殊接尾辞と接頭辞の処理

エスペラント語には多数の接頭辞・接尾辞があり、これらを組み合わせることで新しい単語を形成します。アプリはこれらの特殊処理も行っています：

```python
# 接尾辞「-an」（〜の構成員）の特殊処理
for an in AN:
    if an[1].endswith("/an/"):
        i2 = an[1]
        i3 = re.sub(r"/an/$", "", i2)
        i4 = i3 + "/an/o"
        # ...

# 接尾辞「-on」（分数）の特殊処理
for on in ON:
    if on[1].endswith("/on/"):
        i2 = on[1]
        i3 = re.sub(r"/on/$", "", i2)
        i4 = i3 + "/on/o"
        # ...
```

例えば、`urb`（都市）から`urbano`（都市住民）のような派生形を適切に処理します。

### 8.4 2文字語根の特殊処理

エスペラント語には2文字の重要な語根や文法要素（al, el, de, da, la など）があり、これらは特別な処理が必要です：

```python
suffix_2char_roots = ['ad', 'ag', 'am', 'ar', 'as', 'at', ...]
prefix_2char_roots = ['al', 'am', 'av', 'bo', 'di', 'du', ...]
standalone_2char_roots = ['al', 'ci', 'da', 'de', 'di', 'do', ...]
```

これらの2文字語根に対しては、単独で使われる場合と接頭辞・接尾辞として使われる場合を区別して処理しています。例えば、`al`は単独で「〜へ」を意味する前置詞ですが、`alveni`のように接頭辞としても使用されます。

## 9. 高度なテキスト処理技術

アプリケーションで使用されている高度なテキスト処理技術について詳しく見ていきましょう。

### 9.1 二段階プレースホルダー置換の詳細

この技術は特に重要で、複数の置換ルールが競合する場合の問題を解決します：

```python
def safe_replace(text: str, replacements: List[Tuple[str, str, str]]) -> str:
    valid_replacements = {}
    # まず old→placeholder
    for old, new, placeholder in replacements:
        if old in text:
            text = text.replace(old, placeholder)
            valid_replacements[placeholder] = new
    # 次に placeholder→new
    for placeholder, new in valid_replacements.items():
        text = text.replace(placeholder, new)
    return text
```

例えば、「inter」（〜の間）と「internacia」（国際的な）というパターンがある場合：

1. 長い「internacia」を先に「$45678$」のようなプレースホルダーに置換
2. 短い「inter」を「$12345$」のようなプレースホルダーに置換
3. すべての置換が終わった後、各プレースホルダーを最終的な文字列に置換

これにより、「internacia」が「inter」という部分だけ置換されてしまう問題を防ぎます。

### 9.2 特殊マーカーの処理

%...%（置換スキップ）と@...@（局所置換）の処理は正規表現を使用して実装されています：

```python
def find_percent_enclosed_strings_for_skipping_replacement(text: str) -> List[str]:
    matches = []
    used_indices = set()
    for match in PERCENT_PATTERN.finditer(text):
        start, end = match.span()
        if start not in used_indices and end-2 not in used_indices:
            matches.append(match.group(1))
            used_indices.update(range(start, end))
    return matches
```

この実装には重要なポイントがあります：
- 重複検出を防ぐために`used_indices`を使用
- 入れ子になったマーカーを正しく処理するための範囲チェック
- 最大文字数の制限（50文字/18文字）

### 9.3 テキスト幅の測定とルビ調整

```python
def measure_text_width_Arial16(text, char_widths_dict: Dict[str, int]) -> int:
    total_width = 0
    for ch in text:
        char_width = char_widths_dict.get(ch, 8)
        total_width += char_width
    return total_width
```

この関数は、各文字のArialフォントでのピクセル幅を辞書から取得し、テキスト全体の幅を計算します。これは以下のように使用されます：

- ルビ文字と親文字の幅比率に基づくルビサイズの調整
- 長いルビテキストに対する改行位置の最適計算
- 適切なCSSクラスの選択

### 9.4 HTML生成の工夫

```python
def apply_ruby_html_header_and_footer(processed_text: str, format_type: str) -> str:
```

この関数は、出力形式に応じて適切なHTMLヘッダーとフッターを追加します：

- ルビサイズ調整用のCSSスタイル
- レスポンシブデザイン対応のメタタグ
- 最適な表示のためのフォント設定
- ブラウザ互換性を考慮したスタイル調整

特に、ルビの位置調整は複雑で、各ブラウザで適切に表示されるようCSSが細かく調整されています。

## 10. フロントエンドと処理エンジンの連携

Streamlitフロントエンドと処理エンジンがどのように連携しているかを詳しく見ていきましょう。

### 10.1 状態管理とセッション

```python
initial_text = st.session_state.get("text0_value", "")
# ...
st.session_state["text0_value"] = text0
```

Streamlitのセッション状態を使用して、テキスト入力などのユーザー状態を保持しています。これにより、ページのリロード間でもユーザーの入力が保持されます。

### 10.2 UI要素と処理のリンク

```python
submit_btn = st.form_submit_button('送信')
# ...
if submit_btn:
    # 入力テキストをセッションステートに保存しておく
    st.session_state["text0_value"] = text0
    # ...
    if use_parallel:
        processed_text = parallel_process(...)
    else:
        processed_text = orchestrate_comprehensive_esperanto_text_replacement(...)
```

フォーム送信ボタンがクリックされたときの処理ロジックを定義しています。ユーザーのUI操作がバックエンド処理にどのようにリンクしているかがわかります。

### 10.3 結果の表示方法

```python
if "HTML" in format_type:
    tab1, tab2 = st.tabs(["HTMLプレビュー", "置換結果（HTML ソースコード）"])
    with tab1:
        components.html(preview_text, height=500, scrolling=True)
    with tab2:
        st.text_area("", preview_text, height=300)
else:
    # HTML以外 (括弧形式 など) の場合はテキストタブに表示
    tab3_list = st.tabs(["置換結果テキスト"])
    with tab3_list[0]:
        st.text_area("", preview_text, height=300)
```

出力形式に応じて異なる表示方法を選択しています：
- HTML形式の場合は、プレビューとソースコードの2つのタブで表示
- その他の形式（括弧形式など）は、単一のテキストタブで表示

### 10.4 大きなテキストの扱い

```python
MAX_PREVIEW_LINES = 250
lines = processed_text.splitlines()
if len(lines) > MAX_PREVIEW_LINES:
    # 先頭247行 + "..." + 末尾3行のプレビュー
    first_part = lines[:247]
    last_part = lines[-3:]
    preview_text = "\n".join(first_part) + "\n...\n" + "\n".join(last_part)
    st.warning(f"テキストが長いため（総行数 {len(lines)} 行）、"
              "全文プレビューを一部省略しています。末尾3行も表示します。")
```

大量のテキストを処理する場合の最適化処理として、表示を一部省略するロジックを実装しています。これによりUIの応答性を保ちつつ、結果の概要を確認できるようになっています。

## 11. 高度なプログラミングテクニック

アプリケーション全体を通じて、いくつかの高度なプログラミングテクニックが使用されています。

### 11.1 関数型プログラミングの採用

```python
def orchestrate_comprehensive_esperanto_text_replacement(...) -> str:
```

多くの処理が純粋関数として実装されており、テキスト処理のパイプラインを構成しています。各関数は明確な入力と出力を持ち、副作用を最小限に抑えています。

### 11.2 エラーハンドリングの実装

```python
try:
    # デフォルトJSONをロード
    (replacements_final_list,
     replacements_list_for_localized_string,
     replacements_list_for_2char) = load_replacements_lists(default_json_path)
    st.success("デフォルトJSONの読み込みに成功しました。")
except Exception as e:
    st.error(f"JSONファイルの読み込みに失敗: {e}")
    st.stop()
```

適切な場所で例外処理を行い、エラーが発生した場合はユーザーフレンドリーなメッセージを表示して処理を停止しています。

### 11.3 遅延評価と最適化

```python
if i % 1000 == 0:
    current_count = i + 1
    progress_value = int(current_count / total_items * 100)

    # プログレスバー更新
    progress_bar.progress(progress_value)
    # テキスト表示を更新
    progress_text.write(f"{current_count}/{total_items} 件を処理中...")
```

長時間の処理中は、プログレスバーの更新頻度を制限することでパフォーマンスを確保しています。すべてのステップでUIを更新するのではなく、1000ステップごとに更新しています。

### 11.4 正規表現の効果的な活用

```python
IDENTICAL_RUBY_PATTERN = re.compile(r'<ruby>([^<]+)<rt class="XXL_L">([^<]+)</rt></ruby>')
```

複雑なパターンマッチングには正規表現を効果的に使用しています。特にHTMLタグのような構造的なパターンの処理に適しています。

### 11.5 デコレータの活用

```python
@st.cache_data
def load_replacements_lists(json_path: str) -> Tuple[List, List, List]:
```

Streamlitのキャッシングデコレータを使用して、計算コストの高い関数の結果をキャッシュしています。これにより、同じJSONファイルに対する複数回の読み込み処理を避けることができます。

## 12. パフォーマンス最適化

アプリケーションでは、大量のテキスト処理を効率化するためのパフォーマンス最適化が行われています。

### 12.1 データ構造の最適化

```python
# 一旦辞書型を使う。(後で内容(value)を更新するため)
temporary_replacements_dict = {}
# ...
# 辞書型をリスト型に戻した上で、文字数順に並び替え。
temporary_replacements_list_1 = []
for old, new in temporary_replacements_dict.items():
    temporary_replacements_list_1.append((old, new[0], new[1]))
temporary_replacements_list_2 = sorted(temporary_replacements_list_1, key=lambda x: x[2], reverse=True)
```

データ構造を処理の目的に合わせて選択しています：
- 更新が必要な場合は辞書を使用
- ソートが必要な場合はリストに変換
- 検索が頻繁な場合はセットやマップを使用

### 12.2 アルゴリズムの効率化

```python
# キーが存在するかの検索は O(1) の辞書操作
if not i+k in pre_replacements_dict_2:
    pre_replacements_dict_3[i+k] = [j[0]+k, j[2]+len(k)*10000-3000]
```

O(n)の線形探索ではなく、O(1)の辞書検索を使用してパフォーマンスを向上させています。

### 12.3 並列処理の最適化

```python
def parallel_process(...):
    # ...
    if num_processes <= 1 or num_lines <= 1:
        # 並列化しても意味がない場合は単一プロセスで処理
        return orchestrate_comprehensive_esperanto_text_replacement(...)
```

並列化のオーバーヘッドを考慮して、小さなテキストに対しては並列処理を回避しています。

### 12.4 メモリ使用量の最適化

```python
# 辞書に直接追加
pre_replacements_dict_1[j[0]] = [safe_replace(j[0], temporary_replacements_list_final), j[1]]
```

大量のデータを扱う際にも、中間リストを作成せず、直接辞書に追加することでメモリ使用量を抑えています。

### 12.5 ユーザーインターフェースの応答性

```python
# 先頭247行 + "..." + 末尾3行のプレビュー
first_part = lines[:247]
last_part = lines[-3:]
preview_text = "\n".join(first_part) + "\n...\n" + "\n".join(last_part)
```

大量のテキストを処理する場合でも、UIの応答性を確保するために表示を最適化しています。

## 13. カスタマイズと拡張

このアプリケーションは、様々な方法でカスタマイズや拡張が可能です。中級プログラマーが検討できるカスタマイズポイントを見ていきましょう。

### 13.1 CSVフォーマットの拡張

現在、CSVは主にエスペラント語根と日本語訳/漢字の対応を定義していますが、以下のような拡張が考えられます：

- 品詞情報の追加（現在はJSONで定義）
- 優先順位の直接指定
- コンテキスト依存の置換ルール

### 13.2 新しい出力形式の追加

現在サポートされているHTML形式や括弧形式に加えて、以下のような新しい出力形式の追加が可能です：

```python
def output_format(main_text, ruby_content, format_type, char_widths_dict):
    # 既存の形式
    if format_type == 'HTML格式_Ruby文字_大小调整':
        # ...
    # 新しい形式の追加
    elif format_type == '新形式':
        # 新しい形式の実装
        return f'...{main_text}...{ruby_content}...'
```

例えば、以下のような出力形式が考えられます：
- マークダウン形式
- LaTeX形式
- インタラクティブな形式（JavaScript機能付きHTML）

### 13.3 プレースホルダーシステムの拡張

現在のプレースホルダーシステムは、%...%（スキップ）と@...@（局所置換）をサポートしていますが、さらに多様な制御が可能です：

- 特定の置換ルールのみを適用する指定
- 複数レベルの置換優先度
- 条件付き置換（前後の文脈に依存）

### 13.4 語彙データベースの拡張

アプリケーションの中核は置換ルールのデータベースですが、これを拡張することで機能を向上させることができます：

- 例文のデータベース追加
- エスペラント語の語源情報の追加
- 頻度情報の統合（学習者向け）

### 13.5 AIサポートの統合

現代のテキスト処理では、AI技術の統合も考えられます：

- エスペラント文の自動検出と解析
- 置換提案の自動生成
- 文法チェックやスタイル提案

## 14. まとめと発展的な考察

### 14.1 アプリケーションの技術的特徴のまとめ

このエスペラント文字列置換ツールは、以下の技術的特徴を備えた高度なテキスト処理システムです：

1. **言語構造を考慮した処理**: 一般的な置換ツールとは異なり、エスペラント語の文法構造や品詞特性を考慮した処理を行っています。

2. **階層的な置換戦略**: 単純な置換ではなく、プレースホルダーを使用した二段階置換や、グローバル/ローカルの置換レベルなど、階層的な戦略を採用しています。

3. **最適化されたパフォーマンス**: 並列処理、キャッシング、効率的なデータ構造の使用により、大量のテキスト処理にも対応しています。

4. **柔軟なカスタマイズ**: CSVやJSONによる置換ルールの定義や、様々な出力形式のサポートなど、柔軟なカスタマイズが可能です。

5. **ユーザーフレンドリーなインターフェース**: Streamlitを活用した直感的なインターフェースと、プログレス表示やエラーハンドリングによる良好なユーザー体験を提供しています。

### 14.2 発展的な考察

このアプリケーションの技術やアプローチは、他の言語処理タスクや類似アプリケーションにも応用できます：

1. **他の構成的言語への応用**: エスペラント語と同様に構成的な特性を持つ他の言語（トルコ語、フィンランド語など）にも適用できる可能性があります。

2. **専門用語の処理**: 医学や法律などの専門分野の用語置換や解説付与にも応用できるでしょう。

3. **教育支援ツール**: 言語学習における単語や文法構造の可視化ツールとして発展させることができます。

4. **複数言語間のマッピング**: 異なる言語間の語彙マッピングや対訳生成にも応用可能なアプローチです。

5. **テキスト解析パイプライン**: 文書解析や情報抽出のための前処理パイプラインとしても応用できます。

### 14.3 今後の展望

このアプリケーションは既に優れた機能を持っていますが、さらなる発展の余地もあります：

1. **機械学習の統合**: エスペラント語の構造解析や訳語提案に機械学習モデルを統合することで、さらに高度な処理が可能になるでしょう。

2. **コミュニティ貢献**: 語彙データベースをオープンソース化し、コミュニティでの拡充を促進することで、より包括的なリソースになる可能性があります。

3. **リアルタイム処理**: WebSocketなどを活用して入力と同時にリアルタイムで置換結果を表示する機能の実装も考えられます。

4. **モバイル対応**: PWA（Progressive Web App）として実装し、オフラインでも使用できるモバイルフレンドリーなバージョンの開発も価値があるでしょう。

5. **API化**: 置換エンジンをAPIとして提供し、他のアプリケーションから利用できるようにすることも考えられます。

## 15. 付録: 主要クラスと関数の概要

最後に、アプリケーションの主要な関数とその役割をまとめておきます。

### 15.1 main.py

- `load_replacements_lists`: 置換ルールのJSONを読み込み、3種類のリストを返す
- `unify_halfwidth_spaces`: 半角スペースを統一する
- `convert_to_circumflex`: エスペラント文字を字上符形式に変換する

### 15.2 esp_text_replacement_module.py

- `replace_esperanto_chars`: 文字変換辞書に基づいてエスペラント文字を変換
- `safe_replace`: プレースホルダーを使用した二段階置換を実行
- `find_percent_enclosed_strings_for_skipping_replacement`: %...%で囲まれた部分を検出
- `find_at_enclosed_strings_for_localized_replacement`: @...@で囲まれた部分を検出
- `orchestrate_comprehensive_esperanto_text_replacement`: 置換処理のメインオーケストレーター
- `parallel_process`: テキストを分割して並列処理
- `apply_ruby_html_header_and_footer`: HTML出力にヘッダーとフッターを追加

### 15.3 esp_replacement_json_make_module.py

- `measure_text_width_Arial16`: Arialフォントでのテキスト幅を計算
- `insert_br_at_half_width`: テキスト幅の半分の位置に改行を挿入
- `output_format`: 指定された形式でテキストをフォーマット
- `capitalize_ruby_and_rt`: ルビタグ内の文字を大文字化
- `process_chunk_for_pre_replacements`: 並列処理用のチャンク処理
- `remove_redundant_ruby_if_identical`: 冗長なルビを削除

これらの関数を理解し、必要に応じてカスタマイズすることで、アプリケーションの機能を拡張したり、類似のテキスト処理ツールを開発したりすることができます。

以上で、エスペラント文の文字列(漢字)置換ツールの技術解説書を終わります。このアプリケーションは、単なるテキスト置換ツールを超えた、言語構造を考慮した高度なテキスト処理システムであり、そのアプローチや技術は他の言語処理タスクにも応用できる価値があります。
