````skill
---
name: container-image-hygiene
description: 在使用 Podman/Docker 建構容器映像檔後自動清理 dangling images，避免產生大量 <none> 映像檔佔用磁碟空間。適用於本專案使用 podman compose build/docker compose build 建構 image、需要保持系統乾淨、排查為何 image prune 後仍殘留 <none> 的情境。
license: Complete terms in LICENSE.txt
---

# 容器映像檔清潔（Build 後自動清理）

**等級**：基礎
**預估時間**：2-10 分鐘
**最後更新**：2026-01-26

## 目標

- 建構映像檔後自動清理 dangling images（常見為 `<none>`）
- 降低磁碟被大量舊 image 佔滿的風險
- 提供安全（保守）與進階（較激進）兩種清理模式

## 快速開始（建議）

在專案根目錄執行以下建構腳本：

- Windows：`.github/skills/container-image-hygiene/scripts/build.ps1`
- Linux/Mac：`.github/skills/container-image-hygiene/scripts/build.sh`

### Windows（Podman）

```ps1
# 建構 + 自動清理 dangling images
.\.github\skills\container-image-hygiene\scripts\build.ps1

# 強制重新建構（不使用快取）+ 自動清理
.\.github\skills\container-image-hygiene\scripts\build.ps1 -Force

# 只建構不清理
.\.github\skills\container-image-hygiene\scripts\build.ps1 -NoPrune

# 若你希望同時清理停止中的容器（可協助移除仍被引用的舊 image）
.\.github\skills\container-image-hygiene\scripts\build.ps1 -PruneContainers
```

### Linux/Mac（Docker 或 Podman）

```bash
# 建構 + 自動清理 dangling images
./.github/skills/container-image-hygiene/scripts/build.sh

# 強制重新建構（不使用快取）+ 自動清理
./.github/skills/container-image-hygiene/scripts/build.sh --force

# 只建構不清理
./.github/skills/container-image-hygiene/scripts/build.sh --no-prune

# 若你希望同時清理停止中的容器（可協助移除仍被引用的舊 image）
./.github/skills/container-image-hygiene/scripts/build.sh --prune-containers
```

## 保守清理（只清 dangling images）

此模式最安全：只刪除「沒有 tag 且不再被引用」的 dangling images。

```ps1
podman image prune -f
```

驗證：

```ps1
# 應該回傳空或很少
podman images -f "dangling=true"
```

## 進階清理（處理 prune 後仍殘留的大型 <none>）

如果你看到仍有大型 `<none>`（例如 8GB）存在，常見原因是：

- 有容器（包含停止狀態）仍引用該 image
- 該 image 不是 dangling（例如仍被 build cache/容器引用），因此 `image prune` 不會移除

### Step 1：找出哪些容器還在用該 image

```ps1
podman ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"
```

也可以用 image ID 檢查「是否仍被任何容器當作 ancestor（祖先層）引用」：

```ps1
podman ps -a --filter ancestor=<IMAGE_ID>
```

若發現停止容器引用舊 image，可選擇刪除停止容器（注意：會刪掉容器本體，但不會刪除你的專案檔案與 bind mount 來源資料夾）。

```ps1
podman container prune -f
```

### Step 2：再做一次 image prune

```ps1
podman image prune -f
```

### 仍刪不掉怎麼辦？（常見：layer 仍被新 image 共用）

如果 `podman images -f "dangling=true"` 仍看到大型 `<none>`，而 `podman ps -a --filter ancestor=<IMAGE_ID>` 也有回傳容器，代表該 image 的 layers 仍被目前的 image/容器共用；此時 `image prune` 不會移除它。

處理方式（依你可接受的中斷程度選擇）：

- **最保守**：先不動它；等你下一次以 `--no-cache` 重建並汰換容器後，再清理。
- **可接受重建/停機**：停止並移除相關容器 → 移除依賴的較新 image → 再移除該 `<none>` image，最後用 `--no-cache` 重建。

## 較激進模式（不建議預設開啟）

如果你確定要把「所有未被使用的 images」一起清掉（可能包含 base image，之後需要重新下載），可使用：

```ps1
# 刪除所有未被使用的 images（比 dangling 更廣）
podman image prune -a -f
```

或整體清理（可能影響更多資源：停止容器、未使用網路、未使用 image）：

```ps1
podman system prune -f
```

## 常見注意事項

- **不要在重要容器仍在跑時做激進清理**：保守的 `podman image prune -f` 通常沒問題，但 `-a` / `system prune` 可能影響你預期外的資源。
- **大量 `<none>` 的根因**：通常是反覆用同一個 tag（例如 `latest`）重建，舊版本就會變成 untagged；因此「建構後自動清理」是最省心做法。

## 檢查清單

- [ ] 建構流程使用 `.github/skills/container-image-hygiene/scripts/build.ps1` / `.github/skills/container-image-hygiene/scripts/build.sh`
- [ ] 建構後執行過 `podman image prune -f`
- [ ] 若仍殘留大型 `<none>`，已檢查並清掉停止容器後再 prune
````
