# CHANGELOG

## v1.0.0 — 2026-11-09（公开在线阅读版首次发布）

- 从私有完整版导出：6090 题 / 438 份试卷 / 八个专题，题量与编号版本保持一致。
- 移除 18 册打印 PDF（426 MB）、`export-index/`、`pdf-worker.js` 与 pdf-lib；隐藏所有依赖它们的 PDF 下载入口，首页说明与页脚文案相应改写。
- 20,403 张答案影印 JPG 转为 WebP（质量 82，method 4），同步改写 `presentation.json` 图片引用；小样目检确认小字、上下标与结构式清晰。
- 发布目录由 2.08 GB 降至 1 GB 以下，满足 GitHub Pages 上限。
- 新增公开版 README / NOTICE / MIT LICENSE（仅覆盖代码）/ CONTRIBUTING、Pages 发布 workflow 与纯标准库校验器。
- 版权口径改为「题目来自公开渠道、版权归原权利人、侵权可联系移除」。

### 已知限制

140 题暂无参考答案；159 处存量 KaTeX 错误（47 题）；影印答案不可全文搜索；不提供 PDF 下载。
