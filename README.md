# 河北冀勘官网

河北冀勘工程技术服务有限公司官网（hebeijikan.com）的静态站点源码。

产物是**纯静态 HTML**，无运行时框架、无外部依赖，可部署到 Netlify、阿里云 OSS
或任何静态托管。构建脚本只用 Python 标准库，不需要 Node、不需要 npm。

---

## 目录结构

```
hebeijikan-site/
├── build.py               构建脚本（零依赖，Python 3）
├── netlify.toml           Netlify 构建与缓存配置
├── content/
│   └── site.json          ★ 全站唯一事实来源：公司信息、资质、项目数据、联系方式
├── src/
│   ├── layout.html        页面外壳（head、结构化数据）
│   ├── partials/          页头、页脚
│   ├── pages/*.html       10 个页面的正文与 front-matter
│   └── assets/            css / js / img
├── dist/                  构建产物（不提交，已 gitignore）
└── ACCOUNTS.local.md      账号与域名信息（不提交，已 gitignore）
```

## 本地开发

```bash
python3 build.py            # 构建到 dist/
python3 build.py --serve    # 构建并启动 http://127.0.0.1:8000
```

改完源码需要重新跑一次 `build.py`，没有热更新。

内部评审时可以用查询参数预览备用配色：`?skin=earth`、`?skin=dark`。
正式访客始终看到默认配色，这个参数只是内部工具。

---

## 改内容

**绝大多数内容改动只需要动 `content/site.json`**，不用碰 HTML。
电话、地址、项目数据、资质信息、招聘内容都在里面，改完重新构建即可全站生效。

需要改版式或增删页面时才动 `src/`。新增页面：在 `src/pages/` 放一个
`.html`，开头必须有 JSON front-matter 注释（`title`、`description`，
可选 `keywords`、`faq`、`jsonld`），然后在 `build.py` 的 `PAGE_INDEX`
和 `src/partials/header.html` 里登记。

### 咨询表单

表单标记已按 Netlify 官方文档逐条核对，改动时注意：

- `data-netlify="true"` 触发检测，`name="inquiry"` 是后台里的表单名，两者不能删
- 隐藏字段 `form-name` 的值必须与表单 `name` 一致
- 蜜罐：`netlify-honeypot="bot-field"` 与同名隐藏输入框成对存在，删一个防不住垃圾提交
- `action` 必须是以 `/` 开头的站内路径，**不要带查询字符串**（文档未记载支持）；
  现指向 `/thanks.html`，该页是 `noindex`，不进 sitemap 与 llms.txt
- `name="email"` 字段让通知邮件的回复地址自动指向客户，别改这个字段名

### 内容硬约束

1. **不要凭印象修改或编造任何编号、文号、日期、数字。** 站内的评审文号
   （如 `自然资矿评储字〔2024〕6 号`）、证书编号（`DZKJ2025C-1-029`、
   `A213041370`）、钻探进尺（`21041.44` 米）、品位（`36.18%`）均来自
   公司简介 PDF 与证书原件。这些是甲方会去主管部门官网核验的数据，
   错一个字就是信任事故。改动前先核对原件。
2. **不引用任何境外资源。** 不使用 Google Fonts、CDN 托管的 JS/CSS、
   外部图床——境内访问会卡顿甚至超时。中文用系统字体栈，一切资源自托管。
3. **不使用中文 Web Font。** 一套中文字体动辄数 MB。
4. **关键信息必须是文字，不能是图片。** 电话、地址、办证流程都要是可选中、
   可被搜索引擎和大模型读取的 HTML 文本。
5. **正文最小字号 12px**，正文与背景对比度不低于 4.5:1。
6. **资质证书展示图必须带水印**，且不上传扫描原件（宽度上限 1200px）。
   水印脚本在仓库外：`~/workspace/myh/docs/hebeijikan/watermark.py`。

---

## 发布方式一：Netlify（当前线上方式）

仓库已连接 Netlify，**`git push` 到 `master` 即自动部署**。
`netlify.toml` 已声明构建命令，Netlify 会在它的服务器上执行：

```toml
[build]
  command = "python3 build.py"
  publish = "dist"
```

你本地不需要跑任何命令。

### 注意：构建失败 = 发不出去

