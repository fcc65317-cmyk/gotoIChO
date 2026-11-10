#!/usr/bin/env python3
"""公开在线阅读版一致性校验（纯标准库，Python 3.9+，无第三方依赖）。

    python tools/validate_public.py
    python tools/validate_public.py --root <仓库根>

检查：三层键集 / counts / 专题编号连续 / Chemy 题已剔除 / 图片引用与格式 /
发布目录体积 / 打印册资产已移除 / 单题与选题库入口可见 / 首页数字 /
edition / 明文密钥。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ASSET_RE = re.compile(r"assets/([A-Za-z0-9_\-\.%#\u4e00-\u9fff]+?\.(?:jpg|jpeg|png|webp|svg|gif))", re.I)
SENSITIVE = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "疑似明文 API token"),
    (re.compile(r"[Tt]:[\\/]Aiwork|[Cc]:[\\/]Users"), "本机绝对路径"),
    (re.compile(r"MINERU_TOKEN\s*=\s*['\"]sk-|DEEPSEEK_API_KEY\s*=\s*['\"]"), "硬编码凭据"),
]
TEXT_EXT = {".json", ".html", ".css", ".js", ".md", ".svg", ".txt", ".yml", ".yaml", ".py"}
MAX_FILE = 100 * 1024 * 1024
MAX_SITE = 1024 * 1024 * 1024  # Pages 已发布站点上限 1 GB

failures: list[str] = []
warnings: list[str] = []


def main() -> int:
    ap = argparse.ArgumentParser(description="校验公开版看板")
    ap.add_argument("--root", type=Path, default=REPO)
    root: Path = ap.parse_args().root.resolve()
    site = root / "site"
    if not site.is_dir():
        print("[FAIL] 缺少 site/ 目录")
        return 1
    print(f"仓库根：{root.name}")

    try:
        qs = json.loads((site / "questions.json").read_text(encoding="utf-8"))
        pres = json.loads((site / "presentation.json").read_text(encoding="utf-8"))
        numbering = json.loads((site / "numbering.json").read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[FAIL] 数据 JSON 解析失败：{exc}")
        return 1

    qids, pids = {q["id"] for q in qs}, set(pres)
    nmap, nids = numbering.get("numberById", {}), set()
    nids = set(nmap)
    print(f"题目 {len(qs):,} 道 / {len({str(q.get('paper','')) for q in qs}):,} 份试卷")
    if qids == pids == nids:
        print(f"[OK] 三层键集一致（{len(qids):,}）")
    else:
        failures.append(f"三层键集不一致：q-only={len(qids-pids-nids)} p-only={len(pids-qids)} n-only={len(nids-qids)}")

    total = sum(v for v in numbering.get("countsByTopic", {}).values() if isinstance(v, int))
    if total == len(qs):
        print(f"[OK] countsByTopic = {total:,}")
    else:
        failures.append(f"countsByTopic {total:,} ≠ 题数 {len(qs):,}")

    pairs = [(str(q.get("topic", "")), nmap.get(q["id"])) for q in qs]
    dup = [k for k, c in Counter(pairs).items() if c > 1]
    if dup:
        failures.append(f"专题内编号重复 {len(dup)} 处，例 {dup[:3]}")
    else:
        print("[OK] 专题内编号无重号")

    per_topic = defaultdict(list)
    for q in qs:
        per_topic[str(q.get("topic", ""))].append(nmap.get(q["id"]))
    broken = [t for t, nums in per_topic.items() if sorted(nums) != list(range(1, len(nums) + 1))]
    if broken:
        failures.append(f"专题编号未从 1 连续排定：{broken[:3]}")
    else:
        print("[OK] 各专题编号均从 1 连续排定")

    chemy = [q["id"] for q in qs if str(q["id"]).startswith("chemy")]
    if chemy:
        failures.append(f"仍残留 {len(chemy):,} 道 Chemy 题，例 {chemy[:3]}")
    else:
        print("[OK] 公开版不含 Chemy 来源题")

    refs: set[str] = set()
    def walk(v):
        if isinstance(v, dict):
            for x in v.values(): walk(x)
        elif isinstance(v, list):
            for x in v: walk(x)
        elif isinstance(v, str):
            refs.update(m.group(1) for m in ASSET_RE.finditer(v))
    walk(pres)
    assets = site / "assets"
    disk = {p.name for p in assets.iterdir() if p.is_file()} if assets.is_dir() else set()
    missing = refs - disk
    if missing:
        failures.append(f"图片悬挂引用 {len(missing):,} 张，例 {list(missing)[:3]}")
    else:
        print(f"[OK] 图片引用零缺失（{len(refs):,} 张）")
    jpg_refs = {r for r in refs if r.lower().endswith((".jpg", ".jpeg"))}
    if jpg_refs:
        failures.append(f"仍存在 {len(jpg_refs):,} 处 JPG 引用未转 WebP，例 {list(jpg_refs)[:3]}")
    else:
        print("[OK] 图片引用全部指向 WebP")

    nfiles = nbytes = 0
    big = []
    for p in site.rglob("*"):
        if p.is_file() and not p.is_symlink():
            nfiles += 1
            nbytes += p.stat().st_size
            if p.stat().st_size > MAX_FILE:
                big.append(str(p.relative_to(site)))
    if big:
        failures.append(f"单文件 >100 MiB：{big[:3]}")
    if nbytes > MAX_SITE:
        failures.append(f"发布目录 {nbytes/1073741824:.2f} GB 超过 Pages 1 GB 上限")
    else:
        print(f"[OK] 发布目录 {nfiles:,} 文件 / {nbytes/1048576:.1f} MB（< 1 GB）")

    forbidden = ["downloads", "export-index", "pdf-worker.js",
                 "review.html", "overlap.html", "review-flags.json",
                 "review-source-index.json", "sources"]
    left = [n for n in forbidden if (site / n).exists() or (site / n).is_symlink()]
    if left:
        failures.append(f"仍存在已移除的资产：{left}")
    else:
        print("[OK] 打印册 / 裁剪索引 / 审核台资产均已移除")

    css = (site / "styles.css").read_text(encoding="utf-8")
    if "#downloads" in css and "display: none" in css:
        print("[OK] 专题册直链与 AI 组卷旧 PDF 按钮已隐藏")
    else:
        failures.append("styles.css 缺少隐藏旧 PDF 入口的样式")
    hide_block = css.split("/* 公开在线阅读版", 1)[-1] if "/* 公开在线阅读版" in css else ""
    if ".question-download" in hide_block or ".selection-tools" in hide_block:
        failures.append("单题下载 / 选题库入口被误隐藏")
    else:
        print("[OK] 单题下载与选题库入口保持可见")

    app = (site / "app.js").read_text(encoding="utf-8")
    if all(s in app for s in ("MAX_SELECTION = 10", "ai-printing", "专题 · 第 ${numbers[q.id]} 题", "localStorage")):
        print("[OK] 选题库 1-10 题 · 打印导出 · 专题编号 · 勾选持久化")
    else:
        failures.append("app.js 缺少选题库 / 打印导出 / 专题编号实现")

    html = (site / "index.html").read_text(encoding="utf-8")
    m = re.search(r"<strong>(\d+) 道完整大题</strong>", html)
    if not m or int(m.group(1)) != len(qs):
        failures.append("首页题数与数据不符")
    else:
        print(f"[OK] 首页题数一致（{len(qs):,}）")
    if "下载整个专题" in html or "专题题目 PDF" in html:
        failures.append("首页仍残留 PDF 下载说明")
    if 'href="NOTICE.md"' not in html:
        failures.append("首页未链接 NOTICE.md")
    for name in ("NOTICE.md",):
        if not (site / name).is_file():
            failures.append(f"site/{name} 缺失")

    bad_ed = [q["id"] for q in qs if str(q.get("edition", "unknown")) not in {"0", "unknown"}
              and not str(q.get("edition", "")).isdigit()]
    if bad_ed:
        failures.append(f"edition 非法 {len(bad_ed)} 题，例 {bad_ed[:3]}")
    else:
        print("[OK] edition 取值合法")
    odd = sum(1 for rec in pres.values() if isinstance(rec, dict)
              for f in ("body", "answer") if isinstance(rec.get(f), str) and rec[f].count("$") % 2)
    if odd:
        warnings.append(f"{odd} 个字段的 $ 数量为奇数（存量已知问题）")

    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "assets", "fonts"}]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in TEXT_EXT and fn not in {".gitignore", ".gitattributes"}:
                continue
            if p.name == "validate_public.py":
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pat, label in SENSITIVE:
                if pat.search(text):
                    hits.append(f"{p.relative_to(root).as_posix()} → {label}")
    if hits:
        failures.extend(f"敏感串：{h}" for h in hits[:10])
    else:
        print("[OK] 无明文密钥与本机绝对路径")

    print("\n" + "=" * 52)
    for w in warnings:
        print(f"[WARN] {w}")
    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        print(f"\n结果：FAIL（{len(failures)} 项）")
        return 1
    print(f"结果：PASS（{len(warnings)} 项 WARN）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
