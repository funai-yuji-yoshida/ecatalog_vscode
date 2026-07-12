"""
動的電子カタログ作成アプリ - 商品グループブロック型
見開きページに商品グループブロックを配置
"""

import streamlit as st
import pandas as pd
import base64
import json
import os
from pathlib import Path
from io import BytesIO
try:
    from xhtml2pdf import pisa
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ページ設定
st.set_page_config(
    page_title="電子カタログ作成アプリ",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッションステートの初期化
if 'df' not in st.session_state:
    st.session_state.df = None
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = {}
if 'current_spread' not in st.session_state:
    st.session_state.current_spread = 0
if 'spread_blocks' not in st.session_state:
    st.session_state.spread_blocks = {}  # {spread_idx: {page: [blocks]}}

def load_csv(file):
    """CSVファイルを読み込む"""
    file.seek(0)
    encodings = ['utf-8', 'shift_jis', 'cp932', 'utf-8-sig', 'iso-2022-jp', 'euc-jp']
    for enc in encodings:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=enc)
            if len(df.columns) > 0 and not df.empty:
                return df
        except:
            continue
    raise ValueError("CSVファイルのエンコーディングを検出できませんでした。")

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
        for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
            img_path = os.path.join(folder_path, f"{code}{ext}")
            if os.path.exists(img_path):
                with open(img_path, 'rb') as f:
                    images[code] = base64.b64encode(f.read()).decode()
                break
    return images

