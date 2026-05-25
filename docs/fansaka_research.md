# fansaka.info 調査メモ

## fansaka.info とは

**ファンタジーサッカー研究室** (https://www.fansaka.info/)

Jリーグのファンタジーサッカーを楽しむための情報集約サイト。試合結果・順位表・選手データ・対戦成績などを提供しつつ、有用なJリーグ関連サイトへのリンク集を整理している。

サイト自体が持つ主なコンテンツ：

| パス | 内容 |
|------|------|
| `/table.php` | J1順位表 |
| `/team/` | チーム別対戦成績 |
| `/player/` | Jリーグ選手一覧 |
| `/stadium.php` | スタジアム情報 |
| `/kako/` | 過去データ（ポイント分布など） |
| `/link/` | データソースリンク集 ← ここが本題 |

---

## リンク集 (/link/) に集められているデータソース

直接取得はブロックされたため、検索経由で確認。以下のカテゴリに分類されていると推定される。

### 試合・スコア系
| サイト | URL | 内容 |
|--------|-----|------|
| Jリーグ公式 | https://www.jleague.jp/stats/ | 成績・スタッツ（公式） |
| J. League Data Site | https://data.j-league.or.jp/ | 詳細試合データ（公式） |
| Digital Data Book | https://ddb.j-league.or.jp/ | Jリーグ公式データブック |

### スタッツ・分析系
| サイト | URL | 内容 | 備考 |
|--------|-----|------|------|
| SPORTERIA | https://sporteria.jp/ | Data Stadium 提供のJリーグ詳細スタッツ | **2025年12月サービス終了** |
| SPAIA | https://spaia.jp/football/jleague/ | チーム・選手スタッツ | 現役稼働中 |

### ケガ・出場停止系
- ニッカンスポーツ等のスポーツ紙がケガ・警告累積情報を掲載（ファンサカ向けに重要視されている）

---

## ダッシュボードに使えるデータソース評価

### ◎ StatsBomb J1 2024（最有力）

- **提供元**: Hudl StatsBomb × Wyscout
- **公開時期**: 2025年1月
- **内容**: J1 2024シーズン全試合のイベントデータ（xG・パス・シュート等）＋身体的指標
- **形式**: JSON・CSV
- **取得方法**: フォーム登録後ダウンロード → https://info.hudl.com/free-data-j1-league.html
- **IP制限**: なし（GitHubベース）
- **課題**: 2025シーズン以降の更新は未定、最新データではない

### ○ J. League Data Site（スクレイピング）

- **提供元**: Jリーグ公式
- **内容**: 試合結果・選手スタッツ・チーム成績（公式データ）
- **取得方法**: HTMLスクレイピング（BeautifulSoup / Selenium）
- **IP制限**: なし
- **課題**: 利用規約の確認が必要、動的レンダリングのページあり

### ○ Jリーグ公式サイト（スクレイピング）

- **URL**: https://www.jleague.jp/stats/
- **内容**: 順位表・得点ランキング・試合結果
- **取得方法**: HTMLスクレイピング
- **課題**: 構造変更リスク、規約確認必要

### △ FootyStats API

- **URL**: https://footystats.org/api/
- **内容**: Jリーグ対応、試合・順位・選手スタッツ
- **形式**: REST API
- **課題**: 無料枠の制限が厳しい可能性

### × api-football.com 無料プラン（現状利用中）

- 2025シーズン非対応（2022〜2024のみ）
- クラウドIPからアクセス不可
- **実用性なし** → 切り替え推奨

---

## 次のアクション案

1. **StatsBomb J1 2024 データをダウンロードして使う**
   - フォーム登録 → データ取得 → リポジトリに配置
   - イベントデータ（xG等）が使えるため仕様書の KPI をフルカバーできる
   - 2025年以降のデータは別途調達が必要

2. **J. League Data Site スクレイピングで最新データを補完**
   - 現在進行中の2025/2026シーズンデータはここから取る
   - 利用規約の確認を先に行う

3. **ハイブリッド構成**
   - 過去詳細分析: StatsBomb（イベントデータ）
   - 最新試合結果: Jリーグ公式スクレイピング
   - 自動更新: GitHub Actions

---

Sources:
- [ファンタジーサッカー研究室](https://www.fansaka.info/)
- [Free Data: J1 League 2024 - Hudl StatsBomb](https://www.hudl.com/blog/j1-league-free-data-statsbomb)
- [J. League Data Site](https://data.j-league.or.jp/SFTP01/)
- [Digital Data Book - Jリーグ](https://ddb.j-league.or.jp/)
