#!/usr/bin/env python3
"""从内部工作区 dist/ 一步生成公开库 public-site/site/（可重复运行、不动源数据）。

唯一入口：改完内部 dist/ 后跑本脚本即可，不再需要任何中间仓库。

公开版相对内部完整版做的六件事：
  1. 白名单复制：审核台文件、sources 链接、打印册 downloads/、裁页索引
     export-index/、pdf-worker.js 与 pdf-lib 一律不带出；
     单题 / 选题库 PDF 改为浏览器打印视图（window.print → 另存为 PDF），零额外体积；
  2. 隐藏专题册直链与 AI 组卷的旧 PDF 按钮，保留单题下载、选题库与打印入口；
  3. 剥离 questions.json 的 reviewStatus、percent=0 → null，首页去掉「审核状态」字样；
  4. 只复制被正文引用的题图，并把 JPG 转成 WebP（q=82, method=4），同步改写引用；
  5. 调用 prune_chemy.apply() 剔除 Chemy 来源题、按专题重新连续编号、清理孤儿题图并重算首页统计；
  6. 让发布目录降到 1 GB 以下，满足 GitHub Pages 的硬限制。

内部 dist/ 一个字节都不改；重复运行会重建 public-site/site/。
转换结果缓存在工作区内部缓存目录，重跑无需重新编码。

用法（在 public-site/ 下）::

    python tools/build_public_site.py --dry-run
    python tools/build_public_site.py
    python tools/build_public_site.py --quality 85 --workers 8

依赖：Pillow>=11,<13（仅本脚本需要；看板本身零依赖）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
DEFAULT_SOURCE = REPO.parent / "dist"   # 内部工作台的看板源文件
DEFAULT_OUT = REPO                     # 本公开库根目录
CACHE = REPO.parent / ".zwork" / "public-site-webp-cache"

KEEP_FILES = [
    ".nojekyll", "ai-config.json", "ai-paper.css", "ai-paper.js", "app.js",
    "favicon.svg", "index.html", "interface.css", "knowledge-index.json",
    "numbering.json", "paper-engine.js", "presentation.json", "questions.json",
    "styles.css",
]
KEEP_DIRS = ["assets", "vendor"]
# vendor 里只保留 KaTeX；pdf-lib 仅供 pdf-worker 使用
SKIP_VENDOR_FILES = {"pdf-lib.min.js", "pdf-lib-LICENSE.md"}

HIDE_CSS = """

/* 公开在线阅读版：只隐藏依赖打印册的旧入口（单题 / 选题库下载照常开放） */
#downloads,
[data-ai-export] { display: none !important; }
"""

PUBLIC_NOTICE = """# NOTICE · 来源与版权说明

本站点是个人整理的化学竞赛题目**在线阅读版**，题目与参考答案来自公开渠道的网络资源，版权归各原命题组及相应权利人所有。本站不主张题目内容的著作权，也不用于任何商业用途。

- 若权利人认为内容不宜公开，请通过仓库 Issue 联系，核实后立即移除。
- 本仓库中由维护者编写的**前端代码、样式与整理脚本**采用 MIT 许可（见 `LICENSE`）；题目与答案内容**不在该许可范围内**。
- **本在线阅读版不含 Chemy 系列题目**：为尊重上游整理项目的授权范围，`id` 以 `chemy` 开头的 1933 道题已整体剔除（完整版仅保存在维护者的本地工作台，不对外提供）。
- 剔除后各专题的编号按本版剩余题目重新从 1 连续排定，与内部完整版的题号并不一致；每道题仍保留原卷题号与出处，便于回查。

## 第三方组件

| 组件 | 许可 | 文件 |
| --- | --- | --- |
| KaTeX 0.16.22 | MIT | `site/vendor/katex/LICENSE` |

