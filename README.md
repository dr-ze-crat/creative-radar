# 创作雷达（Creative Radar）

面向视频创作者的选题辅助工具：**一屏看完今天全网在说什么，标出真热点与正在升温的话题**。

> 状态：**v1 已可运行**（2026-10-22）。想改构想先改这里，再动代码。

---

## 一句话定位

打开软件 → 一屏看到百度、B站、微博、知乎四个热榜 → 软件标出**多平台同时在榜的真热点**和**过去一个周期排名涨得最快的话题** → 收藏进选题夹，导出 Markdown 直接开写脚本。

## 目标用户

视频创作者本人（多类型：游戏 / 知识科普 / 影视解说 / 生活日常）。可打包发给朋友，解压即用，不需要装 Python。

## 为什么需要它

网页也能看热榜，软件的价值只在这三件网页做不到的事：

1. **跨平台同题归并**——同一话题 3 个平台都在榜 = 真热点；只在一个平台 = 那个平台自己的瓜。
2. **升温榜而不是热度榜**——刚起飞的话题才是选题时间窗；只看当前热度，看到的都是已经晚了的话题。
3. **领域标签自动匹配**——命中的条目分色打标，一眼筛出跟自己相关的。

---

## 已实现（v1）

| 功能 | 状态 |
|---|---|
| 4 源抓取：百度 / B站 / 微博 / 知乎 | ✅ 实测 181 条 |
| 三档视图：全网热 / 升温中 / 全部 | ✅ |
| 跨源同题归并（字符相似度） | ✅ 实测 7 组，无误并 |
| 升温榜（对比相邻两批 rank） | ✅ |
| **领域分区**：游戏 / 动漫 / 影视 / 科技 / 娱乐 / 体育 / 财经 / 社会 / 生活 / 综合 | ✅ 各带图标、专属色与条数，点击即筛选 |
| **分区专属榜**：点分区时按需抓各平台对应分区榜，与综合热榜命中条目合并 | ✅ 游戏 30+B站、科技 30+B站… |
| **分区榜升温**：分区榜落库（`channel` 列），同一分区再点时能算排名涨幅，并入「升温中」 | ✅ 卡片带 ↑N 与「分区榜」标记 |
| 搜索过滤 / 源开关 | ✅ |
| 顶部标题条显示当前分区与条数 | ✅ |
| 收藏选题夹 + 导出 Markdown 到剪贴板 | ✅ |
| **选题夹按分区分组导出**：收藏时记下领域分区，导出按 游戏/动漫/影视/科技/娱乐/体育/财经/社会/生活/综合 顺序分组，缺分区归「未分类」 | ✅ |
| **界面细节**：卡片紧凑（标题单行、组头去掉、操作按钮 hover 才显，一屏 4→6 张）；字号三档 A-/A/A+；分区可隐藏（「分区」面板勾选）；设置存 SQLite `settings` 表 | ✅ |
| **素材库（v2）**：五源搜索 — Pexels / Pixabay（图+视频）、Unsplash（图）、ccMixter（音乐，**免 key**）、Jamendo（音乐）；收藏进「素材账本」（平台/作者/原页/直链/授权+授权链接）；导出 Markdown 按图片/视频/音乐分组；不下载文件 | ✅ 图片视频需自填 key，ccMixter 免 key |
| SQLite 存历史，30 天自动清理 | ✅ |
| onedir 打包（27 MB） | ✅ |
| 抖音 | ⏸ 暂缓，界面未留位 |

## v2 素材库（多源已完成）

- ✅ **五个源**：Pexels（图+视频）、Pixabay（图+视频）、Unsplash（图）、ccMixter（音乐，免 key）、Jamendo（音乐，client_id）
- ✅ **按需启用**：填了哪个 key 就搜哪个源，一次搜索并行跑所有可用源，结果混排并标平台
- ✅ **授权标注**：每源授权不同（Pexels License / Pixabay Content License / Unsplash License / CC 变体），账本记授权名称 + 授权链接
- ✅ **出处账本**：收藏即记「标题 + 平台 + 作者 + 原页 + 文件直链 + 授权 + 收录日期」，导出 Markdown；音乐分组带 NC 警告
- ✅ 免 key 也能用：ccMixter 音乐不填任何 key 就能搜
- ⏸ 下载到本地：按决定不做，只存链接（点「打开原页」去官网下）

## 明确不做

