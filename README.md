# Van 化学竞赛题库 · 在线阅读版

一个**纯静态**的化学竞赛题库看板：按八个专题阅读、按届次与来源筛选、题干关键词检索、AI 知识点组卷（本地索引）。

- **6090 道完整大题 / 438 份试卷**，八个专题
- 无数据库、无后端、无构建步骤、无外部 CDN；公式由仓库内自带的 KaTeX 渲染
- `site/` 即整站，可直接用 GitHub Pages 或任意静态服务器托管
- **在线阅读版不提供 PDF 下载**，需要离线保存请用浏览器打印（或 AI 组卷结果里的「打印题目 / 打印答案」）

在线地址：本仓库启用 GitHub Pages 后形如 `https://<用户名>.github.io/<仓库名>/`。

## 本地运行

```bash
git clone <本仓库地址>
cd <仓库目录>/site
python -m http.server 8736
# 打开 http://127.0.0.1:8736/
```

不要直接双击 `index.html`——`file://` 下浏览器会拦截 JSON 读取。首次加载约 30 MB 题库数据，稍等即可；题图按需懒加载，断网也能用。

## 目录

```
├─ site/                     ★ 看板整站（Pages 发布这个目录）
│  ├─ index.html / app.js / *.css / *.js
│  ├─ questions.json         题目元数据
│  ├─ presentation.json      题干与答案（前端唯一渲染内容源）
│  ├─ numbering.json         专题内编号与 countsByTopic
│  ├─ knowledge-index.json   AI 组卷知识点索引
│  ├─ assets/                题图与答案影印（WebP）
│  ├─ vendor/katex/          本地 KaTeX 0.16.22（MIT）
│  └─ NOTICE.md
├─ tools/validate_public.py  纯标准库一致性校验（CI 使用）
├─ .github/workflows/        Pages 发布与校验
├─ LICENSE                   代码 MIT；题目内容不在授权范围内
└─ NOTICE.md                 来源、版权与第三方组件
```

## 功能

| 功能 | 说明 |
| --- | --- |
| 浏览 | 八专题 → 届次 → 试卷 → 题目，支持专题题号跳转 |
| 检索 | 题名 / 题干关键词，空格分隔为「与」，可限定专题、届次、试卷，可勾选「同时搜索答案」 |
| 筛选 | 来源机构、CChO 届次（含「Chemy 联赛」「未知届次」） |
| AI 组卷 | `ai-config.json` 为 `local` 模式，用本地知识点索引选题，不发任何网络请求 |
| 打印 | 浏览器打印，或 AI 组卷结果的「打印题目 / 打印答案」 |

**不提供**：专题题目册 / 答案册 PDF、单题 PDF、自选练习卷 PDF。这些功能依赖大体量的打印册文件，已在公开版中移除。

## 数据与维护

- 题目图片统一为 WebP（质量 82），在保持小字与结构式清晰的前提下把发布目录压到 1 GB 以内。
- 数据由内部工作区生成后导出，改动后请运行 `python tools/validate_public.py`。
- 勘误、加题、文件格式说明见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 已知限制

140 题标注「暂无参考答案（待补录）」；159 处存量 KaTeX 渲染错误（47 题）；少量 PUA / 替换字符与文本化反应式；影印答案不可全文搜索；部分题名允许为空。题库内容存在历史 OCR / 切图误差，欢迎提交勘误。

## 版权

题目与参考答案来自公开渠道的网络资源，版权归各原命题组及相应权利人所有，本站仅作学习交流整理，不用于商业用途。详见 [NOTICE.md](NOTICE.md)。