加了构建步骤之后，如果脚本报错（例如 `site.json` 少了逗号），Netlify 会
**构建失败并保持线上为旧版**。好处是不会发出坏页面，坏处是你以为发了其实没发。
**推完请去 Netlify 看一眼构建状态**，或在后台开启部署失败通知。

### 建议的发布流程

1. 开分支推送，Netlify 自动生成 Deploy Preview 链接
2. 用预览链接确认构建成功、页面正常、图片加载
3. 合并到 `master`
4. 检查线上：页面能开、导航无 404、页脚地址与电话正确

### 需要在 Netlify 后台手动配置的（文件管不了）

- **表单通知邮箱** —— `Project configuration → Notifications → Emails and webhooks
  → Form submission notifications`（此路径已按官方文档核实）。收件人填
  `hbjk111@126.com`。**不配的话咨询表单提交只躺在后台，没人知道。**
  注意该区块要等 Netlify 检测到表单后才出现，也就是**部署之后**才能配。
- **部署失败邮件通知** —— 同页 `Deploy notifications → Add notification →
  Deploy failed`。加了构建步骤后，构建失败会静默保持旧版，没有通知你不会知道。
- **关闭 Pretty URLs 后处理** —— `Build & deploy → Post processing →
  Asset optimization`。本站自己输出干净路径，后处理再改写一次是多余的。
- **站点归属** —— 如需公司自持线索，`General → Transfer site`。

---

## 发布方式二：阿里云 OSS（国内托管）

阿里云 OSS 没有构建能力，所以**本地构建后上传 `dist/`**：

```bash
python3 build.py
# 然后把 dist/ 整个目录上传到 OSS bucket 根目录
```

上传可以用控制台拖拽，或用 ossutil：

```bash
ossutil cp -rf dist/ oss://<bucket名>/ --meta "Cache-Control:public, max-age=0, must-revalidate"
```

### OSS 需要配置的项

1. **静态网站托管**：默认首页 `index.html`，默认 404 页 `index.html`
2. **绑定自定义域名** `hebeijikan.com` 并配置 CNAME
3. **开启 CDN**（否则 OSS 直连速度一般）
4. **HTTPS 证书**
5. **缓存策略**：HTML 设 `max-age=0, must-revalidate`；
   `assets/` 下的图片与 CSS 可设长缓存

### 迁移前必须确认

- **ICP 备案主体**必须与实际使用者一致（现为河北冀勘，备案号
  `冀ICP备2021011758号`）。国内托管会被核查，主体不符会有麻烦。
- 咨询表单依赖 Netlify Forms，**迁到 OSS 后表单会失效**，需要改成
  阿里云函数计算、表单服务，或退回到"电话 + 邮箱"。

---

## SEO 与 AI 可见性

本站的目标读者除了人，还有搜索引擎和大模型。已做的：

- **纯静态 HTML**：爬虫与大模型不执行 JS，服务端直出的 HTML 是最好读的形态
- **结构化数据**：每页 `LocalBusiness`，技术服务页附 `FAQPage`
- **`/llms.txt`**：给大模型的站点索引，列出核心事实、页面清单与联系方式
  （llmstxt.org 提议规范，构建时自动生成）
- **`robots.txt` 显式放行 AI 爬虫**：GPTBot、ClaudeBot、PerplexityBot、
  Bytespider、Baiduspider 等，避免被无意屏蔽
- **答案形态的内容**：技术服务页把办证流程写成"办采矿证需要准备哪些报告？"
  这类问题 + 直接回答，这是大模型最容易引用的形态
- **每页独立 title / description / canonical**，自动生成 sitemap.xml

### 上线后要做的（这几步比站内优化更重要）

1. **百度站长平台**提交 sitemap 并做主动推送 —— 国内大模型的信息来源
   很大程度依赖百度索引，这是国内 AI 可见性的地基
2. **微信公众号同步**那三篇办证流程内容 —— 微信搜一搜与元宝里公众号权重高
3. **访问速度**：Netlify 无大陆节点，境内访问慢会直接降低爬虫抓取成功率。
   如果 AI 可见性是重点，迁国内云的收益比任何站内优化都大

### 不要做

给爬虫看与用户不同的内容（cloaking）、堆砌隐藏关键词。会被判作弊，
且对大模型无效——它们读的就是普通访客看到的那份 HTML。

---

## 统计与站长平台（已注册，别重复注册）

### 百度统计 tongji.baidu.com

