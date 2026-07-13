# Streamlit Community Cloud デプロイ手順

## 🌐 Web公開方法

### 前提条件
- ✅ GitHubリポジトリが公開されている
- ✅ requirements.txt がある
- ✅ app.py がある

---

## 📋 デプロイ手順

### 1. Streamlit Community Cloudにアクセス

**URL**: https://share.streamlit.io/

### 2. GitHubでサインイン

1. 「Sign in with GitHub」をクリック
2. GitHubアカウントで認証
3. Streamlitにリポジトリアクセスを許可

### 3. 新しいアプリを作成

1. ダッシュボードで「New app」をクリック

2. リポジトリ情報を入力：
   ```
   Repository: funai-yuji-yoshida/ecatalog_vscode
   Branch: master
   Main file path: app.py
   ```

3. App URL（カスタムURL）を設定：
   ```
   例: ecatalog-vscode
   
   完成URL: https://ecatalog-vscode.streamlit.app
   ```

4. 「Advanced settings」（オプション）
   - Python version: 3.11
   - Secrets: 不要

5. 「Deploy!」をクリック

### 4. デプロイ完了を待つ

- 初回デプロイ: 5〜10分
- 進捗状況が表示される
- ログでエラー確認可能

### 5. アプリにアクセス

```
https://あなたのアプリ名.streamlit.app
```

---

## 🔄 更新方法

### 自動デプロイ

GitHubにプッシュすると自動的に更新されます：

```bash
git add .
git commit -m "機能追加"
git push origin master
```

数分後、Streamlit Cloudで自動的に再デプロイ。

### 手動再起動

Streamlit Cloudダッシュボードから：
1. アプリを選択
2. ⋮（三点メニュー）→「Reboot app」

---

## ⚙️ 設定ファイル

### `.streamlit/config.toml`

```toml
[server]
maxUploadSize = 200  # MB

[theme]
primaryColor = "#667eea"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[browser]
gatherUsageStats = false
```

### `packages.txt`

システムパッケージ（Linux）のインストール：

```
libpango-1.0-0
libpangocairo-1.0-0
```

### `requirements.txt`

Pythonパッケージ：

```
streamlit>=1.32.0
pandas>=2.0.0
Pillow>=10.0.0
xhtml2pdf>=0.2.15
reportlab>=4.0.0
```

---

## 🐛 トラブルシューティング

### 問題1: デプロイに失敗する

**エラー**: `ModuleNotFoundError`

**解決策**:
1. requirements.txtに必要なパッケージが全て記載されているか確認
2. バージョン指定が正しいか確認

### 問題2: PDF生成が動作しない

**原因**: xhtml2pdfのビルドエラー

**解決策**:
アプリは既にエラーハンドリング済み。PDF生成に失敗した場合：
- HTMLダウンロード機能が代替として使用可能
- ブラウザ印刷（Ctrl+P）でPDF保存可能

### 問題3: 画像アップロードが遅い

**原因**: ファイルサイズが大きい

**解決策**:
- 画像を最適化（推奨: 800px幅、300dpi）
- maxUploadSize設定を調整（現在200MB）

### 問題4: アプリがスリープする

**仕様**: 7日間アクセスがないと自動的にスリープ

**解決策**:
- 初回アクセス時に自動的に起動（1〜2分待機）
- 有料プラン（Streamlit Pro）で常時起動可能

---

## 💰 料金プラン

### Community（無料）

- ✅ 無制限の公開アプリ
- ✅ GitHubとの統合
- ✅ 1GBストレージ/アプリ
- ❌ カスタムドメイン
- ❌ 認証機能
- ❌ 優先サポート

### Pro（有料: $20/月/ユーザー）

- ✅ 上記全て
- ✅ カスタムドメイン
- ✅ パスワード保護
- ✅ 優先サポート
- ✅ より多いリソース

---

## 🔒 セキュリティ・プライバシー

### データの扱い

- ✅ アップロードされたCSV・画像はセッション終了時に削除
- ✅ データはStreamlit Cloudサーバーに保存されない
- ✅ セッションデータは暗号化

### 公開範囲

- デフォルト: 誰でもアクセス可能
- 有料プラン: パスワード保護可能

### 推奨事項

- 機密情報を含むCSVは使用しない
- または、ローカル実行を推奨

---

## 📊 リソース制限

### 無料プラン

- CPU: 共有
- RAM: 1GB
- ストレージ: 1GB/アプリ
- 実行時間: 無制限（ただし長時間処理は非推奨）

### 推奨事項

- CSV: 10,000行以内
- 画像: 合計50枚以内/セッション
- 処理時間: 1分以内/操作

---

## 🌐 カスタムドメイン設定（Pro限定）

1. Streamlit Cloudダッシュボード
2. アプリ設定 → Custom subdomain
3. 独自ドメインのCNAMEレコード設定

```
CNAME: your-app.streamlit.app
```

---

## 📞 サポート

**Streamlit Community**:
- Forum: https://discuss.streamlit.io/
- Documentation: https://docs.streamlit.io/
- GitHub: https://github.com/streamlit/streamlit

**このアプリのサポート**:
- Issues: https://github.com/funai-yuji-yoshida/ecatalog_vscode/issues
- Email: yuji-yoshida@funaisoken.co.jp

---

## 🚀 次のステップ

1. ✅ デプロイ完了
2. 📧 URLをチームに共有
3. 📝 フィードバック収集
4. 🔄 機能改善・更新

**デプロイ完了URL**: https://your-app.streamlit.app
