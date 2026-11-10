# 数据字典（改题前必读）
> 注：公开在线阅读版已整体剔除 Chemy 来源题、专题编号重新连续排定；字段结构与内部完整版一致。

看板的全部内容由 `site/` 下**三层 JSON** 构成，三者以题目 `id` 为主键，必须严格一致。

## 1. 三层结构

| 文件 | 内容 | 谁渲染 |
| --- | --- | --- |
| `questions.json` | 数组，每题元数据：`id`、`topic`、`tags`、`title`、`number`、`paper`、`edition`、`points`、`percent`、`provenance`、`sourcePaperLabel`、`original_topic` 等 | 目录、筛选、来源标签、题号跳转 |
| `presentation.json` | 对象，`{ "<题ID>": { "body": "...", "answer": "...", "titleHtml": "..." } }` | **前端唯一渲染内容源**（题干/答案正文） |
| `numbering.json` | `numberById`（专题内连续编号 N）、`countsByTopic`、`version` | 「专题第 N 题」与 PDF 编号 |

> Chemy 存量题在 `questions.json` 里也带 `body`/`answer` 字段，属历史数据，**前端不读、不要改**；统一以 `presentation.json` 为准。
> 自有题的正文与答案**只在** `presentation.json`。

### 必须维持的不变量

1. 三层键集一致：`len(questions) == len(presentation) == len(numberById)`，且 ID 集合完全相同；
2. `sum(countsByTopic.values()) == 题目总数`；
3. 每个专题内 `numberById` 无重号；
4. `presentation.json` 里所有 `assets/...` 引用都指向 `site/assets/` 中真实存在的文件；
5. 正文里的 `$` 定界符成对（KaTeX 渲染 `$...$` / `$$...$$`）。

以上均由 `tools/validate.py` 检查。

## 2. 关键字段口径

| 字段 | 规则 |
| --- | --- |
| `id` | 全库唯一。Chemy 题为 `chemy{届}-{卷}-{题}` 前缀（溯源信息，不得「顺手清理」）；自有题形如 `ORG-1419`、`ANAL-0071` |
| `topic` | 八个专题之一；一题只属一个专题 |
| `title` | **允许为空字符串**。卷面无题名就留空，不要写「无题名」「(无标题)」等占位；前端遇空题名直接省略 |
| `number` | 原卷题号；**不是** `numbering.json` 里的专题编号 N |
| `edition` | 只取真实 CChO 届次、`0`（Chemy 联赛单列）或 `"unknown"`（机构自有系列届号）。**禁止 `bank`**。判定顺序：① IChO 预备题取卷面年份折算；② 联考卷「第 N 届」→ `unknown`（仅卷面同时写「第 N 届 + 初赛/决赛模拟」才采信 N）；③ 卷面写「第 N 届」→ N；④ 只写年份 → `年份 − 1986`；⑤ COBP 套卷 `NN-xx` → NN；⑥ 其余 → `unknown` |
| `tags` | 每题 ≤4 个考点，以题目内容为准 |
| `provenance` | 溯源信息（来源卷、页码等），**不要改** |

## 3. 正文与答案

- 正文是 HTML 片段；公式用 `$...$` / `$$...$$` 交给本地 KaTeX。
- 图片**只以相对路径** `assets/<文件名>` 引用（`<img src="assets/...">` 等）；自有题图命名 `<题ID>-<序号>-<sha12>.<ext>`。
- **题名只在 `title` 字段**，正文里不要再写题头。
- 自有题正文的小问标签一律 `N-x`（N = `numbering.numberById[id]`，**不是** `q.number`）；官方卷点格式 `1.1 / 2.1.1` 属例外，保留原样。
- 多数官方答案是**按题头影印的原卷裁片**（红字答案 / 蓝字说明 / 黑字题干，200dpi JPEG），因此不可全文搜索；不要试图转写成文字。
- 无答案的题使用占位文案「暂无参考答案（待补录）」，共 140 题，属已知限制。

## 4. 其他文件

| 文件 | 说明 |
| --- | --- |
| `knowledge-index.json` | AI 组卷知识点索引；改正文后需重算对应 `sourceHash`，本地模式才会选中新题 |
| `ai-config.json` | `{"mode":"local","backendUrl":""}`；保持 local 即完全离线 |
| `assets/` | 题图与答案影印；删除前确认无引用 |
| `downloads/` | 18 册专题打印 PDF（历史产物，6 册沿用旧编号） |
| `export-index/` | 单题 PDF 拼接所需的裁剪范围；与 `downloads/` 配套 |
| `vendor/` | KaTeX 0.16.22 + pdf-lib，含各自许可证 |

## 5. 新增题目（三层同批登记）

按 `tools/question-template.json` 填写，然后：

1. `questions.json` 追加元数据记录；
2. `presentation.json` 追加 `{ "<新ID>": { "body": ..., "answer": ... } }`；
3. `numbering.json` **同一批**写 `numberById["<新ID>"]`，并把对应专题的 `countsByTopic` +1；
4. 图片复制到 `assets/`，正文用 `assets/...` 引用；
5. 运行 `python tools/validate.py`，全部 PASS 再提交。

> 常见错误：只加前两层忘了 `numbering.json`（看板编号漂移）、图片没随附（悬挂引用）、`edition` 写成机构自有届号。
