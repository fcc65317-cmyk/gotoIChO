## 改动说明

<!-- 写明题 ID 与改动原因，例：errata(ORG-1419): 补回被题图吞掉的小问 3-2 题干 -->

## 改动类型

- [ ] 勘误纠错（题干 / 答案 / 图片）
- [ ] 元数据修正（tags / title / topic / edition）
- [ ] 新增题目
- [ ] 文档 / 工具 / 前端

## 检查表

- [ ] 只改了允许字段；没有改动 Chemy 存量题的 `body` / `answer`、`id` 或 `provenance`
- [ ] 三层键集仍一致（questions / presentation / numbering.numberById）
- [ ] 新增题已**同批**写入 `numbering.json` 的 `numberById` 与 `countsByTopic`
- [ ] 新增/替换的图片已放进 `site/assets/`，正文只以 `assets/...` 相对路径引用
- [ ] 小问标签为 `N-x`（N = numberById），题名无占位文字
- [ ] `edition` 只取真实届次 / `0` / `"unknown"`
- [ ] 勘误已在 `ERRATA.md` 追加一行（含依据）
- [ ] 新增题已写清来源，**未上传原卷 PDF / 无授权材料**
- [ ] 未引入任何密钥、token、`.env` 或本机绝对路径
- [ ] `python tools/validate.py` 结果为 PASS
- [ ] 本地起静态服务抽查过受影响题目

> 提醒：`site/` 是生成产物，请勿直接手改；改动请提请维护者在内部源数据中修改后重新生成。
