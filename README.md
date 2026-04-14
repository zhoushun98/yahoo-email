# 📮 Yahoo 别名邮箱查看器

一个轻量级 Web 应用，用于实时查看雅虎别名邮箱收到的邮件。客户输入别名地址，点击拉取，即可查看最新邮件，无需登录。

## 功能

- **前台**：输入别名邮箱 → 实时 IMAP 拉取最新 10 封邮件（发件人、主题、时间、摘要）
- **管理后台**：登录后管理雅虎主账号（邮箱 + IMAP 应用密码）和别名（启用/禁用前台访问）
- **安全**：IMAP 密码 Fernet 加密存储，管理员密码 bcrypt 哈希，会话签名 cookie

## 技术栈

FastAPI / Jinja2 / Bootstrap 5 / SQLite + SQLAlchemy / Fernet / bcrypt / itsdangerous

## 快速开始

### 本地运行

```bash
# 克隆项目
git clone git@github.com:zhoushun98/yahoo-email.git
cd yahoo-email

# 安装依赖（需要 uv）
uv sync

# 生成 .env 配置文件（自动生成密钥）
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" > .env
echo "FERNET_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env
echo "ADMIN_USERNAME=admin" >> .env
echo "ADMIN_PASSWORD=admin123" >> .env

# 启动
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker 部署

```bash
# 配置 .env 文件（同上）

# 一键启动
docker compose up -d
```

启动后访问：

| 地址 | 说明 |
|------|------|
| `http://localhost:8000` | 前台 — 输入别名拉取邮件 |
| `http://localhost:8000/admin/login` | 管理后台 — 默认账号 admin / admin123 |

## 项目结构

```
yahoo-email/
├── main.py              # 应用入口
├── config.py            # 配置加载
├── database.py          # 数据库引擎/会话
├── models.py            # ORM 模型（Admin, YahooAccount, Alias）
├── encryption.py        # Fernet 加解密
├── auth.py              # 管理员认证
├── imap_client.py       # IMAP 邮件拉取
├── routers/
│   ├── admin.py         # 管理后台路由
│   └── mail.py          # 前台邮件拉取 API
├── templates/
│   ├── base.html        # 基础模板
│   ├── index.html       # 前台首页
│   ├── login.html       # 登录页
│   └── admin.html       # 管理后台
├── tests/               # 测试用例
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 使用流程

1. 登录管理后台，添加雅虎主账号（邮箱 + [应用密码](https://login.yahoo.com/myaccount/security/app-password)）
2. 为主账号添加别名地址，启用前台访问
3. 前台输入别名地址，点击「拉取邮件」即可查看

## 环境变量

| 变量 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `SECRET_KEY` | 是 | 会话签名密钥 | — |
| `FERNET_KEY` | 是 | IMAP 密码加密密钥 | — |
| `ADMIN_USERNAME` | 否 | 管理员用户名 | `admin` |
| `ADMIN_PASSWORD` | 否 | 管理员初始密码 | `admin123` |
| `DATABASE_URL` | 否 | 数据库连接 | `sqlite:///yahoo_email.db` |
| `IMAP_TIMEOUT` | 否 | IMAP 连接超时（秒） | `10` |

## 测试

```bash
uv run pytest
```
