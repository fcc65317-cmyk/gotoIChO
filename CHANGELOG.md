# CHANGELOG

## v1.2.0 — 2026-11-10（撤掉私有库中间层，生成链路直连本地工作台）

- **不再需要私有库 `van_chem_question_bank`**：本地工作台 `dist/` 现在**一步直接生成**本站，省掉中间的 2 GB 快照仓库；维护者每次更新由「两条生成命令 + 两次 Push」简化为「**一条命令 + 一次 Push**」。
- 生成脚本迁入本仓库：`tools/build_public_site.py`（默认源改为 `dist/`）与 `tools/prune_chemy.py`。脚本自带原来中间层做的清洗：剥离 `reviewStatus`、`percent=0 → null`、首页去掉「审核状态」字样、只取被正文引用的题图；末尾仍由 `prune_chemy.apply()` 剔除 Chemy 题并重算首页。
- 迁移并保留协作能力：勘误 Issue 模板、PR 模板、`ERRATA.md` 勘误台账、`docs/DATA-FORMAT.md` 数据字典、`tools/question-template.json` 加题模板。
- 维护指南改为「本地工作台 + 公开库」两层口径；README / NOTICE / CONTRIBUTING 同步更新。
- 生成时**只取保留题目引用的题图**（不先把 1933 道待剔除题的图搬进来再删），原地覆盖重建、几乎零删除，约 3 分钟重建整站。
- 全量复现验证：`index.html` / `questions.json` / `presentation.json` / `knowledge-index.json` / `styles.css` 与上一版逐字节一致（`app.js` 仅 CRLF/LF 行尾差异，`numbering.json` 仅 JSON 键顺序差异、字段值全同）；`validate_public.py` PASS，冷启动 16 个资源 200、7 个已移除路径 404。
- 站点内容不变（4157 题 / 410 卷 / 806.9 MB），仅站点内 `NOTICE.md` 的「完整版存放位置」措辞更新。

## v1.1.0 — 2026-11-10（剔除 Chemy 题 + 单题 PDF / 选题库）

- **剔除 Chemy 系列题目 1933 道**（`id` 以 `chemy` 开头），公开版剩余 **4157 题 / 410 份试卷**；首页题数、卷数、届次分布、来源统计表、来源叙述与页脚同步重算，Chemy 相关措辞全部移除。
- **专题编号按本版剩余题目重新从 1 连续排定**；`numbering.json` 新增 `legacyNumberById` 记录与内部完整版原编号的对照，每道题仍保留原卷题号与出处。AI 组卷索引同步剔除对应条目并重算题数。
- 删除仅被剔除题目引用的题图 7646 张，发布目录进一步缩小。
- **重新开放单题 PDF 下载**，并新增**选题库**：勾选 1～10 道题，可分别导出「题目」或「答案」；页面自动排版后打开打印窗口，选「另存为 PDF」保存为一个 PDF。PDF 内每题标题使用**专题编号**，另附原卷题号与出处。
- 选题支持按题号 / 名称 / 整卷 / 整届批量勾选，勾选结果保存在浏览器本地；超过 10 道会提示并阻止。
- PDF 改用浏览器打印视图生成（化学式、上下标、结构式、影印答案与网页完全一致），不再依赖 18 册打印册、`export-index/`、`pdf-worker.js` 与 pdf-lib；专题册直链与 AI 组卷旧 PDF 按钮保持隐藏，打印功能保留。
- 校验器新增：Chemy 题零残留、各专题编号从 1 连续、单题/选题库入口可见、`app.js` 含选题库实现。
- 新增维护者工作区文档 `docs/本地与GitHub维护指南.md`（本地大项目与两个 GitHub 仓库的关系、每次同步步骤）。

### 已知限制

导出 PDF 需经过浏览器打印窗口选择「另存为 PDF」，不是一键直接下载文件；影印答案不可全文搜索；少量存量 KaTeX 错误与 OCR / 切图误差；部分题名允许为空。

## v1.0.0 — 2026-11-09（公开在线阅读版首次发布）

- 从私有完整版导出：6090 题 / 438 份试卷 / 八个专题，题量与编号版本保持一致。
- 移除 18 册打印 PDF（426 MB）、`export-index/`、`pdf-worker.js` 与 pdf-lib；隐藏所有依赖它们的 PDF 下载入口，首页说明与页脚文案相应改写。
- 20,403 张答案影印 JPG 转为 WebP（质量 82，method 4），同步改写 `presentation.json` 图片引用；小样目检确认小字、上下标与结构式清晰。
- 发布目录由 2.08 GB 降至 1 GB 以下，满足 GitHub Pages 上限。
- 新增公开版 README / NOTICE / MIT LICENSE（仅覆盖代码）/ CONTRIBUTING、Pages 发布 workflow 与纯标准库校验器。
- 版权口径改为「题目来自公开渠道、版权归原权利人、侵权可联系移除」。
