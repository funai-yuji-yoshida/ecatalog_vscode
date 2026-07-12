"""
動的電子カタログ作成アプリ - FlipHTML5風UI
A4見開きページ形式の電子カタログを動的に生成します。
"""

import streamlit as st
import pandas as pd
import base64
import json
import os
from pathlib import Path
from io import BytesIO

# ページ設定
st.set_page_config(
    page_title="電子カタログ作成アプリ",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッションステートの初期化
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0
if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = {}
if 'block_selections' not in st.session_state:
    st.session_state.block_selections = {}

def load_csv(file, encoding='shift_jis'):
    """CSVファイルを読み込む"""
    try:
        df = pd.read_csv(file, encoding=encoding)
        return df
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file, encoding='cp932')
            return df
        except:
            df = pd.read_csv(file, encoding='utf-8')
            return df

def image_to_base64(image_data):
    """画像データをBase64エンコード"""
    if isinstance(image_data, bytes):
        return base64.b64encode(image_data).decode()
    else:
        buffered = BytesIO()
        image_data.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

def load_images_from_folder(folder_path, product_codes):
    """フォルダから画像を読み込む"""
    images = {}
    if not os.path.exists(folder_path):
        return images

    for code in product_codes:
        # 複数の拡張子に対応
        for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
            img_path = os.path.join(folder_path, f"{code}{ext}")
            if os.path.exists(img_path):
                with open(img_path, 'rb') as f:
                    images[code] = base64.b64encode(f.read()).decode()
                break
    return images

