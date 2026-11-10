# Van 化学竞赛题库 · 在线阅读版

一个**纯静态**的化学竞赛题库看板：按八个专题阅读、按届次与来源筛选、题干关键词检索、AI 知识点组卷（本地索引），以及**单题 PDF / 选题库导出**。

- **4157 道完整大题 / 410 份试卷**，八个专题
- **不含 Chemy 系列题目**：为尊重上游整理项目的授权范围，`id` 以 `chemy` 开头的 1933 道题已整体剔除；完整版仅保存在维护者的本地工作台，不对外提供
- 无数据库、无后端、无构建步骤、无外部 CDN；公式由仓库内自带的 KaTeX 渲染
- `site/` 即整站，可直接用 GitHub Pages 或任意静态服务器托管
- 答案影印统一为 WebP（质量 82），发布目录约 0.8 GB，低于 GitHub Pages 的 1 GB 上限

在线地址：`https://fcc65317-cmyk.github.io/gotoIChO/`

## 编号口径（重要）

本版剔除题目后，**各专题编号已重新从 1 连续排定**，与内部完整版的题号并不一致。网页、目录跳题号、导出的 PDF 三者使用同一份 `numbering.json`，彼此一致；`numbering.json` 里的 `legacyNumberById` 记录了与内部完整版原编号的对照。每道题页面上也保留**原卷题号与出处**，便于回查。

## 单题 PDF 与选题库

| 功能 | 操作 |
| --- | --- |
| 下载本题 PDF | 每道题下方点「下载本题 PDF」 |
| 选题库 | 勾选「选入练习卷」，或点「按题目 / 试卷选题」按题号、名称、整卷、整届批量勾选 |
| 数量限制 | 一次 **1～10 道**；勾选会保存在浏览器本地，关闭页面也不会丢 |
| 导出 | 点「下载选题 PDF」→ 选「下载题目 PDF」或「下载答案 PDF」→ 页面自动排版并打开打印窗口 → 在打印窗口选**「另存为 PDF」**即可保存为一个 PDF |
| PDF 内的编号 | 每道题标题为「某某专题 · 第 N 题」，N 是**专题编号**（与网页一致）；原卷题号与出处另用小字标注 |

采用浏览器打印视图而非前端生成 PDF 文件，是为了让化学式、上下标、结构式与影印答案**和网页上完全一致清晰**，同时不增加任何依赖与体积。浏览器自带的「打印」也始终可用。

**不提供**：18 册专题打印册、单题/自选卷的旧版裁页 PDF。这些功能依赖大体量的整册 PDF，已在本版移除。

## 本地运行

```bash
git clone <本仓库地址>
cd <仓库目录>/site
python -m http.server 8736
# 打开 http://127.0.0.1:8736/
```

不要直接双击 `index.html`——`file://` 下浏览器会拦截 JSON 读取。首次加载题库数据稍等即可；题图按需懒加载，断网也能用。

## 目录

```
├─ site/                     ★ 看板整站（Pages 发布这个目录）
│  ├─ index.html / app.js / *.css / *.js
│  ├─ questions.json         题目元数据
│  ├─ presentation.json      题干与答案（前端唯一渲染内容源）
│  ├─ numbering.json         专题内编号、countsByTopic、内部编号对照
│  ├─ knowledge-index.json   AI 组卷知识点索引
│  ├─ assets/                题图与答案影印（WebP）
│  ├─ vendor/katex/          本地 KaTeX 0.16.22（MIT）
│  └─ NOTICE.md
├─ tools/
│  ├─ build_public_site.py   ★ 从内部 dist/ 一步生成本站
│  ├─ prune_chemy.py         剔除 Chemy 题 / 重新编号（由上一脚本调用）
│  ├─ validate_public.py     纯标准库一致性校验（CI 使用）
│  └─ question-template.json 加题模板
├─ docs/DATA-FORMAT.md       数据字典（改题前必读）
├─ .github/
│  ├─ ISSUE_TEMPLATE/errata.yml   勘误入口
│  ├─ PULL_REQUEST_TEMPLATE.md
│  └─ workflows/             Pages 发布与校验
├─ ERRATA.md                 勘误台账
├─ LICENSE                   代码 MIT；题目内容不在授权范围内
└─ NOTICE.md                 来源、版权与第三方组件
```

## 数据与维护

- 本仓库的 `site/` 由**维护者本地工作台的 `dist/`** 一步生成，入口是 [`tools/build_public_site.py`](tools/build_public_site.py)：剥离内部审核标记 → 剔除 Chemy 题 → 按专题重新连续编号 → 图片转 WebP → 清理孤儿图 → 重算首页统计 → 排除打印册与审核台资产。**请勿手改 `site/` 里的生成物**，下次刷新会被整体覆盖。
- 改动后请运行 `python tools/validate_public.py`（检查三层数据一致、编号连续、图片零缺失、无 Chemy 题、体积 < 1 GB、无密钥）。
- 勘误见 [ERRATA.md](ERRATA.md)，加题与字段说明见 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [docs/DATA-FORMAT.md](docs/DATA-FORMAT.md)。
- 维护者每次更新只需**一条生成命令 + 一次 Push**；GitHub Actions 会自动重新发布网站。

## 已知限制

部分题目标注「暂无参考答案（待补录）」；少量存量 KaTeX 渲染错误、PUA / 替换字符与文本化反应式；影印答案不可全文搜索；部分题名允许为空。题库内容存在历史 OCR / 切图误差，欢迎提交勘误。

## 版权

题目与参考答案来自公开渠道的网络资源，版权归各原命题组及相应权利人所有，本站仅作学习交流整理，不用于商业用途。前端代码采用 MIT 许可，**题目内容不在该许可范围内**。详见 [NOTICE.md](NOTICE.md)。
