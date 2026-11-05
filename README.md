# SC TW Guide｜Star Citizen 繁體中文新手攻略

專為繁體中文玩家整理的《星際公民》(Star Citizen) 新手入門與攻略網站，內容以 **PVE** 為主。

🌐 **網站：<https://taksito.github.io/sc-tw/>**

---

## 📚 網站內容

| 單元 | 內容 |
|---|---|
| 🌌 星際公民是什麼？ | 遊戲特色、優缺點，入坑前先看 |
| 🧭 開始旅程 | 電腦檢核、註冊與安裝、角色創建、第一次飛行 |
| 🚀 基礎飛行 | 6 步驟教學：登機、起飛、操作、量子航行、降落、實戰練習 |
| 💼 專業領域 | 貨運（Covalex、Red Wind、Ling Family）、飛船戰鬥、地面 FPS、加油、挖礦 |
| ⛏️ 挖礦小幫手 | 選星系／星球／區域查礦物出現機率，輸入掃描訊號判斷礦物種類 |
| ⚙️ 進階技巧 | 保險、飛機組件（武器、電源護盾冷卻、量子引擎、雷達）、Wikelo 交易 |
| 🌎 世界介紹 | Stanton、Pyro（含爭奪區攻略）、Nyx 星系 |
| 🚢 飛機購買指南 | 移動、貨運、戰鬥飛船推薦，CCU 現金購船 |
| 📰 改版資訊 | 4.7～4.10.3 改版整理 |
| 📡 PTU 更新追蹤台 | 自動追蹤官方 PTU Patch Notes 並翻譯成繁體中文 |
| ⌨️ 中文化與輸入 | 繁中語言包安裝教學 |
| 📝 塔克 Blog | 網站更新紀錄與遊戲心得 |

---

## 🗂️ 專案結構

```
├── index.html               首頁
├── components.js            左側選單與共用功能（新增頁面時在這裡加連結）
├── styles.css               全站樣式
├── *.html                   各單元頁面
├── cargohauling/            貨運教學
├── ships/                   飛船介紹
├── update48/ update49/ update410/   改版資訊
├── rockbreaker/             碎石機攻略
├── images/                  站內圖片（images/src/ 是攻略圖的原始檔）
├── data/
│   ├── mining-4.10.2.json   挖礦小幫手資料（來源：SCMDB）
│   ├── ptu-notes.json/.js   PTU 追蹤台資料（自動產生，請勿手動修改）
│   └── glossary.json        PTU 翻譯用的飛船／武器名稱對照表
├── scripts/ptu_update.py    PTU 追蹤台自動更新程式
└── .github/workflows/ptu-tracker.yml   PTU 追蹤台排程
```

純 HTML／CSS／JavaScript 靜態網站，透過 **GitHub Pages** 從 `main` 分支發布，不需要建置。

> 💡 修改 `styles.css` 或 `components.js` 後，記得把各頁面引用的 `?v=日期` 版本號一起更新，瀏覽器才會抓到新版。

---

## 📡 PTU 更新追蹤台（自動更新）

- **來源**：[RSI Spectrum Patch Notes 論壇](https://robertsspaceindustries.com/spectrum/community/SC/forum/190048)
- **排程**：GitHub Actions 每 6 小時檢查一次，有新公告就用 **Gemini API** 翻譯成繁體中文，最多保留 10 筆
- **金鑰**：Repo 的 Settings → Secrets → `GEMINI_API_KEY`
- **手動執行**：Actions → PTU 更新追蹤台 → Run workflow（勾選「只測試」不會寫入網站）
- **統一譯名**：編輯 `data/glossary.json`，格式為 `"英文": "中文"`

---

## 📝 資料來源與版權

- 遊戲畫面、名稱與相關素材版權歸 **Cloud Imperium Games** 所有，本站為非商業的玩家攻略。
- 圖片主要引用自 [Star Citizen Wiki](https://starcitizen.tools/)，挖礦資料來自 [SCMDB](https://scmdb.net/)，各頁最下方附有詳細來源。
- 部分攻略參考社群創作者（如 MrKraken）的整理，已於頁面中標註。

---

## 🎁 推薦碼

還沒註冊的話，可以使用推薦碼 **`STAR-MQY9-QQ7P`**，多拿 5,000 aUEC 開局資金：
<https://www.robertsspaceindustries.com/enlist?referral=STAR-MQY9-QQ7P>

See You In The 'Verse! o7 — 塔克