def generate_catalog_html(blocks_per_page, left_blocks, right_blocks, design_config):
    """見開きカタログのHTMLを生成"""

    # CSSスタイル
    css = f"""
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}

        .catalog-container {{
            perspective: 2000px;
            width: 100%;
            max-width: 1400px;
        }}

        .catalog-spread {{
            display: flex;
            background: white;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.6s ease;
        }}

        .catalog-spread:hover {{
            transform: translateY(-5px);
            box-shadow: 0 25px 70px rgba(0,0,0,0.4);
        }}

        .page {{
            flex: 1;
            padding: 30px;
            position: relative;
        }}

        .page-left {{
            border-right: 2px solid #e0e0e0;
            background: linear-gradient(to right, #ffffff 0%, #fafafa 100%);
        }}

        .page-right {{
            background: linear-gradient(to left, #ffffff 0%, #fafafa 100%);
        }}

        .page-number {{
            position: absolute;
            bottom: 15px;
            font-size: 12px;
            color: #999;
            font-weight: bold;
        }}

        .page-left .page-number {{
            left: 15px;
        }}

        .page-right .page-number {{
            right: 15px;
        }}

        .blocks-grid {{
            display: grid;
            gap: 20px;
            height: 100%;
        }}

        .grid-1 {{ grid-template-columns: 1fr; }}
        .grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
        .grid-4 {{ grid-template-columns: repeat(2, 1fr); grid-template-rows: repeat(2, 1fr); }}
        .grid-6 {{ grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); }}
        .grid-8 {{ grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(2, 1fr); }}

        .product-block {{
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: {design_config['padding']}px;
            background: white;
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
            overflow: hidden;
        }}

        .product-block:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
            border-color: {design_config['header_color']};
        }}

        .product-image {{
            width: 100%;
            height: 150px;
            object-fit: contain;
            margin-bottom: 10px;
            background: #f9f9f9;
            border-radius: 4px;
        }}

        .product-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: {design_config['font_size']}px;
        }}

        .product-table th {{
            background: {design_config['header_color']};
            color: white;
            padding: {design_config['padding']}px;
            text-align: left;
            font-weight: bold;
            border: 1px solid {design_config['border_color']};
        }}

        .product-table td {{
            padding: {design_config['padding']}px;
            border: 1px solid {design_config['border_color']};
            background: white;
        }}

        .product-table tr:nth-child(even) td {{
            background: #f8f9fa;
        }}

        .navigation {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 30px;
        }}

        .nav-button {{
            background: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .nav-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            background: #667eea;
            color: white;
        }}

        .nav-button:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}

        .no-data {{
            color: #999;
            text-align: center;
            padding: 20px;
            font-style: italic;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .navigation {{
                display: none;
            }}
        }}
    </style>
    """

    # ブロック生成関数
    def create_block_html(block_data):
        if not block_data:
            return '<div class="product-block"><div class="no-data">商品が選択されていません</div></div>'

        image_html = ''
        if block_data.get('image'):
            image_html = f'<img src="data:image/png;base64,{block_data["image"]}" class="product-image" alt="{block_data.get("name", "商品画像")}">'

        table_rows = ''
        for col, value in block_data.get('data', {}).items():
            table_rows += f'<tr><th>{col}</th><td>{value}</td></tr>'

        return f'''
        <div class="product-block">
            {image_html}
            <table class="product-table">
                {table_rows}
            </table>
        </div>
        '''

    # グリッドクラス決定
    grid_class = f"grid-{blocks_per_page}"

    # 左ページのブロック生成
    left_html = ''.join([create_block_html(block) for block in left_blocks])

    # 右ページのブロック生成
    right_html = ''.join([create_block_html(block) for block in right_blocks])

    # 完全なHTML
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>電子カタログ</title>
        {css}
    </head>
    <body>
        <div class="catalog-container">
            <div class="catalog-spread">
                <div class="page page-left">
                    <div class="blocks-grid {grid_class}">
                        {left_html}
                    </div>
                    <div class="page-number">Page {st.session_state.current_page * 2 + 1}</div>
                </div>
                <div class="page page-right">
                    <div class="blocks-grid {grid_class}">
                        {right_html}
                    </div>
                    <div class="page-number">Page {st.session_state.current_page * 2 + 2}</div>
                </div>
            </div>
            <div class="navigation">
                <button class="nav-button" onclick="window.parent.postMessage({{type: 'prev'}}, '*')"
                        id="prevBtn">
                    ◀ 前のページ
                </button>
                <button class="nav-button" onclick="window.parent.postMessage({{type: 'next'}}, '*')"
                        id="nextBtn">
                    次のページ ▶
                </button>
            </div>
        </div>
        <script>
            // Streamlitとの通信
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'updatePage') {{
                    window.location.reload();
                }}
            }});
        </script>
    </body>
    </html>
    """

    return html


# ========== サイドバー: コントロールパネル ==========
with st.sidebar:
    st.title("📖 電子カタログ設定")

    # CSV読み込み
    st.header("1️⃣ データ読み込み")
    uploaded_csv = st.file_uploader("CSVファイルをアップロード", type=['csv'])

    if uploaded_csv:
        st.session_state.df = load_csv(uploaded_csv)
        st.success(f"✅ {len(st.session_state.df)}件のデータを読み込みました")

        # データプレビュー
        with st.expander("📊 データプレビュー"):
            st.dataframe(st.session_state.df.head(10), use_container_width=True)

    # レイアウト設定
    st.header("2️⃣ レイアウト設定")
    blocks_per_page = st.selectbox(
        "1ページあたりのブロック数",
        options=[1, 2, 4, 6, 8],
        index=2,
        help="見開き1ページ（左または右）に表示する商品ブロック数"
    )

    # カラム選択
    st.header("3️⃣ 表示項目選択")
    if st.session_state.df is not None:
        selected_columns = st.multiselect(
            "表示するカラム（スペック項目）",
            options=st.session_state.df.columns.tolist(),
            default=st.session_state.df.columns.tolist()[:5] if len(st.session_state.df.columns) >= 5 else st.session_state.df.columns.tolist(),
            help="選択したカラムのみがテーブルに表示されます"
        )

        product_id_column = st.selectbox(
            "商品識別カラム（画像マッチング用）",
            options=st.session_state.df.columns.tolist(),
            index=0,
            help="画像ファイル名とマッチングするカラムを選択"
        )
    else:
        selected_columns = []
        product_id_column = None

    # 画像読み込み
    st.header("4️⃣ 画像設定")
    image_mode = st.radio(
        "画像の読み込み方法",
        options=["フォルダ指定", "ファイルアップロード"],
        horizontal=True
    )

    if image_mode == "フォルダ指定":
        folder_path = st.text_input(
            "画像フォルダのパス",
            placeholder="例: C:/images/products",
            help="商品コードと一致するファイル名の画像を自動検索"
        )
        if folder_path and st.session_state.df is not None and product_id_column:
            product_codes = st.session_state.df[product_id_column].astype(str).tolist()
            st.session_state.uploaded_images = load_images_from_folder(folder_path, product_codes)
            st.info(f"🖼️ {len(st.session_state.uploaded_images)}枚の画像を読み込みました")
    else:
        uploaded_files = st.file_uploader(
            "画像ファイルをアップロード",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True
        )
        if uploaded_files:
            st.session_state.uploaded_images = {}
            for file in uploaded_files:
                # ファイル名から拡張子を除いた部分を商品コードとする
                code = Path(file.name).stem
                st.session_state.uploaded_images[code] = image_to_base64(file.read())
            st.info(f"🖼️ {len(st.session_state.uploaded_images)}枚の画像をアップロードしました")

    # デザイン設定
    st.header("5️⃣ デザイン設定")
    header_color = st.color_picker("テーブルヘッダー色", "#667eea")
    border_color = st.color_picker("枠線の色", "#dddddd")
    font_size = st.slider("フォントサイズ (px)", 10, 28, 14)
    padding = st.slider("セル余白 (px)", 5, 25, 10)

    design_config = {
        'header_color': header_color,
        'border_color': border_color,
        'font_size': font_size,
        'padding': padding
    }

# ========== 商品選択パネル ==========
st.title("📝 商品配置設定")

if st.session_state.df is not None and selected_columns:
    # ページナビゲーション
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 前のページ", use_container_width=True):
            if st.session_state.current_page > 0:
                st.session_state.current_page -= 1
                st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>見開き {st.session_state.current_page + 1}</h3>",
                   unsafe_allow_html=True)
    with col3:
        if st.button("次のページ ➡️", use_container_width=True):
            st.session_state.current_page += 1
            st.rerun()

    st.divider()

    # 左右ページの商品選択
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("📄 左ページ")
        left_blocks = []
        for i in range(blocks_per_page):
            with st.expander(f"ブロック {i+1}", expanded=(i==0)):
                key = f"left_{st.session_state.current_page}_{i}"
                selected_product = st.selectbox(
                    "商品を選択",
                    options=["未選択"] + st.session_state.df[product_id_column].astype(str).tolist(),
                    key=key
                )

                if selected_product != "未選択":
                    product_row = st.session_state.df[
                        st.session_state.df[product_id_column].astype(str) == selected_product
                    ].iloc[0]

                    block_data = {
                        'name': selected_product,
                        'data': {col: product_row[col] for col in selected_columns},
                        'image': st.session_state.uploaded_images.get(str(selected_product), '')
                    }
                    left_blocks.append(block_data)
                else:
                    left_blocks.append(None)

    with right_col:
        st.subheader("📄 右ページ")
        right_blocks = []
        for i in range(blocks_per_page):
            with st.expander(f"ブロック {i+1}", expanded=(i==0)):
                key = f"right_{st.session_state.current_page}_{i}"
                selected_product = st.selectbox(
                    "商品を選択",
                    options=["未選択"] + st.session_state.df[product_id_column].astype(str).tolist(),
                    key=key
                )

                if selected_product != "未選択":
                    product_row = st.session_state.df[
                        st.session_state.df[product_id_column].astype(str) == selected_product
                    ].iloc[0]

                    block_data = {
                        'name': selected_product,
                        'data': {col: product_row[col] for col in selected_columns},
                        'image': st.session_state.uploaded_images.get(str(selected_product), '')
                    }
                    right_blocks.append(block_data)
                else:
                    right_blocks.append(None)

    # カタログプレビュー
    st.divider()
    st.subheader("👁️ カタログプレビュー")

    catalog_html = generate_catalog_html(blocks_per_page, left_blocks, right_blocks, design_config)
    st.components.v1.html(catalog_html, height=800, scrolling=True)

    # HTML出力
    st.divider()
    st.subheader("💾 出力")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 HTMLをダウンロード", use_container_width=True):
            st.download_button(
                label="⬇️ ダウンロード実行",
                data=catalog_html,
                file_name=f"catalog_spread_{st.session_state.current_page + 1}.html",
                mime="text/html",
                use_container_width=True
            )

    with col2:
        if st.button("🖨️ 印刷プレビュー", use_container_width=True):
            st.info("ブラウザの印刷機能（Ctrl+P）をご利用ください")

else:
    st.info("👈 左のサイドバーからCSVファイルをアップロードしてください")

    # サンプル情報
    st.markdown("""
    ### 📖 使い方

    1. **CSVデータを読み込み**: 左サイドバーから商品データのCSVファイルをアップロード
    2. **レイアウト選択**: 1ページあたりのブロック数（商品数）を選択
    3. **表示項目設定**: カタログに表示したいカラム（スペック項目）を選択
    4. **画像設定**: フォルダ指定またはファイルアップロードで商品画像を読み込み
    5. **デザイン調整**: 色・フォントサイズ・余白をカスタマイズ
    6. **商品配置**: 各ブロックに表示する商品を選択
    7. **プレビュー確認**: リアルタイムで見開きカタログを確認
    8. **出力**: HTMLファイルとしてダウンロードまたは印刷

    ### 💡 特徴

    - ✨ FlipHTML5風の美しい見開きUI
    - 🎨 リアルタイムデザイン変更
    - 📊 CSV動的バインディング
    - 🖼️ 画像の自動マッチング
    - 📱 レスポンシブ対応
    - 🖨️ 印刷最適化済み
    """)

# フッター
st.divider()
st.markdown("""
<div style='text-align: center; color: #999; padding: 20px;'>
    <p>電子カタログ作成アプリ v1.0 | Powered by Streamlit</p>
</div>
""", unsafe_allow_html=True)
