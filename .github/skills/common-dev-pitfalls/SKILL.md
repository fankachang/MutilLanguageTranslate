# Common Development Pitfalls

常見開發陷阱與最佳實踐指南。適用於任何程式語言與框架。

**觸發時機**: 當開發者遇到測試失敗、模組引用錯誤、類別設計問題、或路由/命名空間錯誤時使用。

---

## 1. 路由/URL 命名空間問題

### 問題描述
在具有模組化架構的框架中（如 Django、Flask Blueprint、Express Router、Next.js），路由名稱需要包含命名空間前綴。

### ❌ 錯誤模式
`
# 缺少命名空間前綴
redirect('index')
url_for('home')
Router.push('/dashboard')
`

### ✅ 正確做法
`
# 使用完整的命名空間路徑
redirect('app_name:index')
url_for('blueprint_name.home')
Router.push('/module/dashboard')
`

### 檢查重點
- 確認路由配置中是否設定了命名空間/前綴
- 所有路由引用都使用 `namespace:route_name` 格式
- 前端 JavaScript 中的路由也要使用完整路徑

---

## 2. 方法/函數缺少別名（Alias）

### 問題描述
當測試或其他程式碼期望某個方法名稱，但實際實作使用了不同的名稱時，應提供別名保持 API 相容。

### ✅ 正確做法

**Python:**
`python
class ConfigLoader:
    def is_valid_code(self, code: str) -> bool:
        ...
    
    def is_supported(self, code: str) -> bool:
        """is_valid_code 的別名"""
        return self.is_valid_code(code)
`

**TypeScript/JavaScript:**
`	ypescript
class ConfigLoader {
    isValidCode(code: string): boolean { ... }
    
    // 別名
    isSupported = this.isValidCode.bind(this);
}
`

### 檢查重點
- 新增方法時，檢查是否有既有程式碼/測試期望不同的方法名稱
- 考慮提供別名方法以保持向後相容
- 在註解/文檔中標註別名關係

---

## 3. 自訂例外/錯誤類別必須實作字串表示

### 問題描述
自訂例外類別需要實作字串表示方法，以便在日誌和除錯時顯示完整資訊。

### ❌ 錯誤模式
`
# 字串轉換只會顯示 message，無法追蹤錯誤代碼
class CustomError extends Error {
    constructor(code, message) {
        super(message);
        this.code = code;
    }
}
`

### ✅ 正確做法

**Python:**
`python
class CustomError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)
    
    def __str__(self) -> str:
        return f"{self.code}: {self.message}"
`

**TypeScript/JavaScript:**
`	ypescript
class CustomError extends Error {
    constructor(public code: string, message: string) {
        super(message);
        this.name = 'CustomError';
    }
    
    toString(): string {
        return ${this.code}: ;
    }
}
`

**Java:**
`java
public class CustomException extends Exception {
    private String code;
    
    @Override
    public String toString() {
        return code + ": " + getMessage();
    }
}
`

---

## 4. 資料類別應提供屬性別名

### 問題描述
當欄位名稱與常見慣例不同時，應提供別名以提高可用性。

### ✅ 正確做法

**Python (dataclass):**
`python
@dataclass
class Request:
    received_at: datetime
    
    @property
    def created_at(self) -> datetime:
        """received_at 的別名"""
        return self.received_at
`

**TypeScript:**
`	ypescript
class Request {
    receivedAt: Date;
    
    get createdAt(): Date {
        return this.receivedAt;
    }
}
`

**Kotlin:**
`kotlin
data class Request(val receivedAt: Instant) {
    val createdAt: Instant get() = receivedAt
}
`

---

## 5. 測試中引用正確的模組與類別

### 問題描述
測試程式碼必須從正確的模組引入類別，並使用正確的屬性/參數名稱。

### ❌ 錯誤模式
`
# 從錯誤的模組引入
from utils.config import Language  # Language 不在這裡

# 使用錯誤的屬性名稱
obj = SomeClass(
    native_name='...',  # 實際屬性名是 name_en
    enabled=True        # 實際屬性名是 is_enabled
)
`

### ✅ 正確做法
`
# 1. 先確認類別定義的實際位置
# 2. 檢查類別的實際屬性名稱
# 3. 使用 IDE 自動完成功能驗證

from models import Language  # 正確的模組

obj = Language(
    name_en='English',   # 正確的屬性名稱
    is_enabled=True      # 正確的屬性名稱
)
`

### 檢查重點
- 寫測試前，先確認類別的實際定義位置
- 檢查類別的實際屬性/參數名稱
- 使用 IDE 的自動完成功能來驗證

---

## 6. 測試必須提供所有必要參數

### 問題描述
建立物件時，必須提供所有沒有預設值的必要參數。

### ❌ 錯誤模式
`
# 缺少必要參數
response = Response(
    id='test-456',
    status='failed',
    error_code='ERROR_001'
    # 缺少 processing_time 和 execution_mode
)
`

### ✅ 正確做法
`
# 提供所有必要參數（即使是錯誤情境）
response = Response(
    id='test-456',
    status='failed',
    processing_time=0,    # 必要參數
    execution_mode='cpu', # 必要參數
    error_code='ERROR_001',
    error_message='錯誤訊息'
)
`

### 檢查重點
- 建立物件前，檢查類別定義中哪些欄位沒有預設值
- 即使是錯誤情境測試，也要提供所有必要參數
- 考慮為常見測試情境建立 factory 函數或 fixture

---

## 開發檢查清單

### 開發新功能前
- [ ] 閱讀現有測試，了解既有程式碼的期望行為
- [ ] 檢查類別定義：屬性名稱、必要參數、模組位置
- [ ] 確認路由命名空間設定

### 開發新功能後
- [ ] 執行所有測試
- [ ] 驗證 UI 渲染（若有前端）

### 程式碼審查重點
- [ ] 自訂例外類別有字串表示方法
- [ ] 資料類別有常見屬性的別名
- [ ] 路由使用命名空間
- [ ] 測試從正確的模組引入類別
- [ ] 測試提供所有必要參數
