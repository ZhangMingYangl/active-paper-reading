#!/usr/bin/env python3
"""把主动阅读母版安装到 Obsidian 知识库，并开启 Obsidian 的“模板”核心插件。

用法：
    python setup.py --vault "D:/Obsidian/我的知识库"
    python setup.py --vault ~/Documents/MyVault --folder 论文阅读 --dry-run

做了什么：
1. 把 templates/ docs/ prompts/ examples/ 复制到 <知识库>/<folder>/ 下（已有同名文件不覆盖，除非加 --force）；
2. 在 .obsidian/core-plugins.json 里开启“模板”插件；
3. 如果知识库还没设置模板文件夹，就设为 <folder>/templates；
   如果已经设置了别的模板文件夹，不改设置，而是把母版额外复制一份到那个文件夹。
修改前会把原配置备份为 *.bak。只用 Python 标准库。
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
PARTS = ["templates", "docs", "prompts", "examples"]
TEMPLATE_NAME = "论文阅读-主动思考模板.md"


def log(msg):
    print(msg, flush=True)


def copy_tree(src, dst, force, dry):
    copied = skipped = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        target = dst / f.relative_to(src)
        if target.exists() and not force:
            skipped += 1
            continue
        if not dry:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
        copied += 1
    return copied, skipped


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8") or "null") or default
    except json.JSONDecodeError:
        sys.exit(f"无法解析 {path}，为避免损坏配置已停止。请手动开启模板插件。")


def save_json(path, data, dry):
    if dry:
        return
    if path.exists():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def enable_templates_plugin(obsidian, dry):
    path = obsidian / "core-plugins.json"
    data = load_json(path, [])
    if isinstance(data, list):  # 新版 Obsidian：已开启插件的列表
        if "templates" in data:
            return "模板插件原本已开启"
        data.append("templates")
    elif isinstance(data, dict):  # 旧版 Obsidian：{插件名: true/false}
        if data.get("templates") is True:
            return "模板插件原本已开启"
        data["templates"] = True
    else:
        sys.exit(f"{path} 的格式无法识别，已停止。请手动开启模板插件。")
    save_json(path, data, dry)
    return "已开启模板插件"


def set_template_folder(obsidian, vault, folder, dry, force):
    path = obsidian / "templates.json"
    data = load_json(path, {})
    if not isinstance(data, dict):
        sys.exit(f"{path} 的格式无法识别，已停止。")
    wanted = f"{folder}/templates"
    current = (data.get("folder") or "").strip("/")
    if not current:
        data["folder"] = wanted
        save_json(path, data, dry)
        return f"模板文件夹已设为 {wanted}"
    if current == wanted:
        return f"模板文件夹原本就是 {wanted}"
    target = vault / current / TEMPLATE_NAME
    if target.exists() and not force:
        return f"你已有模板文件夹 {current}，里面已有同名母版，未覆盖"
    if not dry:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / "templates" / TEMPLATE_NAME, target)
    return f"你已有模板文件夹 {current}，没有改设置，已把母版复制进去"


def main():
    ap = argparse.ArgumentParser(description="安装主动阅读母版到 Obsidian 知识库")
    ap.add_argument("--vault", required=True, help="Obsidian 知识库根目录（里面有 .obsidian 文件夹）")
    ap.add_argument("--folder", default="论文阅读", help="安装到知识库里的哪个文件夹，默认“论文阅读”")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的同名文件")
    ap.add_argument("--dry-run", action="store_true", help="只显示会做什么，不真正修改")
    a = ap.parse_args()

    vault = Path(a.vault).expanduser().resolve()
    obsidian = vault / ".obsidian"
    if not obsidian.is_dir():
        sys.exit(f"{vault} 里没有 .obsidian 文件夹。请确认这是 Obsidian 知识库的根目录，并且至少用 Obsidian 打开过一次。")
    folder = a.folder.replace("\\", "/").strip("/")
    dest = vault / folder
    prefix = "[预演] " if a.dry_run else ""

    total_c = total_s = 0
    if dest.resolve() == REPO:  # 项目本身就放在知识库的这个位置，不用再复制
        log(f"{prefix}项目已在 {dest}，跳过复制")
        PARTS.clear()
    for part in PARTS:
        c, s = copy_tree(REPO / part, dest / part, a.force, a.dry_run)
        total_c += c
        total_s += s
    log(f"{prefix}复制 {total_c} 个文件到 {dest}" + (f"，跳过 {total_s} 个已存在的文件" if total_s else ""))
    log(prefix + enable_templates_plugin(obsidian, a.dry_run))
    log(prefix + set_template_folder(obsidian, vault, folder, a.dry_run, a.force))
    log("")
    log("完成。如果插入模板时找不到母版，请完全关闭并重新打开 Obsidian。")
    log(f"然后新建一篇笔记，按 Ctrl/Cmd+P，输入“模板”，选“插入模板 → {TEMPLATE_NAME[:-3]}”。")
    log(f"第一次用请先读：{folder}/docs/01-新手操作教程.md")


if __name__ == "__main__":
    main()
