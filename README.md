# 在线答题系统

Flask 在线答题系统 - 支持单选、多选、判断、填空题型，包含分组答题、进度保存、批量导入导出功能。

## 项目结构

```
project/
├── app.py              # 主入口（应用初始化 + 路由注册）
├── config.py           # 配置管理
├── models.py           # 数据库模型
├── utils.py            # 辅助函数（装饰器、业务逻辑）
├── routes/             # 路由模块
│   ├── __init__.py     # 路由注册
│   ├── auth.py         # 认证路由（登录/注册/退出）
│   ├── quiz.py         # 答题路由（答题/提交/历史）
│   └── admin.py        # 管理后台路由
├── templates/          # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── quiz.html
│   ├── result.html
│   ├── history.html
│   └── admin/          # 管理后台模板
├── uploads/            # 上传文件目录
├── instance/           # SQLite 数据库（运行时生成）
└── requirements.txt    # Python 依赖
```

## 快速开始

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

访问 http://127.0.0.1:5000

## 默认管理员

- 用户名：`admin`
- 密码：`admin123`

## 功能特性

- ✅ 四种题型：单选、多选、判断、填空
- ✅ 分组答题（按顺序完成，全对才能进入下一组）
- ✅ 进度保存（下次继续从上次完成的分组开始）
- ✅ 批量导入题目（Excel/CSV）
- ✅ 导出答题记录（Excel）
- ✅ 用户管理
- ✅ 全对动画庆祝效果

## 重构说明

原 `app.py` 约 2000 行，已重构为模块化结构：

| 文件 | 行数 | 职责 |
|------|------|------|
| app.py | ~40 | 应用初始化、路由注册 |
| config.py | ~25 | 配置管理 |
| models.py | ~120 | 数据库模型 |
| utils.py | ~50 | 辅助函数 |
| routes/auth.py | ~50 | 认证路由 |
| routes/quiz.py | ~280 | 答题路由 |
| routes/admin.py | ~400 | 管理后台路由 |

**备份位置**: `project_backup_20260330_1817xx`