站点无外部 CDN、无统计脚本、无后端服务；所有字体、脚本与图片均在仓库内。
"""

JPG_REF_RE = re.compile(r"assets/([A-Za-z0-9_\-\.%#\u4e00-\u9fff]+?\.jpg)", re.I)


def write_text_safe(path: Path, text: str) -> None:
    """Windows 上新建的大目录偶尔被索引/杀毒短暂锁定，重试并先清只读位。"""
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


def patch_index(html: str, total: int) -> tuple[str, list[str]]:
    notes = []
    html, n = re.subn(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{total} 道化学竞赛题目，按八个专题、届次与来源机构查找，搜索题干关键词，查看参考答案，单题或选题库导出 PDF；纯静态、离线可用的在线阅读版。">',
        html,
    )
    notes.append(f"meta description 改为在线阅读版（{n} 处）")

    html, n = re.subn(
        r"<p>题目与参考答案来自公开渠道.*?</p>",
        "<p>题目与参考答案来自公开渠道的网络资源，版权归各原命题组及相应权利人所有；"
        "本站仅供学习交流，不用于任何形式的商业用途。来源、致谢与第三方组件许可见 "
        '<a href="NOTICE.md">NOTICE.md</a>；如涉及侵权请联系移除。</p>',
        html, flags=re.S, count=1,
    )
    notes.append(f"首页版权段改为公开版口径（{n} 处）")

    # 源 index.html 已改为「单题 / 选题库（打印另存）」口径，公开版原样沿用，不再替换。
    html, n = re.subn(
        r"版权归原命题组所有，仅供学术交流使用，请勿用于任何形式的商业用途。",
        "版权归原命题组及相应权利人所有；本站仅作学习交流整理，如涉及侵权请联系移除。",
        html,
    )
    notes.append(f"页脚版权行改写（{n} 处）")

    if "原题号与审核状态" in html:
        html = html.replace("（机构、卷名、原题号与审核状态）", "（机构、卷名与原卷题号）")
        notes.append("去掉「审核状态」字样（内部标记不公开）")
    return html, notes


def convert_one(src: Path, dst: Path, quality: int) -> tuple[str, int, int]:
    """JPG → WebP；返回 (状态, 原字节, 新字节)。带缓存，失败原样复制 JPG。"""
    cached = CACHE / (src.stem + ".webp")
    old_size = src.stat().st_size
    try:
        if not (cached.is_file() and cached.stat().st_size > 0):
            from PIL import Image
            tmp = dst.with_suffix(".tmpwebp")
            im = Image.open(src).convert("RGB")
            im.save(tmp, "WEBP", quality=quality, method=4)
            im.close()
            CACHE.mkdir(parents=True, exist_ok=True)
            tmp.replace(cached)
        shutil.copy2(cached, dst)
        return "webp", old_size, dst.stat().st_size
    except Exception as exc:  # 单张失败不影响整体
        shutil.copy2(src, dst.parent / src.name)
        return f"kept-jpg:{type(exc).__name__}", old_size, old_size


def main() -> int:
    ap = argparse.ArgumentParser(description="生成公开版看板 public-site/")
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--quality", type=int, default=82, help="WebP 质量，默认 82")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-images", action="store_true", help="只处理文本与结构，调试用")
    args = ap.parse_args()

    src: Path = args.source.resolve()
    out: Path = args.out.resolve()
    site = out / "site"
    if not src.is_dir():
        print(f"[FAIL] 源目录不存在：{src.name}", file=sys.stderr)
        return 1
    missing = [f for f in KEEP_FILES if not (src / f).is_file()]
    if missing:
        print(f"[FAIL] 源目录缺文件：{missing}", file=sys.stderr)
        return 1

    questions = json.loads((src / "questions.json").read_text(encoding="utf-8"))
    total = len(questions)
    print(f"源：{src.name}；目标：{out.name}/site；题目 {total} 道；WebP q={args.quality}")
    print(f"模式：{'DRY-RUN' if args.dry_run else 'APPLY'}，{args.workers} 线程")

    if not args.dry_run:
        out.mkdir(parents=True, exist_ok=True)
        # 原地覆盖重建（不整目录删除）：只写本次需要的文件，
        # 末尾由 prune_chemy 把陈旧文件移出，避免一次批量删除上万文件。
        site.mkdir(parents=True, exist_ok=True)
        print("  · 原地覆盖重建（不清空旧目录）")

    # 1) 顶层文件
    for name in KEEP_FILES:
        s = src / name
        if args.dry_run:
            continue
        if name == "index.html":
            patched, notes = patch_index(s.read_text(encoding="utf-8"), total)
            write_text_safe(site / name, patched)
            for note in notes:
                print(f"  · index.html：{note}")
        elif name == "styles.css":
            css = s.read_text(encoding="utf-8")
            if "公开在线阅读版" not in css:
                css += HIDE_CSS
            write_text_safe(site / name, css)
            print("  · styles.css：仅隐藏专题册直链与 AI 组卷旧 PDF 按钮，单题/选题库保持可见")
        elif name == "questions.json":
            qs = json.loads(s.read_text(encoding="utf-8"))
            stripped = zeros = 0
            for q in qs:
                if "reviewStatus" in q:
                    q.pop("reviewStatus", None)
                    stripped += 1
                if q.get("percent") == 0:
                    q["percent"] = None
                    zeros += 1
            write_text_safe(site / name, json.dumps(qs, ensure_ascii=False, separators=(",", ":")))
            print(f"  · questions.json：剥离 reviewStatus {stripped:,} 题，percent=0 → null {zeros:,} 题")
        elif name == "presentation.json":
            (site / name).write_bytes(s.read_bytes())  # 稍后按映射改写
        else:
            shutil.copy2(s, site / name)

    # 2) vendor（排除 pdf-lib）
    if not args.dry_run:
        (site / "vendor").mkdir(parents=True, exist_ok=True)
    vendor_files = 0
    for p in sorted((src / "vendor").rglob("*")):
        if p.is_symlink() or not p.is_file():
            continue
        if p.name in SKIP_VENDOR_FILES:
            continue
        vendor_files += 1
        if not args.dry_run:
            target = site / "vendor" / p.relative_to(src / "vendor")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
    print(f"  · vendor/：{vendor_files} 文件（已排除 pdf-lib）")

    # 3) assets：原有 webp 直接复制；jpg 转 webp
    assets_src = src / "assets"
    assets_dst = site / "assets"
    if not args.dry_run:
        assets_dst.mkdir(parents=True, exist_ok=True)
    # 只取「公开版保留题目」引用的题图：既等价于原先中转层的 --prune-orphans，
    # 也避免把待剔除 Chemy 题的图先搬进来再删（更快，且几乎零删除）。
    pres_all = json.loads((src / "presentation.json").read_text(encoding="utf-8"))
    pres_kept = {k: v for k, v in pres_all.items() if not str(k).startswith("chemy")}
    pres_refs = set(
        m.group(1) for m in re.finditer(
            r"assets/([A-Za-z0-9_\-\.%#\u4e00-\u9fff]+?\.(?:jpg|jpeg|png|webp|svg|gif))",
            json.dumps(pres_kept, ensure_ascii=False), re.I,
        )
    )
    jpgs = sorted(p for p in assets_src.iterdir()
                  if p.suffix.lower() == ".jpg" and p.name in pres_refs)
    webps = sorted(p for p in assets_src.iterdir()
                   if p.suffix.lower() == ".webp" and p.name in pres_refs)
    other = [p for p in assets_src.iterdir()
             if p.is_file() and p.suffix.lower() not in {".jpg", ".webp"}
             and p.name in pres_refs]
    print(f"  · 只取保留题目引用的 {len(pres_refs):,} 张题图"
          f"（剔除 {len(pres_all) - len(pres_kept):,} 道 Chemy 题，跳过孤儿图）")
    print(f"  · assets/：{len(jpgs):,} 张 JPG 待转、{len(webps):,} 张 WebP 直拷、{len(other)} 张其它")

    mapping: dict[str, str] = {}
    failures: list[str] = []
    old_total = new_total = 0
    if not args.dry_run and not args.skip_images:
        for p in webps + other:
            shutil.copy2(p, assets_dst / p.name)
        tasks = []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for p in jpgs:
                target = assets_dst / (p.stem + ".webp")
                tasks.append((p, target, pool.submit(convert_one, p, target, args.quality)))
            done = 0
            for p, target, fut in tasks:
                status, ob, nb = fut.result()
                old_total += ob
                new_total += nb
                if status == "webp":
                    mapping[p.name] = target.name
                else:
                    failures.append(f"{p.name} ({status})")
                done += 1
                if done % 4000 == 0:
                    print(f"    转换进度 {done:,}/{len(jpgs):,}")
    elif args.dry_run:
        for p in jpgs:
            mapping[p.name] = p.stem + ".webp"

    print(f"  · 图片：JPG {old_total/1048576:.1f} MB → WebP {new_total/1048576:.1f} MB"
          f"（{new_total/old_total*100:.1f}%）" if old_total else "  · 图片：跳过")
    if failures:
        print(f"  ⚠ {len(failures)} 张转换失败，已保留原 JPG：{failures[:3]}")

    # 4) 按映射一次性改写 presentation.json 的引用
    if mapping and not args.dry_run:
        pres = site / "presentation.json"
        text = pres.read_text(encoding="utf-8")
        def repl(m):
            old = m.group(1)
            return "assets/" + mapping.get(old, old)
        text, n = JPG_REF_RE.subn(repl, text)
        write_text_safe(pres, text)
        print(f"  · presentation.json：改写 {n:,} 处图片引用（{len(mapping):,} 个映射）")

    # 5) 站点内 NOTICE
    if not args.dry_run:
        write_text_safe(site / "NOTICE.md", PUBLIC_NOTICE)

    # 6) 数据层变换：剔除 Chemy 题、按专题重新连续编号、清图、重算首页
    if not args.dry_run:
        from prune_chemy import apply as prune_apply
        stats = prune_apply(site)
        print(f"  · 数据层：剔除 Chemy {stats['removed']:,} 题 → 剩 {stats['total']:,} 题 / {stats['papers']} 份卷")
        print(f"  · 编号：按专题重新从 1 连续排定；AI 索引删 {stats['entry_removed']:,} 条")
        print(f"  · 题图：清理无人引用 {stats['pruned_images']:,} 张 / {stats['pruned_mb']} MB")
        if stats["residual_chemy"]:
            print("[FAIL] 仍有 Chemy 题残留", file=sys.stderr)
            return 1

    n_files = n_bytes = 0
    if not args.dry_run:
        for p in site.rglob("*"):
            if p.is_file() and not p.is_symlink():
                n_files += 1
                n_bytes += p.stat().st_size
        print(f"\n[OK] public-site/site/：{n_files:,} 文件 / {n_bytes/1048576:.1f} MB "
              f"({n_bytes/1073741824:.2f} GB)")
        print("源：内部工作区 dist/（直连，无中间仓库）")
        print("已排除：审核台 5 件、sources 链接、downloads/、export-index/、pdf-worker.js、pdf-lib")
        print("已开放：单题 PDF、选题库（1-10 题合成打印 PDF，题号用专题编号）")
        print("下一步：cd <public-site 目录> && python tools/validate_public.py")
    else:
        print("\n[DRY-RUN] 未写盘")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