def generate_spread_html(left_blocks, right_blocks, design_config, spread_number, pdf_mode=False):
    """見開きページのHTMLを生成"""

    # PDF用の簡素化されたCSS
    if pdf_mode:
        css = f"""
        <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'MS Gothic', 'Yu Gothic', sans-serif;
            background: white;
            padding: 10px;
        }}

        .spread {{
            display: table;
            width: 100%;
        }}

        .page {{
            display: table-cell;
            width: 50%;
            padding: 10px;
            vertical-align: top;
        }}

        .product-group-block {{
            border: 2px solid #333;
            margin-bottom: 15px;
            page-break-inside: avoid;
        }}

        .block-category-header {{
            background: #2c5aa0;
            color: white;
            padding: 8px 12px;
            font-size: {design_config['font_size'] + 2}px;
            font-weight: bold;
        }}

        .block-product-title {{
            background: #f0f0f0;
            padding: 10px 12px;
            font-size: {design_config['font_size'] + 1}px;
            font-weight: bold;
            border-bottom: 1px solid #ccc;
        }}

        .block-specs {{
            padding: 8px 12px;
            background: white;
            border-bottom: 1px solid #ccc;
        }}

        .spec-item {{
            font-size: {design_config['font_size'] - 1}px;
            margin: 3px 0;
        }}

        .block-images {{
            text-align: center;
            padding: 10px;
            background: #fafafa;
            border-bottom: 1px solid #ccc;
        }}

        .block-image {{
            max-width: 120px;
            max-height: 100px;
            margin: 5px;
        }}

        .image-label {{
            font-size: {design_config['font_size'] - 2}px;
            color: #666;
        }}

        .block-variants-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: {design_config['font_size'] - 1}px;
        }}

        .block-variants-table th {{
            background: #2c5aa0;
            color: white;
            padding: 6px;
            text-align: left;
            border: 1px solid #fff;
        }}

        .block-variants-table td {{
            padding: 6px;
            border: 1px solid #ccc;
        }}

        .order-number-cell {{
            background: #ff9800;
            color: white;
            font-weight: bold;
            text-align: center;
        }}

        .price-cell {{
            font-weight: bold;
            color: #d32f2f;
            text-align: right;
        }}

        .barcode-cell {{
            text-align: center;
            font-family: monospace;
            font-size: {design_config['font_size'] - 2}px;
        }}

        .page-number {{
            text-align: center;
            color: #999;
            font-size: 10px;
            margin-top: 10px;
        }}
        </style>
        """
    else:
        # 通常表示用のCSS（既存のまま）
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
            padding: 20px;
        }}

        .spread-container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        .spread {{
            display: flex;
            gap: 20px;
            background: transparent;
        }}

        .page {{
            flex: 1;
            background: white;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            border-radius: 8px;
            min-height: 1000px;
        }}

        .page-number {{
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 15px;
            font-weight: bold;
        }}

        .product-group-block {{
            border: 2px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 25px;
            background: white;
        }}

        .product-group-block:last-child {{
            margin-bottom: 0;
        }}

        .block-category-header {{
            background: linear-gradient(135deg, #2c5aa0 0%, #1e3c72 100%);
            color: white;
            padding: 10px 15px;
            font-size: {design_config['font_size'] + 2}px;
            font-weight: bold;
        }}

        .block-category-header::before {{
            content: "★ ";
        }}

        .block-product-title {{
            background: #f8f9fa;
            padding: 12px 15px;
            font-size: {design_config['font_size'] + 1}px;
            font-weight: bold;
            color: #333;
            border-bottom: 1px solid #e0e0e0;
        }}

        .block-specs {{
            padding: 10px 15px;
            background: white;
            border-bottom: 1px solid #e0e0e0;
        }}

        .spec-item {{
            font-size: {design_config['font_size'] - 1}px;
            color: #555;
            margin: 4px 0;
        }}

        .spec-item::before {{
            content: "■ ";
            color: #2c5aa0;
        }}

        .block-images {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: #fafafa;
            border-bottom: 1px solid #e0e0e0;
            flex-wrap: wrap;
        }}

        .block-image-wrapper {{
            text-align: center;
        }}

        .block-image {{
            max-width: 150px;
            max-height: 120px;
            object-fit: contain;
            background: white;
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }}

        .image-label {{
            font-size: {design_config['font_size'] - 2}px;
            color: #666;
            margin-top: 5px;
        }}

        .block-variants-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: {design_config['font_size'] - 1}px;
        }}

        .block-variants-table thead {{
            background: linear-gradient(135deg, #2c5aa0 0%, #1e3c72 100%);
            color: white;
        }}

        .block-variants-table th {{
            padding: 8px;
            text-align: left;
            font-weight: 600;
            border: 1px solid rgba(255,255,255,0.3);
            font-size: {design_config['font_size'] - 1}px;
        }}

        .block-variants-table tbody tr {{
            border-bottom: 1px solid #e0e0e0;
        }}

        .block-variants-table tbody tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .block-variants-table td {{
            padding: 8px;
            border: 1px solid #e0e0e0;
        }}

        .order-number-cell {{
            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
            color: white;
            font-weight: bold;
            text-align: center;
            font-size: {design_config['font_size']}px;
        }}

        .price-cell {{
            font-weight: bold;
            color: #d32f2f;
            text-align: right;
        }}

        .barcode-cell {{
            text-align: center;
            font-family: 'Courier New', monospace;
            font-size: {design_config['font_size'] - 2}px;
        }}

        .empty-block {{
            padding: 40px;
            text-align: center;
            color: #ccc;
            font-style: italic;
            background: #fafafa;
        }}
    </style>
    """

    def create_group_block_html(block_data):
        if not block_data or not block_data.get('records'):
            return '<div class="product-group-block"><div class="empty-block">ブロック未設定</div></div>'

        category = block_data.get('category', '')
        title = block_data.get('title', '商品名')
        specs = block_data.get('specs', [])
        images = block_data.get('images', [])
        records = block_data.get('records', [])

        # カテゴリヘッダー（メーカー名など）
        category_html = ''
        if category:
            # PDF用は★を直接テキストに含める
            if pdf_mode:
                category_html = f'<div class="block-category-header">★ {category}</div>'
            else:
                category_html = f'<div class="block-category-header">{category}</div>'

        # 商品タイトル
        title_html = f'<div class="block-product-title">{title}</div>'

        # スペック
        specs_html = ''
        if specs:
            # PDF用は■を直接テキストに含める
            if pdf_mode:
                specs_items = ''.join([f'<div class="spec-item">■ {spec}</div>' for spec in specs])
            else:
                specs_items = ''.join([f'<div class="spec-item">{spec}</div>' for spec in specs])
            specs_html = f'<div class="block-specs">{specs_items}</div>'

        # 画像
        images_html = ''
        if images:
            imgs = ''
            for img in images:
                img_data = img.get('data', '')
                img_label = img.get('label', '')
                if img_data:
                    imgs += f'''
                    <div class="block-image-wrapper">
                        <img src="data:image/png;base64,{img_data}" class="block-image" alt="{img_label}">
                        <div class="image-label">{img_label}</div>
                    </div>
                    '''
            if imgs:
                images_html = f'<div class="block-images">{imgs}</div>'

        # バリエーション表
        table_html = ''
        if records:
            headers = list(records[0].keys())
            headers_html = ''.join([f'<th>{h}</th>' for h in headers])

            rows = ''
            for record in records:
                cells = []
                for key, value in record.items():
                    if 'order' in key.lower() or 'number' in key.lower():
                        cells.append(f'<td class="order-number-cell">{value}</td>')
                    elif '価格' in key or 'price' in key.lower() or '定価' in key:
                        cells.append(f'<td class="price-cell">{value}</td>')
                    elif 'barcode' in key.lower() or 'jan' in key.lower() or 'コード' in key:
                        cells.append(f'<td class="barcode-cell">|||||||||||||||||||<br>{value}</td>')
                    else:
                        cells.append(f'<td>{value}</td>')
                rows += '<tr>' + ''.join(cells) + '</tr>'

            table_html = f'''
            <table class="block-variants-table">
                <thead><tr>{headers_html}</tr></thead>
                <tbody>{rows}</tbody>
            </table>
            '''

        return f'''
        <div class="product-group-block">
            {category_html}
            {title_html}
            {specs_html}
            {images_html}
            {table_html}
        </div>
        '''

    # 左ページ
    left_html = ''.join([create_group_block_html(block) for block in left_blocks])

    # 右ページ
    right_html = ''.join([create_group_block_html(block) for block in right_blocks])

    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>電子カタログ - 見開き {spread_number + 1}</title>
        {css}
    </head>
    <body>
        <div class="spread-container">
            <div class="spread">
                <div class="page">
                    {left_html}
                    <div class="page-number">Page {spread_number * 2 + 1}</div>
                </div>
                <div class="page">
                    {right_html}
                    <div class="page-number">Page {spread_number * 2 + 2}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return html


# ========== サイドバー ==========
with st.sidebar:
    st.title("📖 カタログ設定")

    st.header("1️⃣ データ読み込み")
    uploaded_csv = st.file_uploader("CSVファイルをアップロード", type=['csv'])

    if uploaded_csv:
        try:
            st.session_state.df = load_csv(uploaded_csv)
            st.success(f"✅ {len(st.session_state.df)}件")
            with st.expander("📊 データプレビュー"):
                st.dataframe(st.session_state.df.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"❌ エラー: {str(e)}")

    st.header("2️⃣ レイアウト設定")
    blocks_per_page = st.selectbox(
        "1ページあたりのブロック数",
        options=[1, 2, 4],
        index=1,
        help="左右各ページに配置する商品グループブロック数"
    )

    st.header("3️⃣ カラム設定")
    if st.session_state.df is not None:
        all_columns = st.session_state.df.columns.tolist()

        group_by_column = st.selectbox(
            "グループ化カラム（商品名）",
            options=all_columns,
            index=1 if len(all_columns) > 1 else 0,
            help="同じ値でグループ化"
        )

        # メーカーっぽいカラムを自動検出
        default_category_index = 0
        for idx, col in enumerate(all_columns):
            if 'メーカー' in col or 'maker' in col.lower() or 'brand' in col.lower() or 'ブランド' in col:
                default_category_index = idx + 1  # +1 は "なし" の分
                break

        category_column = st.selectbox(
            "カテゴリヘッダー表示カラム（★マーク付き青ヘッダー）",
            options=["なし"] + all_columns,
            index=default_category_index,
            help="ブロック左上の青いヘッダー「★シマノ」に表示するカラム（例: メーカー名）"
        )

        st.info(f"💡 選択中: {category_column if category_column != 'なし' else '未選択'}")

        spec_columns = st.multiselect(
            "スペック項目カラム",
            options=all_columns,
            default=[],
            help="■付きで表示"
        )

        product_id_column = st.selectbox(
            "商品識別カラム（画像マッチング）",
            options=all_columns,
            index=0
        )

        image_label_column = st.selectbox(
            "画像ラベルカラム",
            options=["なし"] + all_columns,
            help="画像の下に表示"
        )

        table_columns = st.multiselect(
            "表示カラム（バリエーション表）",
            options=all_columns,
            default=all_columns[:5] if len(all_columns) >= 5 else all_columns
        )
    else:
        group_by_column = None
        category_column = "なし"
        spec_columns = []
        product_id_column = None
        image_label_column = "なし"
        table_columns = []

    st.header("4️⃣ 画像設定")
    image_mode = st.radio(
        "画像の読み込み方法",
        options=["フォルダ指定", "ファイルアップロード"],
        horizontal=True
    )

    if image_mode == "フォルダ指定":
        folder_path = st.text_input("画像フォルダのパス", placeholder="例: C:/images")
        if folder_path and st.session_state.df is not None and product_id_column:
            codes = st.session_state.df[product_id_column].astype(str).tolist()
            st.session_state.uploaded_images = load_images_from_folder(folder_path, codes)
            if st.session_state.uploaded_images:
                st.success(f"🖼️ {len(st.session_state.uploaded_images)}枚")
    else:
        uploaded_files = st.file_uploader("画像ファイルをアップロード", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if uploaded_files:
            st.session_state.uploaded_images = {}
            for file in uploaded_files:
                code = Path(file.name).stem
                st.session_state.uploaded_images[code] = image_to_base64(file.read())
            st.success(f"🖼️ {len(st.session_state.uploaded_images)}枚")

    st.header("5️⃣ デザイン設定")
    font_size = st.slider("フォントサイズ (px)", 10, 16, 11)
    padding = st.slider("余白 (px)", 8, 20, 12)

    design_config = {
        'font_size': font_size,
        'padding': padding
    }

# ========== メイン画面 ==========
st.title("📝 見開きページ作成（商品グループブロック型）")

if st.session_state.df is not None and group_by_column and table_columns:

    # ページナビゲーション
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ 前の見開き", use_container_width=True):
            if st.session_state.current_spread > 0:
                st.session_state.current_spread -= 1
                st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>見開き {st.session_state.current_spread + 1}</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("次の見開き ➡️", use_container_width=True):
            st.session_state.current_spread += 1
            st.rerun()

    st.divider()

    # 利用可能な商品グループ
    available_groups = st.session_state.df[group_by_column].unique().tolist()
    group_options = ["未選択"] + [str(g) for g in available_groups]

    # 左右ページのブロック選択
    left_col, right_col = st.columns(2)

    left_blocks_data = []
    right_blocks_data = []

    with left_col:
        st.subheader("📄 左ページ")

        for i in range(blocks_per_page):
            with st.expander(f"ブロック {i+1}", expanded=(i == 0)):
                selected_group = st.selectbox(
                    "商品グループを選択",
                    options=group_options,
                    key=f"left_{st.session_state.current_spread}_{i}"
                )

                if selected_group != "未選択":
                    group_df = st.session_state.df[st.session_state.df[group_by_column] == selected_group]

                    # カテゴリ（メーカー名など）
                    category = ""
                    if category_column != "なし":
                        category = str(group_df.iloc[0][category_column])
                        st.caption(f"📌 カテゴリ: {category}")

                    # タイトル
                    title = selected_group

                    # スペック
                    specs = []
                    if spec_columns:
                        for col in spec_columns:
                            specs.append(f"{col}: {group_df.iloc[0][col]}")

                    # 画像選択UI
                    st.markdown("**🖼️ 画像を選択**")
                    available_images = list(st.session_state.uploaded_images.keys()) if st.session_state.uploaded_images else []

                    if available_images:
                        # グループ内の商品IDから自動選択候補を作成
                        unique_ids = group_df[product_id_column].unique()
                        default_selections = [str(uid) for uid in unique_ids if str(uid) in available_images][:5]

                        selected_image_keys = st.multiselect(
                            "表示する画像を選択（最大5枚）",
                            options=available_images,
                            default=default_selections,
                            key=f"img_left_{st.session_state.current_spread}_{i}",
                            help="このブロックに表示する画像を選択してください"
                        )

                        # 選択された画像のプレビュー
                        if selected_image_keys:
                            cols = st.columns(min(len(selected_image_keys), 3))
                            for idx, img_key in enumerate(selected_image_keys[:3]):
                                with cols[idx]:
                                    st.image(
                                        f"data:image/png;base64,{st.session_state.uploaded_images[img_key]}",
                                        caption=img_key,
                                        width=100
                                    )
                    else:
                        st.warning("⚠️ 画像がアップロードされていません")
                        selected_image_keys = []

                    # 画像データ構築
                    images = []
                    for img_key in selected_image_keys[:5]:
                        img_data = st.session_state.uploaded_images.get(img_key, '')
                        label = img_key
                        if image_label_column != "なし":
                            # 画像キーに対応する行を探す
                            matching_rows = group_df[group_df[product_id_column].astype(str) == img_key]
                            if not matching_rows.empty:
                                label = str(matching_rows.iloc[0][image_label_column])
                        images.append({'data': img_data, 'label': label})

                    # レコード
                    records = []
                    for _, row in group_df.iterrows():
                        record = {col: str(row[col]) for col in table_columns if col in row}
                        records.append(record)

                    left_blocks_data.append({
                        'category': category,
                        'title': title,
                        'specs': specs,
                        'images': images,
                        'records': records
                    })

                    st.success(f"✅ {len(group_df)}件のバリエーション | 📷 {len(images)}枚の画像")
                else:
                    left_blocks_data.append(None)

    with right_col:
        st.subheader("📄 右ページ")

        for i in range(blocks_per_page):
            with st.expander(f"ブロック {i+1}", expanded=(i == 0)):
                selected_group = st.selectbox(
                    "商品グループを選択",
                    options=group_options,
                    key=f"right_{st.session_state.current_spread}_{i}"
                )

                if selected_group != "未選択":
                    group_df = st.session_state.df[st.session_state.df[group_by_column] == selected_group]

                    # カテゴリ（メーカー名など）
                    category = ""
                    if category_column != "なし":
                        category = str(group_df.iloc[0][category_column])
                        st.caption(f"📌 カテゴリ: {category}")

                    title = selected_group
                    specs = []
                    if spec_columns:
                        for col in spec_columns:
                            specs.append(f"{col}: {group_df.iloc[0][col]}")

                    # 画像選択UI
                    st.markdown("**🖼️ 画像を選択**")
                    available_images = list(st.session_state.uploaded_images.keys()) if st.session_state.uploaded_images else []

                    if available_images:
                        # グループ内の商品IDから自動選択候補を作成
                        unique_ids = group_df[product_id_column].unique()
                        default_selections = [str(uid) for uid in unique_ids if str(uid) in available_images][:5]

                        selected_image_keys = st.multiselect(
                            "表示する画像を選択（最大5枚）",
                            options=available_images,
                            default=default_selections,
                            key=f"img_right_{st.session_state.current_spread}_{i}",
                            help="このブロックに表示する画像を選択してください"
                        )

                        # 選択された画像のプレビュー
                        if selected_image_keys:
                            cols = st.columns(min(len(selected_image_keys), 3))
                            for idx, img_key in enumerate(selected_image_keys[:3]):
                                with cols[idx]:
                                    st.image(
                                        f"data:image/png;base64,{st.session_state.uploaded_images[img_key]}",
                                        caption=img_key,
                                        width=100
                                    )
                    else:
                        st.warning("⚠️ 画像がアップロードされていません")
                        selected_image_keys = []

                    # 画像データ構築
                    images = []
                    for img_key in selected_image_keys[:5]:
                        img_data = st.session_state.uploaded_images.get(img_key, '')
                        label = img_key
                        if image_label_column != "なし":
                            # 画像キーに対応する行を探す
                            matching_rows = group_df[group_df[product_id_column].astype(str) == img_key]
                            if not matching_rows.empty:
                                label = str(matching_rows.iloc[0][image_label_column])
                        images.append({'data': img_data, 'label': label})

                    records = []
                    for _, row in group_df.iterrows():
                        record = {col: str(row[col]) for col in table_columns if col in row}
                        records.append(record)

                    right_blocks_data.append({
                        'category': category,
                        'title': title,
                        'specs': specs,
                        'images': images,
                        'records': records
                    })

                    st.success(f"✅ {len(group_df)}件のバリエーション | 📷 {len(images)}枚の画像")
                else:
                    right_blocks_data.append(None)

    # プレビュー
    st.divider()
    st.subheader("👁️ 見開きプレビュー")

    spread_html = generate_spread_html(left_blocks_data, right_blocks_data, design_config, st.session_state.current_spread)
    st.components.v1.html(spread_html, height=1100, scrolling=True)

    # 出力
    st.divider()
    st.subheader("💾 出力")

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label=f"📥 HTMLダウンロード",
            data=spread_html,
            file_name=f"catalog_spread_{st.session_state.current_spread + 1}.html",
            mime="text/html",
            use_container_width=True
        )

    with col2:
        if PDF_AVAILABLE:
            if st.button("📄 PDFを生成", use_container_width=True, type="primary"):
                with st.spinner("PDFを生成中..."):
                    try:
                        # PDF用のHTMLを生成（pdf_mode=True）
                        pdf_html = generate_spread_html(
                            left_blocks_data,
                            right_blocks_data,
                            design_config,
                            st.session_state.current_spread,
                            pdf_mode=True
                        )

                        # A4サイズのCSS追加
                        pdf_html = pdf_html.replace(
                            '</head>',
                            '''
                            <style>
                            @page {
                                size: A4 landscape;
                                margin: 10mm;
                            }
                            </style>
                            </head>
                            '''
                        )

                        # PDFに変換
                        pdf_output = BytesIO()
                        pisa_status = pisa.CreatePDF(
                            pdf_html.encode('utf-8'),
                            dest=pdf_output
                        )

                        if not pisa_status.err:
                            pdf_output.seek(0)
                            st.download_button(
                                label="⬇️ PDFダウンロード",
                                data=pdf_output.getvalue(),
                                file_name=f"catalog_spread_{st.session_state.current_spread + 1}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("✅ PDF生成完了！")
                        else:
                            st.error("❌ PDF生成に失敗しました")
                            st.info("💡 HTMLをダウンロードしてブラウザから印刷（Ctrl+P）してください")
                    except Exception as e:
                        st.error(f"❌ エラー: {str(e)}")
                        st.info("💡 HTMLをダウンロードしてブラウザから印刷してください")
        else:
            st.warning("⚠️ PDF機能を使用するには、xhtml2pdfをインストールしてください")
            with st.expander("インストール方法"):
                st.code("pip install xhtml2pdf", language="bash")
                st.markdown("""
                または、HTMLをダウンロードしてブラウザから印刷（Ctrl+P → PDFとして保存）できます。
                """)

else:
    st.info("👈 左のサイドバーでCSVをアップロードし、設定を行ってください")

st.divider()
st.markdown("""
<div style='text-align: center; color: #999; padding: 20px;'>
    <p>電子カタログ作成アプリ v5.0 (商品グループブロック型) | Powered by Streamlit</p>
</div>
""", unsafe_allow_html=True)
