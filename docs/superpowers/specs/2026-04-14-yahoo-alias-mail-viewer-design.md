# 雅虎别名邮箱查看器 — 设计规格

## 概述

一个 Web 应用，允许客户输入雅虎别名邮箱地址，实时拉取并查看该别名收到的邮件。管理员在后台配置雅虎主账号及其别名，只有已配置的别名才能在前台使用。

**核心场景**：接收验证码/通知邮件，无需登录，输入别名即查看。

## 业务流程

1. **管理员**在后台添加雅虎主账号（邮箱 + IMAP 应用密码）
2. **管理员**为主账号关联别名地址，并启用前台访问
3. **客户**在前台输入别名地址，点击"拉取邮件"
4. **系统**查找别名对应的主账号 → 实时通过 IMAP 连接雅虎 → 搜索发往该别名的邮件 → 返回最新 10 封
5. **前台**展示简洁邮件列表（发件人、主题、时间、摘要）

## 技术栈

| 组件 | 选择 |
|------|------|
| 后端框架 | FastAPI |
| 模板引擎 | Jinja2 |
| 前端 UI | Bootstrap 5 |
| 数据库 | SQLite + SQLAlchemy |
| 密码加密 | Fernet 对称加密（IMAP 密码）、bcrypt（管理员密码） |
| 会话管理 | itsdangerous 签名 cookie |
| 邮件协议 | IMAP（imap.mail.yahoo.com:993 SSL） |
| 包管理 | uv |

## 数据模型

### Admin（管理员）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| username | String, 唯一 | 用户名 |
| password_hash | String | bcrypt 哈希 |

### YahooAccount（雅虎主账号）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| email | String, 唯一 | 雅虎邮箱地址 |
| imap_password | String | Fernet 加密的应用密码 |
| status | String | normal / disabled |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### Alias（别名）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| alias_email | String, 唯一 | 别名邮箱地址 |
| account_id | Integer, FK → YahooAccount.id | 所属主账号 |
| enabled | Boolean | 是否启用前台访问 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**关系**：YahooAccount 一对多 Alias。

## 项目结构

```
yahoo-email/
├── pyproject.toml
├── .env                    # SECRET_KEY, FERNET_KEY
├── .gitignore
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置加载
├── database.py             # SQLAlchemy 引擎/会话
├── models.py               # ORM 模型
├── encryption.py           # Fernet 加解密
├── auth.py                 # 管理员认证（session cookie）
├── imap_client.py          # IMAP 邮件拉取逻辑
├── routers/
│   ├── admin.py            # 管理后台路由（账号/别名 CRUD）
│   └── mail.py             # 前台邮件拉取路由
└── templates/
    ├── base.html           # 基础模板（Bootstrap 5）
    ├── index.html          # 前台首页（极简居中布局）
    ├── login.html          # 管理员登录页
    └── admin.html          # 管理后台页（顶部 Tab 导航）
```

## API 路由

### 前台

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 前台首页，显示输入框 |
| `/api/mail/fetch` | POST | 接收别名地址，返回最新 10 封邮件 JSON |

### 管理后台

| 路由 | 方法 | 说明 |
|------|------|------|
| `/admin/login` | GET/POST | 管理员登录 |
| `/admin/logout` | GET | 管理员退出 |
| `/admin/` | GET | 管理后台主页（重定向到账号列表） |
| `/admin/accounts` | GET | 主账号列表 |
| `/admin/accounts` | POST | 添加主账号 |
| `/admin/accounts/{id}` | DELETE | 删除主账号（级联删除别名） |
| `/admin/aliases` | GET | 别名列表 |
| `/admin/aliases` | POST | 添加别名 |
| `/admin/aliases/{id}` | DELETE | 删除别名 |
| `/admin/aliases/{id}/toggle` | POST | 启用/禁用别名 |

## IMAP 拉取逻辑

`imap_client.py` 核心函数：

```python
def fetch_emails(email: str, imap_password: str, alias: str, count: int = 10) -> list[dict]:
    """
    连接雅虎 IMAP，搜索发往 alias 的邮件，返回最新 count 封。
    返回: [{"from": str, "subject": str, "date": str, "snippet": str}, ...]
    """
```

- 连接 `imap.mail.yahoo.com:993`（IMAP4_SSL）
- 登录主账号
- SELECT INBOX
- `SEARCH TO "<alias>"` 搜索
- FETCH 最新 10 封的 envelope（FROM、SUBJECT、DATE）和 BODY 前 200 字符作为摘要
- 解析 MIME 编码的头部（处理 UTF-8、Base64 等）
- 超时 10 秒

## UI 设计

### 前台（极简干净风格）

- 白色背景，居中布局（max-width: 500px）
- 顶部标题 + 邮箱输入框 + "拉取邮件"按钮
- 点击后显示 loading 动画
- 邮件列表：每封邮件一行卡片，显示发件人、主题、时间、摘要
- 空状态："暂无邮件"
- 错误状态："未找到该邮箱"或"服务暂时不可用"

### 管理后台（顶部 Tab 导航）

- 顶部导航栏：标题 + 退出登录
- Tab 页：主账号 | 别名管理
- 主账号页：表格列表 + 添加按钮 + 编辑/删除操作
- 别名页：表格列表 + 添加按钮 + 启用/禁用/删除操作
- 添加操作使用 Bootstrap Modal 弹窗

## 安全

- **IMAP 密码**：Fernet 加密存储，密钥在 `.env` 的 `FERNET_KEY`
- **管理员密码**：bcrypt 哈希
- **管理员会话**：itsdangerous 签名 cookie，密钥在 `.env` 的 `SECRET_KEY`
- **前台无鉴权**：但只有 Alias 表中 `enabled=True` 的别名才可查询
- **信息不泄露**：别名不存在或未启用统一返回"未找到该邮箱"
- `.env` 和 `yahoo_email.db` 通过 `.gitignore` 排除

## 错误处理

| 场景 | 处理 |
|------|------|
| 别名不存在/未启用 | 返回"未找到该邮箱" |
| IMAP 连接失败 | 返回"邮件服务暂时不可用，请稍后重试" |
| IMAP 认证失败 | 返回错误，管理后台可标记账号异常 |
| 拉取超时 | 10 秒超时，返回超时提示 |

## 部署

- `uvicorn main:app --host 0.0.0.0 --port 8000`
- SQLite 文件 `yahoo_email.db` 在项目根目录
- 首次启动自动建表
- `.env` 需提前配置 `SECRET_KEY` 和 `FERNET_KEY`

## 验证方案

1. 启动应用，访问前台首页，确认极简 UI 正常渲染
2. 访问 `/admin/login`，用默认管理员账号登录
3. 添加一个雅虎主账号（需要真实的雅虎应用密码）
4. 为该主账号添加一个别名并启用
5. 回到前台，输入别名地址，点击拉取，确认邮件列表正确展示
6. 测试错误场景：输入不存在的别名、禁用的别名、错误的账号密码