| 项 | 值 |
|---|---|
| 站点 ID | `42f143c4389e1c543f9dcc1b35e9fe6d` |
| 代码位置 | `content/site.json` → `analytics.baiduId`，由 `src/layout.html` 渲染进每个页面的 `<head>` |
| 登录账号 | 见 `ACCOUNTS.local.md` |

统计 ID 不是密钥（网页源码里公开可见），所以正常提交进版本库。**换账号只需改 `site.json` 一处**，全站生效。

代码放在 `<head>` 末尾，位置有讲究：百度那段脚本用
`document.getElementsByTagName("script")[0]` 找插入锚点，**页面里必须已经存在至少一个
`<script>` 标签**，否则会报错。我们的 JSON-LD 结构化数据正好在它前面，不要调换顺序。

**已埋的四个事件**（`src/assets/js/site.js`），都带来源页面路径：

| 事件类别 | 动作 | 说明 |
|---|---|---|
| 联系 | 点击电话 | 记录是哪个页面的电话被点 |
| 联系 | 点击邮箱 | 同上 |
| 联系 | 提交表单 | 表单提交动作 |
| 联系 | 表单提交成功 | 到达 `/thanks.html` 才算，比监听提交更准，这是真正的转化 |
| 联系 | 地图导航 | 记录点的是高德还是百度 |

查看位置：百度统计 → **行为分析 → 事件分析**。

**最该看的一个数字**：哪个页面贡献的「点击电话」最多。它会告诉你线索从哪来，决定后续内容往哪投。

埋点函数做了 `window._hmt` 存在性判断并包了 try/catch——**百度脚本加载失败不会影响网站本身**。

### 百度搜索资源平台 ziyuan.baidu.com

| 项 | 值 |
|---|---|
| 验证方式 | HTML 标签 |
| 验证码 | `code-bLrF3sJh2o` |
| 代码位置 | `src/layout.html` 的 `<meta name="baidu-site-verification">` |
| 登录账号 | 见 `ACCOUNTS.local.md` |

⚠️ **这个验证码是从改版前的老站继承下来的**，说明之前有人验证过。
**不要删掉那行 meta**，删了站点归属验证会失效。如果登录不进原账号，需要重新验证并替换验证码。

**为什么这个平台重要**：国内大模型（豆包、元宝、Kimi 等）的信息来源很大程度依赖百度索引。
百度收录是国内 AI 可见性的地基，比任何站内优化都更影响「AI 回答问题时会不会提到你们」。

**上线后要做的三件事**：

1. **提交 sitemap** —— 数据引入 → 链接提交 → sitemap，填
   `https://hebeijikan.com/sitemap.xml`（构建时自动生成）
2. **配置主动推送** —— 链接提交 → 主动推送，页面上有推送接口和 token。
   token 属于密钥，**写进 `ACCOUNTS.local.md`，不要提交进版本库**。
   拿到后可在 `build.py` 末尾加一个可选步骤，构建完自动推送全部页面 URL
3. **填写站点属性** —— 公司名、联系方式、logo，搜索结果的展示会更完整

主动推送与 sitemap 的区别：sitemap 是「等百度来抓」，主动推送是「改完立刻告诉百度」，收录速度差很多。

### 还没做的

- **微信公众号**：`河北冀勘工程技术服务有限公司`。微信搜一搜与元宝里公众号权重很高，
  建议把技术服务页那三条办证流程扩写成文章同步过去，收益可能比网站本身更大

## 待办

- [ ] **ISO9001 证书 2026-10-23 到期**，确认换证进度后再上线资质页，
      避免官网挂出即将过期的证书
- [ ] Netlify 表单通知邮箱尚未配置
- [ ] 溶洞案例桩号（K37+245 等）是否可公开展示，建议与甲方确认
- [ ] 补充深源公司地址
- [ ] 域名 2031-05-20 到期，建议开启自动续费
- [ ] 百度搜索资源平台：提交 sitemap、配置主动推送（见上一节）
- [ ] 冀勘经营范围是否覆盖市政业务（市政页目前作为自有能力呈现）
- [ ] 深源、秦凯的持股关系是控股还是参股，据工商登记写准
- [ ] 三条办证流程扩写成文章并同步微信公众号

账号与域名信息见 `ACCOUNTS.local.md`（不在版本库中）。
