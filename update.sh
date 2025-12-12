#!/bin/bash

# 確保腳本發生錯誤時停止執行
set -e

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 檢查是否以 root 執行 (應該以一般使用者執行)
if [ "$EUID" -eq 0 ]; then
  echo -e "${RED}錯誤: 請不要以 root (sudo) 執行此腳本。${NC}"
  echo -e "腳本內部會在需要時自動呼叫 sudo。"
  echo -e "請使用: ./update.sh"
  exit 1
fi

echo -e "${GREEN}=== 開始更新 Anki Pi ===${NC}"

PROJECT_DIR=$(pwd)
echo -e "${YELLOW}[INFO] 專案路徑: $PROJECT_DIR${NC}"

# 1. 更新程式碼
echo -e "${YELLOW}[INFO] 正在從 Git 下載最新程式碼...${NC}"
# 檢查是否有衝突
if ! git pull; then
    echo -e "${RED}錯誤: Git 更新失敗，可能存在檔案衝突。${NC}"
    echo -e "請手動解決衝突後再嘗試更新。"
    exit 1
fi

# 2. 更新 Python 依賴
if [ -d "venv" ]; then
    echo -e "${YELLOW}[INFO] 正在更新 Python 依賴...${NC}"
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
else
    echo -e "${RED}錯誤: 找不到虛擬環境 (venv)。請確認安裝是否完整。${NC}"
    exit 1
fi

# 3. 重新啟動服務
echo -e "${YELLOW}[INFO] 正在重新啟動 Systemd 服務...${NC}"
if systemctl list-units --full -all | grep -Fq "anki_pi.service"; then
    sudo systemctl restart anki_pi
    echo -e "${GREEN}服務已重新啟動。${NC}"
else
    echo -e "${YELLOW}警告: 找不到 anki_pi 服務，跳過重新啟動。${NC}"
    echo -e "如果您是在本機開發環境執行，這是正常的。"
fi

# 4. 顯示狀態
echo -e "${GREEN}=== 更新完成！ ===${NC}"
echo -e "目前版本資訊："
git log -1 --format="%h - %s (%cd)" --date=short

# 嘗試顯示服務狀態 (如果存在)
if systemctl list-units --full -all | grep -Fq "anki_pi.service"; then
    echo -e "\n${YELLOW}[服務狀態]${NC}"
    sudo systemctl status anki_pi --no-pager
fi
