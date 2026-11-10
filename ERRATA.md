# ERRATA · 勘误台账

> 面向本公开库的协作者。记录**已确认并已修好**的题目错误；发现错误请先提 Issue。

## 怎么报勘误

在仓库 **Issues → New issue → 题目勘误**，写清三样：

1. **题目 ID** 或网页上显示的「专题 · 第 N 题」编号；
2. **原卷出处**（届次、卷名、原卷题号）——网站每个专题重新连续编号，原卷题号才是对号最可靠的方式；
3. 错在哪里、正确内容是什么（可附截图）。

## 修好后记在这里

| 日期 | 题目 ID / 专题编号 | 原卷出处 | 改了什么 | 已上线版本 |
| --- | --- | --- | --- | --- |
| — | — | — | 暂无记录 | — |

## 修勘误会动到哪里

公开库里的 `site/` 是**生成出来的**，不要直接改它（下次刷新会被整体覆盖）。维护者按以下顺序处理：

1. 在**本地工作台的源数据** `dist/` 里改 `presentation.json` 对应题 ID 的 `body` / `answer`（涉及题名、标签、届次时同步改 `questions.json` / `numbering.json`）；
2. 在 `public-site/` 下跑 `python tools/build_public_site.py` 重新生成整站；
3. 跑 `python tools/validate_public.py`，PASS 后提交、Push；
4. GitHub Actions 自动重新发布网站，约 3～10 分钟；
5. 回到本文件追加一行，并在提交说明里写清题号。

> 批量勘误累积后统一处理即可，流程相同，不需要额外的「回灌」步骤——本地源数据本来就是唯一的一份。

## 加新题

模板见 [`tools/question-template.json`](tools/question-template.json)，字段说明见 [`docs/DATA-FORMAT.md`](docs/DATA-FORMAT.md)。
新题同样先在内部源数据登记，再重新生成；公开版会自动剔除 Chemy 来源题、重新连续编号并重算首页统计，不用手动算题号。
