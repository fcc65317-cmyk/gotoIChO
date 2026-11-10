# 协作说明

欢迎提交勘误与改进。仓库只放**在线阅读版看板**与生成/校验脚本，不含题目入库 / 切题 / OCR 工具，也不含打印册 PDF。

> `site/` 由 [`tools/build_public_site.py`](tools/build_public_site.py) 从维护者的本地工作台一步生成。直接改 `site/` 的 PR 会在下次刷新时被覆盖；维护者会把改动回写到内部源数据，再重新生成并合并。勘误台账见 [ERRATA.md](ERRATA.md)，字段说明见 [docs/DATA-FORMAT.md](docs/DATA-FORMAT.md)。

## 三类贡献

| 类型 | 改哪里 | 要求 |
| --- | --- | --- |
| 勘误纠错 | `site/presentation.json` 中该题的 `body` / `answer` | 在 Issue 或 PR 里写明题 ID、错误内容、正确内容与依据（原卷页码 / 官方答案） |
| 元数据修正 | `site/questions.json` 的 `tags` / `title` / `topic` / `edition` | 不改 `id`、不改 `provenance`、不动正文 |
| 新增题目 | 三层同批登记：`questions.json` + `presentation.json` + `numbering.json` | 同时写 `numberById` 与 `countsByTopic`；图片放 `site/assets/`，只以 `assets/...` 相对路径引用 |

改完运行：

```bash
python tools/validate_public.py
```

CI 会在每个 PR 上跑同一份校验（纯标准库，Python 3.9+）。

## 硬性规则

1. 三层键集必须一致：`questions.json` = `presentation.json` = `numbering.json.numberById`。
2. `sum(countsByTopic.values())` 必须等于题目总数；专题内编号不得重号。
3. 图片一律 WebP，正文引用 `assets/...`，不得出现悬挂引用。
4. `edition` 只取真实 CChO 届次、`0`（联赛类合集）或 `"unknown"`；禁止 `bank`。
5. 专题内编号必须从 1 连续（本版剔除 Chemy 题后重新排定）；正文里的小问标签与「原第 N 题」沿用**原卷编号**，与专题编号不同，属预期口径，不要批量替换。
6. 新增题必须写清来源；**不要上传整份原卷 PDF 或来源不明的材料**。
7. 单题 PDF 与选题库走浏览器打印视图（`window.print()`），不依赖任何外部文件；**不要重新引入 18 册打印册、`export-index/`、`pdf-worker.js` 或 pdf-lib**，它们会让发布目录超过 GitHub Pages 的 1 GB 上限。
8. 不提交任何密钥、`.env` 或本机绝对路径。
9. 不要重新引入中间快照层：`site/` 必须能由 `tools/build_public_site.py` 从内部 `dist/` 一步重建；不要把 18 册打印册、原始 JPG 大图或审核台文件放进仓库。

## 题库来源

题目来自公开渠道的网络资源，版权归原权利人。提交新题前请确认来源适合公开展示；若收到权利人移除请求，维护者会立即处理。