| 不做 | 原因 |
|---|---|
| 抖音签名逆向 | 需 a_bogus，维护成本不划算；真要做得走 WebView 抠 DOM |
| 素材下载到本地 | v2 才做 |
| AI 写脚本 / 配音 / 剪辑 | 另一个赛道 |
| 去水印、搬运 | 版权风险 |
| 各平台账号数据 | 需登录后台，隐私与稳定性都差 |
| 常驻托盘 / 开机自启 | 用完就关 |

---

## 怎么用

**下载现成的（Windows x64，不用装 Python）**

到 [Releases](https://github.com/dr-ze-crat/creative-radar/releases) 下载最新版 `CreativeRadar_v1.0.1_win64.zip`，解压双击 `创作雷达.exe`。数据会写在同目录 `data\` 下，整个文件夹拷走即带走全部设置。

**直接使用（自己打包后也是这个）**

```
dist\创作雷达\创作雷达.exe
```

**便携 / U 盘 / 课堂演示版**

打包好后把整个 `创作雷达` 文件夹（含 `_internal`）拷到目标电脑，数据会写在同目录 `data\radar.db`——拷走整个文件夹就带走收藏、设置与历史。想预置内容给离线演示，就把一份 `radar.db` 放进 `data\` 再打包。

窗口尺寸按屏幕自适应（屏宽−80 / 屏高−80，最大 1280×820），投影分辨率 1366×768 也不会超出屏幕。

解压后双击即可。首次启动会抓一次，约 2–4 秒。

**开发运行**

```
.venv\Scripts\python.exe app.py
```

**单源验证抓取是否还活着（接口改版时先跑这个）**

```
.venv\Scripts\python.exe fetch.py baidu
.venv\Scripts\python.exe fetch.py all
```

**离线自检（聚类 / 标签 / 入库 / 升温 / 收藏 / 剪贴板）**

```
.venv\Scripts\python.exe selfcheck.py
```

**重新打包**

```
.venv\Scripts\python.exe -m PyInstaller --noconfirm --windowed --name "创作雷达" ^
  --add-data "web;web" --hidden-import fetch_baidu --hidden-import fetch_bilibili ^
  --hidden-import fetch_weibo --hidden-import fetch_zhihu --distpath dist --workpath build app.py
```

> 四个 `fetch_*` 必须用 `--hidden-import` 声明：主程序是 `importlib.import_module` 动态导入，PyInstaller 静态分析看不到。

**重建图标 sprite**（改了 assets/icons 之后）

```
.venv\Scripts\python.exe tools\build_icons.py
```

---

## 技术选型

| 项 | 选择 | 理由 |
|---|---|---|
| 语言 | Python **3.12.10**（`.venv`） | 机器默认 3.14.8 太新，PyInstaller 7 才支持；3.12 稳定 |
| 界面 | pywebview（WebView2）+ 单 HTML | 界面用 HTML/CSS 写，改一行刷新即见 |
| 前后端 | pywebview `js_api` | **不起本地 HTTP 服务**，免端口冲突 |
| 打包 | PyInstaller **onedir** | 单文件 exe 常被 Defender 误报；onedir 解压即用 |
| 数据 | SQLite，**便携优先**：程序同目录 `data\radar.db` 可写就用它（U 盘带走收藏与设置），否则退回 `%LOCALAPPDATA%\创作雷达\radar.db` | 要算升温必须存历史快照 |
| 图标 | Tabler Icons 3.49.0（MIT）+ 自绘应用图标 | 界面图标免费商用；应用图标为**透明底橙色渐变雷达**，由 `tools/make_icon.py` 用 Pillow 绘制 |
| 配色 | **暖亮**：米白 `#fffaf5` 底 + 橙 `#ff7a45` 强调，侧栏浅米色分层 | 用户明确要求「明亮温暖」；暗色主题已弃用 |
| 字体 | 系统字体栈 | 不下载字体，省体积 |
| 网络 | 只读热榜，只出不进 | 不上传任何数据 |

---

## 接口备忘（2026-10-22 实测，改版时照这个查）

| 源 | 实际可用接口 | 要点 |
|---|---|---|
| 百度 | `https://top.baidu.com/api/board?platform=wise&tab=realtime` | 条目在 **`data.cards[0].content[0].content`**（双层嵌套），只有 `word/url/index/isTop`，**没有数值热度** |
| B站 | `https://api.bilibili.com/x/web-interface/popular?ps=50&pn=1` | 需 `Referer: https://www.bilibili.com/` |
| 微博 | `https://weibo.com/ajax/side/hotSearch` | 免登录；**必须过滤 `is_ad`**，否则混进广告 |
| 知乎 | `https://api.zhihu.com/topstory/hot-list?limit=50` | `www.zhihu.com/api/v3/...` 现在 **401 需 cookie**；这个接口返回 30 条（上限），`detail_text` 是「564 万热度」 |

## 素材源（多源，全部 2026-10-22 实测）

| 源 | 类型 | key | 端点 / 字段 | 实测 |
|---|---|---|---|---|
| Pexels | 图 + 视频 | 免费，200 次/小时 | `/v1/search`、`/videos/search`；头 `Authorization: <key>`；`photos[]` 有 `url`/`photographer`/`src.medium`/`src.original` | API 无 key=401、CDN 200 ✅ |
| Pixabay | 图 + 视频 | 免费，100 次/60 秒 | `https://pixabay.com/api/?key=`、`/api/videos/?key=`；`hits[]` 有 `pageURL`/`webformatURL`/`largeImageURL`/`videos.large.url` | API 无 key=400 可达 ✅ |
| Unsplash | 图 | 免费 demo 50 次/小时 | `/search/photos`；头 `Authorization: Client-ID <key>`；`results[]` 有 `urls`/`user`/`links.html` | API 无 key=401、CDN 200 ✅ |
| ccMixter | 音乐 | **免 key** | `https://ccmixter.org/api/query?f=json&limit=12&search=`；`files[].download_url`、`license_name`/`license_url` | ✅ 12 条实测 |
| Jamendo | 音乐 | 免费 client_id | `https://api.jamendo.com/v3.0/tracks/?client_id=&format=json&audioformat=mp32&search=` | API 可达（无 id 报 code=5） |

**坑**：
- **ccMixter 在 `limit>=15` 时回超长响应头**，标准库抛 `LineTooLong: got more than 65536 bytes`。解法：`common.py` 里把 `http.client._MAXLINE` 放宽到 1MB，并把 limit 收到 12。
- **Pixabay 音乐没有 API**，音乐页 `https://pixabay.com/music/search/...` 直接 403（Cloudflare）⇒ 音乐改用 ccMixter + Jamendo。
- **ccMixter / Jamendo 的音乐多为 CC 变体，常带 NC（禁止商用）**；账本逐条记 `license_name` 与 `license_url`，导出时音乐分组加 NC 警告，用前自己看一眼。
- Openverse / Wikimedia Commons 在本机**连接超时**（被墙），「免 key CC 图片库」这条路不通。
- 各源错误都在各自的 `*Error` 里翻成中文（key 无效 / 配额用完 / 连不上）。

## 分区专属榜（2026-10-22 实测）

点某个分区时，**不只看综合热榜里命中关键词的几条**，而是去抓该平台真正分区榜，与综合命中合并展示（分区榜条目带「分区榜」标记）。带 10 分钟内存缓存，重复点不重复抓。

| 分区 | 专属榜 |
|---|---|
| 游戏 | B站 `ranking/v2?rid=4`（96 条） |
| 动漫 | B站 `rid=1` 动画区（95 条） |
| 影视 | B站 `rid=181` 影视 + `rid=23` 电影 |
| 科技 | B站 `rid=188` 科技 + `rid=36` 知识 |
| 娱乐 | B站 `rid=5` + 微博 `hot_band?band=ent`（文娱榜 51 条） |
| 体育 | B站 `rid=234` 运动 + 百度 `tab=sports`（30 条） |
| 财经 | 百度 `tab=finance`（30 条） |
| 生活 | B站 `rid=160` 生活 + `rid=211` 美食 |
| 社会 / 综合 | 无专属榜，只用综合热榜命中 |

**接口坑**：
- B站 `rid=71`（综艺）返回 `-400 请求错误`，不能直接用；其余 rid 都正常。
- 百度只有 `tab=finance` / `tab=sports` 是文字榜（`tabTextList`）；`tab=movie/teleplay/novel/car` 是 `tabImgInfoList` 图片卡，结构不同；`tab=game` 直接 `no found page`。
- 微博文娱榜用 `ajax/statuses/hot_band?band=ent`，字段是 `data.band_list`（`word_scheme` + `num`），不是热搜那个 `data.realtime`。

抓取层约定：每个源一个文件，暴露 `fetch() -> list[Item]`，**一个源挂了只损失一个源**。这是整个项目里唯一值得做的抽象。

---

## 已知限制与坑

- **改 exe 图标后看不见变化**：PyInstaller 若已存在同名 `.spec`，会**复用 spec 并忽略命令行 `--icon`**。解法：删掉 `创作雷达.spec`（必要时连 `build\创作雷达`）后重新打包，日志里应出现 `Copying icon to EXE`。验证时把 exe 复制到临时目录再提取，因为 Shell 图标缓存会返回旧图。
- **百度没有热度数值**，界面只显示排名与「置顶」。
- **知乎只返回 30 条**，接口上限。
- **升温榜需要至少两批数据**：第一次打开为空，点一次「刷新」后才有。分区榜同理——**同一分区要隔 10 分钟以上再点一次**，才出现分区内升温（分区榜与综合热榜各存各的批次，`channel` 列区分，互不比较）。
- **领域分区靠关键词规则**，不含 AI：实测 181 条里「综合」（未分类）约占 **67%**，因为大量标题是「某人回应某事」这类人名事件，关键词抓不住。关键词表在 `app.py` 的 `TAGS`，加词即可，不用改代码；想再降需要引入分类模型，刻意不做。
- **同题归并用字符 Jaccard（阈值 0.55）**，不引入 AI 模型；短标题可能误并或漏并。
- **剪贴板写入会覆盖你当前剪贴板**。WebView2 在 `file://` 下 `navigator.clipboard` 不可靠，所以走后端 Win32 API。
- **旧收藏没有分区信息**：`collected.tag` 是后加的列，本次升级前收藏的条目 tag 为空，导出时归入「未分类」；重新收藏一次即可带上分区。
- **素材库必须自己填 key**：图片/视频要 Pexels、Pixabay 或 Unsplash 任一 key；音乐 ccMixter 免 key、Jamendo 要 client_id。key 只存本机 `radar.db` 的 `settings` 表，不随 exe 分发，发给别人时对方要填自己的。
- **素材只存链接不下载**：账本里是原页与文件直链，文件本身去 Pexels 官网下；这样不占磁盘也不替你决定用途。
- **Pexels 免费额度 200 次/小时**，超了会提示「配额用完」。
- **⚠ 分发前先清掉 key**：API key 存在 `data\radar.db` 的 `settings` 表里。把带 key 的 `data\` 连同程序发给别人（或上传网盘/仓库）＝把 key 一起给出去。分享前删掉整个 `data\` 文件夹即可（程序会自动新建空库）。
- **启动即刷新**：先秒开上次数据，随即自动抓一次最新（约 2–4 秒）；也可随时手动「刷新」。
- **打包后 exe 不弹黑框**（windowed），出错只体现在界面上的 toast，不会留控制台日志。

---

## 目录结构

```
F:\视频创作助手\
├─ README.md            # 本文件，构想与运维真源
├─ app.py               # pywebview 窗口 + js_api（抓取/视图/收藏/导出/标签表）
├─ common.py            # Item 数据结构 + 标准库 HTTP
├─ fetch.py             # 命令行入口：python fetch.py baidu|all
├─ fetch_baidu.py
├─ fetch_bilibili.py
├─ fetch_weibo.py
├─ fetch_zhihu.py
├─ fetch_pexels.py       # Pexels 素材搜索（图片 + 视频），需免费 key
├─ fetch_pixabay.py      # Pixabay 素材搜索（图片 + 视频），需免费 key
├─ fetch_unsplash.py     # Unsplash 图片搜索，需免费 Access Key
├─ fetch_music.py        # 音乐：ccMixter（免 key）+ Jamendo（client_id）
├─ db.py                # SQLite：批次入库（channel 区分综合/分区榜）/ 30 天清理 / 收藏 / settings（字号、隐藏分区）
├─ clip.py              # Win32 剪贴板（写 + 读回自检）
├─ selfcheck.py         # 离线自检，失败即断言
├─ tools\build_icons.py # SVG → web/icons.js sprite
├─ tools\make_icon.py   # 生成应用图标（Pillow 绘制，暖橙雷达）
├─ tools\check_migrate.py        # 旧库迁移验证（复制生产库，确认加 channel 列不丢数据）
├─ tools\check_channel_rising.py # 分区升温端到端验证（真实网络 + 临时库）
├─ assets\icons\        # Tabler Icons（MIT）
├─ assets\appicon.ico   # 应用图标（7 尺寸），打包与窗口共用
├─ assets\appicon.png   # 1024 预览
├─ web\appicon.png      # 128，侧栏 logo
├─ web\index.html       # 单页界面（暖亮）
├─ web\icons.js         # 生成物，勿手改
├─ .venv\               # Python 3.12 虚拟环境
├─ build\               # PyInstaller 中间产物
└─ dist\创作雷达\        # 打包产物（onedir，27 MB）
```

## 变更记录

| 日期 | 内容 |
|---|---|
| 2026-10-22 | 构想定稿：v1 只做热点，抖音暂缓；桌面 exe，onedir 打包 |
| 2026-10-22 | v1 完成：4 源打通、三类视图、聚类与升温、收藏导出、打包 27 MB、离线自检通过 |
| 2026-10-22 | 界面改为暖亮配色（米白+橙），侧栏浅米色分层；升温对比基准改为「至少 10 分钟前最近一批」，避免连点刷新后升温榜全空 |
| 2026-10-22 | 自绘应用图标（暖橙雷达）：exe 图标、窗口图标、侧栏 logo 统一；`tools/make_icon.py` 可改色重生成 |
| 2026-10-22 | 图标改**无底透明**：去掉圆角方底，图形本身用橙色渐变（#ff915a → #f4581e），侧栏 logo 加浅橙圆角承托 |
| 2026-10-22 | 新增**领域分区**：10 类各有图标与专属色、带条数，卡片标签同步上色；关键词表扩到 9 类，未分类从 78% 降到 67% |
| 2026-10-22 | 分区接入**平台专属榜**（B站 17 个分区 rid、百度 finance/sports、微博文娱榜），点分区自动切到列表视图并显示「综合 7 条 + 分区榜 30 条」 |
| 2026-10-22 | **P1 分区榜落库**：items 加 `channel` 列（综合热榜为空、分区榜为分区名），分区榜与综合热榜各存各的批次；同一分区再点时算分区内排名涨幅，升温度并入「升温中」视图（卡片带 ↑N 与「分区榜」标记）。旧库自动 `ALTER TABLE` 迁移（实测 6878 条旧数据全留） |
| 2026-10-22 | **P2 选题夹按分区分组导出**：`collected` 加 `tag` 列（旧库自动迁移），收藏时记下领域分区；导出 Markdown 按 TAGS 顺序分组、缺分区归「未分类」；顺带修分区榜条目收藏后丢失来源的问题（前端 `findItem` 跨 CH 查找），以及切换分区后子分类 chips 不清空的残留 |
| 2026-10-22 | **P5 界面细节**：卡片紧凑化（标题单行 + hover 看全文、去掉重复组头、多平台链接并排、操作按钮 hover 才显）——一屏从 4 张到 6 张；侧栏分区 chips 改 flex-wrap，名字不再被省略；新增字号三档 A-/A/A+（基准 `--fs`，关键文字用 `calc(var(--fs)*系数)`）；新增「分区」面板可勾选隐藏不用的分区。设置存 SQLite `settings` 表（`file://` 下 localStorage 不可靠） |
| 2026-10-22 | **v2 素材库**：Pexels 图片 + 视频搜索（`fetch_pexels.py`，免费 key、200 次/小时），结果网格带缩略图/尺寸/时长/作者；收藏进 `materials` 表生成**授权账本**，导出 Markdown 含作者、作者主页、原页、文件直链、授权、收录日期；按决定**不下载文件**。实测：Pexels API 无 key 401、CDN 可直连；Openverse/Wikimedia 本机不可达故放弃 |
| 2026-10-22 | **素材库扩到五源**：新增 `fetch_pixabay.py`（图+视频）、`fetch_unsplash.py`（图）、`fetch_music.py`（ccMixter 免 key + Jamendo）；`material_search` 改为按已填 key 并行搜所有可用源、结果混排并标平台；materials 加 `license_url` 列（CC 授权可点回原文）；素材页加「音乐」类型、齿轮按钮改 key；账本导出按图片/视频/音乐分组，音乐组带 NC 警告。实测：ccMixter 12 条、导出含 CC 链接；修掉 ccMixter 在 limit≥15 时的 `LineTooLong`（放宽 `http.client._MAXLINE` 到 1MB） |
| 2026-10-22 | **开源发布**：公开仓库 [dr-ze-crat/creative-radar](https://github.com/dr-ze-crat/creative-radar)（GPL-3.0）；v1.0.0 Release 附 Windows x64 打包 |
| 2026-10-22 | **便携 + 课堂版**：`data_path()` 改为便携优先（程序同目录 `data\radar.db` 可写就用，否则回退 LOCALAPPDATA）；窗口尺寸按屏幕自适应；产出 `创作雷达_课堂版_2026-10-22.zip`（14.31 MB，含预置 9653 条热榜/54 批、3 条选题夹、2 条素材账本、`课堂使用说明.txt`）。普通版同名 zip 重打，Release 发 **v1.0.1** |

---

## 协议
[GPL-3.0](LICENSE) © 2026 创作雷达 contributors

界面图标来自 [Tabler Icons](https://tabler.io/icons)（MIT），素材来自 Pexels / Pixabay / Unsplash / ccMixter / Jamendo，各自授权见软件内「素材账本」。
