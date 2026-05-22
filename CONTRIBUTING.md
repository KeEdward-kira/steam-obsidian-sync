# 贡献指南

感谢你对 Steam-Obsidian Sync 项目的关注！欢迎任何形式的贡献。

## 如何参与

### 报告问题

- 在 [Issues](../../issues) 中搜索是否已有相同问题
- 如果没有，点击 **New Issue** 创建新问题
- 请包含以下信息：
  - 问题描述（发生了什么 vs 期望什么）
  - 复现步骤
  - 运行环境（Python 版本、操作系统）
  - 相关的错误日志

### 提交功能建议

- 在 [Issues](../../issues) 中提出你的想法
- 描述你希望实现的功能和使用场景

### 提交代码

1. **Fork** 本仓库
2. 创建功能分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 进行修改并提交：
   ```bash
   git commit -m "Add: 简短描述你的改动"
   ```
4. 推送到你的 Fork：
   ```bash
   git push origin feature/your-feature-name
   ```
5. 在 GitHub 上创建 **Pull Request**

## 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/KeEdward/steam-obsidian-sync.git
cd steam-obsidian-sync

# 安装依赖
pip install -r steam/requirements.txt

# 配置环境变量
cp steam/.env.example steam/.env
# 编辑 steam/.env，填入你的 Steam API Key 和 Steam ID
```

### 获取 Steam API Key

1. 访问 [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. 登录 Steam 账号并申请 API Key
3. 将 Key 填入 `.env` 文件的 `STEAM_API_KEY`

### 获取 Steam ID

- 登录 [Steam](https://store.steampowered.com/) 后，访问你的个人资料页
- URL 中的数字即为你的 Steam ID（如 `76561198XXXXXXXXX`）
- 如果 URL 显示的是自定义名称，可以使用 [SteamDB Calculator](https://steamdb.info/calculator/) 查找数字 ID

## 代码规范

- Python 代码遵循 PEP 8 风格
- 提交信息使用中文或英文均可，保持简洁明了
- 修改核心脚本前，请先在 Issue 中讨论你的方案

## 项目结构

```
steam-obsidian-sync/
├── steam/
│   ├── steam_to_obsidian.py    # 主同步脚本
│   ├── update_achievements.py  # 成就更新脚本
│   ├── .env.example            # 环境变量模板
│   ├── requirements.txt        # Python 依赖
│   ├── 游戏总览.md             # Dataview 游戏总览页
│   ├── 游戏待玩清单.md         # Dataview 待玩清单页
│   └── Steam Games/            # 自动生成的游戏文件（不纳入版本控制）
├── .obsidian/
│   └── snippets/
│       └── dataview-cards.css  # 卡片布局 CSS 片段
└── .gitignore
```

## 有疑问？

随时在 [Issues](../../issues) 中提问，没有愚蠢的问题！
