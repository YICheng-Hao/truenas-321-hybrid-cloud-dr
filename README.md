# 📊 TrueNAS 3-2-1 混合雲架構與災難復原（DR）自動化監控系統

[![GitHub Repository](https://shields.io)](https://github.com)
[![Prometheus](https://shields.io)](https://prometheus.io)
[![Grafana](https://shields.io)](https://grafana.com)
[![AWS S3](https://shields.io)](https://amazon.com)

本專案專為 **TrueNAS 混合雲備份架構** 設計，落實 **3-2-1 備份原則**（3 份資料、2 種媒介、1 份異地/雲端）。透過整合 **Prometheus** 監控系統、自製 **Python 即時腳本** 與 **Grafana 視覺化儀表板**，實現對地端 TrueNAS 實機狀態、網路流量，以及 AWS S3 雲端儲存槽容量與 API 延遲的全面性即時監控。

---

## 🏗️ 專案資料夾結構

本倉庫的檔案配置如下，完美將實機營運程式碼與設定檔抽離，便於版本控制與快速部署：

*   **`systemd/`**：存放實機（Linux/TrueNAS 監控主機）上的 4 個 Systemd 服務管理設定檔。
*   **`configs/`**：存放 Prometheus 主要抓取策略與 SNMP Exporter 的自訂 ZFS 模組片段。
*   **`scripts/`**：存放自主研發的 Python S3 監控腳本，負責即時抓取 AWS 儲存槽指標。
*   **`grafana/`**：存放經最佳化調整的 3-2-1 DR 監控儀表板 JSON 匯出檔。

---

## 🚀 實機快速部署指令

若要在全新監控主機上復現此專案，請登入主機後執行以下步驟：

### 1. 複製本專案倉庫
```bash
git clone https://github.com你的帳號名稱/truenas-321-hybrid-cloud-dr.git
cd truenas-321-hybrid-cloud-dr
```

### 2. 部署 Systemd 服務檔
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 3. 啟動所有監控服務
```bash
sudo systemctl enable --now snmp_exporter cloudwatch_exporter s3_realtime_exporter prometheus
```

---

## 📈 監控核心指標與效益

本系統成功採集並監控以下關鍵指標（KPI）：
*   **地端 TrueNAS**：ZFS 儲存池健康度（`zpoolHealthStatus`）、可用空間與硬體操作燈號。
*   **雲端 AWS S3**：儲存桶真實體積（Bytes）、總物件數量、每秒 API 請求延遲。
*   **營運成本預估**：透過 Python 腳本即時計算當月 S3 Standard 儲存空間之預估美元費用（以 \$0.025 USD/GB 估算），防範雲端預算超支。
