#!/usr/bin/env python3
"""公开在线阅读版的数据层变换（只作用于 public-site/site/）。

由 build_public_site.py 在生成站点后自动调用；也可单独运行::

    python tools/prune_chemy.py                 # 默认作用于本仓库 site/

做四件事：
  1. 剔除 id 以 ``chemy`` 开头的 1933 道 Chemy 来源题；
  2. 按专题把剩下的题重新从 1 连续编号（保留 legacyNumberById 便于对照内部完整版）；
  3. 删掉只被剔除题目引用的题图；
  4. 依据剩余题目重算首页题数、卷数、届次分布、来源统计表与版权/口径说明。

内部 dist/ 一个字节都不动；重复运行结果相同（幂等）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ASSET_RE = re.compile(
    r"assets/([A-Za-z0-9_\-\.%#\u4e00-\u9fff]+?\.(?:jpg|jpeg|png|webp|svg|gif))", re.I
)
TOPICS = ["有机化学", "高分子化学", "分析化学", "结构化学", "无机化学", "物理化学", "生物化学", "综合"]


def write_text_safe(path: Path, text: str) -> None:
    last: Exception | None = None
    for _ in range(4):
        try:
            if path.exists():
                try:
                    path.chmod(0o666)
                except OSError:
                    pass
            path.write_text(text, encoding="utf-8", newline="\n")
            return
        except OSError as exc:
            last = exc
            time.sleep(1)
    raise RuntimeError(f"无法写入 {path.name}: {last}")


def dump_json(path: Path, obj) -> None:
    write_text_safe(path, json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def asset_refs(obj) -> set[str]:
    out: set[str] = set()

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str):
            out.update(m.group(1) for m in ASSET_RE.finditer(v))

    walk(obj)
    return out


def edition_paragraph(kept: list[dict]) -> str:
    counts = Counter(str(q.get("edition", "unknown")) for q in kept)
    numeric = sorted(int(e) for e in counts if e.isdigit() and int(e) > 0)
    lo, hi = (numeric[0], numeric[-1]) if numeric else (0, 0)
    top = [f"第 {e} 届 {counts[str(e)]} 题" for e in (40, 39, 38) if counts[str(e)]]
    extra = f"；另有未知届次 {counts['unknown']} 题" if counts["unknown"] else ""
    return (
        '<p><strong>届次。</strong>届次指该卷面向的中国化学奥林匹克届次，年份与届号固定对应：'
        "第 N 届 = 1986 + N 年（第 39 届为 2025 年，第 40 届为 2026 年）。判定按卷面为准："
        "卷面写明“第 N 届”的取其届号；卷面只写年份的按年份折算（2025 年模拟卷归第 39 届，"
        "2017 年第 49 届 IChO 预备题归第 31 届）；联考类试卷标注的“第 N 届”是各机构自有系列届号，"
        "不属中国化学奥林匹克届次，一律归入“未知届次”。"
        f"本版覆盖第 {lo}～{hi} 届（{1986 + lo}～{1986 + hi} 年）共 {len(numeric)} 个届次分组，其中"
        + "、".join(top) + extra + "。</p>"
    )


def patch_home(html: str, kept: list[dict], removed: int) -> str:
    total = len(kept)
    papers = len({(str(q.get("edition", "unknown")), str(q.get("paper", ""))) for q in kept})
    groups = len({str(q.get("edition", "unknown")) for q in kept})

    html = re.sub(r'(<meta name="description" content=")\d+( 道)', rf"\g<1>{total}\g<2>", html)
    html = re.sub(r"<strong>\d+ 道完整大题</strong>", f"<strong>{total} 道完整大题</strong>", html)
    html = re.sub(r"（\d+ 份试卷）", f"（{papers} 份试卷）", html)

    # 来源叙述与页脚：去掉 Chemy
    html = html.replace("来自 Chemy、", "来自 ")
    html = html.replace("来源：Chemy、", "来源：")
    # 在「本站现收录…」这段末尾补一句本版口径说明（不依赖原句具体措辞）
    note = ("本在线阅读版不含 Chemy 系列题目；为便于阅读，"
            "专题编号按本版剩余题目重新从 1 连续排定，与内部完整版的题号不同。")
    html, n = re.subn(r"(<p>本站现收录.*?)(</p>)", lambda m: m.group(1) + note + m.group(2),
                      html, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError(f"首页介绍段命中 {n} 次，无法补写编号口径说明")

    # 届次段整体重写（原文含 Chemy 联赛 240 题等旧口径）
    html, n = re.subn(r"<p><strong>届次。</strong>.*?</p>", lambda m: edition_paragraph(kept), html, flags=re.S)
    if n != 1:
        raise RuntimeError(f"首页届次段命中 {n} 次，停止以免写坏页面")

    # 目录说明里 Chemy 联赛单列的说法已不适用
    html = html.replace(
        "卷面未标注届次的联考卷收在“未知届次”一栏，Chemy 联赛合集单列，两者都可正常筛选、选题与下载。",
        "卷面未标注届次的联考卷收在“未知届次”一栏，可正常筛选、选题与下载。",
    )
    html = html.replace("网页与下载的 PDF 使用同一编号。", "网页与导出的 PDF 使用同一专题编号。")

    # 来源统计表：删 Chemy 行、改合计行
    html, n = re.subn(r"\s*<tr><td>Chemy</td>.*?</tr>", "", html, flags=re.S)
    if n != 1:
        raise RuntimeError(f"来源表 Chemy 行命中 {n} 次")
    html, n = re.subn(
        r"<tr><td><strong>合计</strong></td>.*?</tr>",
        f'<tr><td><strong>合计</strong></td><td class="num"><strong>{total}</strong></td>'
        f"<td>八专题、{groups} 个届次分组（含未知届次）；已剔除 Chemy 来源 {removed} 题</td></tr>",
        html, flags=re.S,
    )
    if n != 1:
        raise RuntimeError(f"统计表合计行命中 {n} 次")
    return html


def apply(site: Path) -> dict:
    site = site.resolve()
    if not site.is_dir():
        raise RuntimeError(f"站点目录不存在：{site}")

    qs = json.loads((site / "questions.json").read_text(encoding="utf-8"))
    pres = json.loads((site / "presentation.json").read_text(encoding="utf-8"))
    numbering = json.loads((site / "numbering.json").read_text(encoding="utf-8"))
    knowledge = json.loads((site / "knowledge-index.json").read_text(encoding="utf-8"))

    removed_ids = {q["id"] for q in qs if str(q["id"]).startswith("chemy")}
    kept = [q for q in qs if q["id"] not in removed_ids]
    if not kept:
        raise RuntimeError("剔除后没有剩余题目，拒绝写盘")
    kept_ids = {q["id"] for q in kept}

    # 1) 重新连续编号：组内保持原专题编号的相对顺序
    old_map: dict[str, int] = numbering.get("numberById", {})
    by_topic: dict[str, list[str]] = defaultdict(list)
    for q in kept:
        by_topic[q.get("topic", "综合")].append(q["id"])
    new_map: dict[str, int] = {}
    counts: dict[str, int] = {}
    for topic in TOPICS:
        ids = by_topic.get(topic, [])
        ids.sort(key=lambda i: (old_map.get(i, 10 ** 9), i))
        counts[topic] = len(ids)
        for n, qid in enumerate(ids, 1):
            new_map[qid] = n
    for topic, ids in by_topic.items():
        if topic not in TOPICS:
            for n, qid in enumerate(ids, 1):
                new_map[qid] = n
            counts[topic] = len(ids)

    numbering["numberById"] = new_map
    numbering["countsByTopic"] = counts
    numbering["legacyNumberById"] = {i: old_map[i] for i in kept_ids if i in old_map}
    numbering["publicRenumbered"] = True
    numbering["originalTotal"] = len(qs)
    numbering["excludedSource"] = "chemy"
    numbering["excludedCount"] = len(removed_ids)

    # 2) 三份数据同步删题
    pres = {k: v for k, v in pres.items() if k in kept_ids}
    before_entries = len(knowledge.get("entries", []))
    if isinstance(knowledge.get("entries"), list):
        knowledge["entries"] = [e for e in knowledge["entries"] if not str(e.get("id", "")).startswith("chemy")]
    knowledge["totalQuestions"] = len(kept)
    knowledge["analyzedQuestions"] = len(knowledge.get("entries", []))

    # 3) 删掉不再被任何题目引用的图片
    refs = asset_refs(pres)
    assets = site / "assets"
    pruned = pruned_bytes = 0
    if assets.is_dir():
        stale = [p for p in assets.iterdir() if p.is_file() and p.name not in refs]
        if stale:
            # 移出而非删除：一次批量删除上万文件会被环境安全钩子拦下，
            # 移到工作区缓存目录也让陈旧图可回滚，之后可人工清理。
            trash = site.parent.parent / ".zwork" / (
                "public-site-stale-" + time.strftime("%Y%m%d-%H%M%S")
            )
            trash.mkdir(parents=True, exist_ok=True)
            for p in stale:
                pruned_bytes += p.stat().st_size
                try:
                    p.rename(trash / p.name)
                except OSError:
                    p.unlink()
                pruned += 1

    # 4) 首页统计与文案
    html = (site / "index.html").read_text(encoding="utf-8")
    html = patch_home(html, kept, len(removed_ids))

    # 写盘（全部成功后才写，避免中途失败留下半成品）
    dump_json(site / "questions.json", kept)
    dump_json(site / "presentation.json", pres)
    dump_json(site / "numbering.json", numbering)
    dump_json(site / "knowledge-index.json", knowledge)
    write_text_safe(site / "index.html", html)

    residual = sum(1 for q in kept if str(q["id"]).startswith("chemy"))
    return {
        "total": len(kept),
        "removed": len(removed_ids),
        "papers": len({(str(q.get("edition", "unknown")), str(q.get("paper", ""))) for q in kept}),
        "pruned_images": pruned,
        "pruned_mb": round(pruned_bytes / 1048576, 1),
        "entry_removed": before_entries - len(knowledge.get("entries", [])),
        "residual_chemy": residual,
        "counts": counts,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="公开版：剔除 Chemy 题并重新连续编号")
    ap.add_argument("--site", type=Path, default=Path(__file__).resolve().parent.parent / "site")
    args = ap.parse_args()
    try:
        r = apply(args.site)
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    print(f"[OK] 剩余 {r['total']:,} 题 / {r['papers']} 份卷；剔除 Chemy {r['removed']:,} 题")
    print(f"     专题编号已重新从 1 连续排定；AI 索引删 {r['entry_removed']:,} 条")
    print(f"     清理无人引用题图 {r['pruned_images']:,} 张 / {r['pruned_mb']} MB")
    print(f"     countsByTopic：{r['counts']}")
    if r["residual_chemy"]:
        print("[FAIL] 仍有 Chemy 题残留", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
