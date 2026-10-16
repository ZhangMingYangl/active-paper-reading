#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 ZhangMingYangl
"""把主动阅读母版安装到 Obsidian 知识库，并开启 Obsidian 的“模板”核心插件。

用法：
    python setup.py --vault "D:/Obsidian/我的知识库"
    python setup.py --vault ~/Documents/MyVault --folder 论文阅读 --dry-run
    python setup.py --vault "D:/Obsidian/我的知识库" --update      # 更新到新版

做了什么：
1. 把 templates/ docs/ prompts/ examples/ 复制到 <知识库>/<folder>/ 下（已有同名文件不覆盖，除非加 --force）；
2. 在 .obsidian/core-plugins.json 里开启“模板”插件；
3. 如果知识库还没设置模板文件夹，就设为 <folder>/templates；
   如果已经设置了别的模板文件夹，不改设置，而是把母版额外复制一份到那个文件夹。
修改前会把原配置备份为 *.bak。只用 Python 标准库。

更新（--update）：用户没改过的文件直接换成新版；改过的先备份到 <folder>/备份/<时间>/ 再换新版。
已经写好的论文笔记不受影响。安装记录保存在 <folder>/.apr-install.json。
"""
import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
PARTS = ["templates", "docs", "prompts", "examples"]
TEMPLATE_NAME = "论文阅读-主动思考模板.md"
MANIFEST = ".apr-install.json"
VERSION = (REPO / "VERSION").read_text(encoding="utf-8").strip() if (REPO / "VERSION").exists() else "未知"


def log(msg):
    print(msg, flush=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files():
    """仓库里要装进知识库的文件：(来源路径, 相对安装目录的路径)。"""
    for part in PARTS:
        for f in sorted((REPO / part).rglob("*")):
            if f.is_file():
                yield f, f.relative_to(REPO).as_posix()


def copy_tree(dest, force, dry, installed):
    copied = skipped = 0
    for f, rel in source_files():
        target = dest / rel
        if target.exists() and not force:
            skipped += 1
            continue
        if not dry:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
        installed[rel] = digest(f)
        copied += 1
    return copied, skipped


def read_manifest(dest):
    path = dest / MANIFEST
    if not path.exists():
        return {"files": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"files": {}}


def write_manifest(dest, files, extra_template, dry):
    if dry:
        return
    data = {"version": VERSION, "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "files": files, "extra_template": extra_template}
    (dest / MANIFEST).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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
    EXTRA["path"] = f"{current}/{TEMPLATE_NAME}"
    EXTRA["hash"] = digest(REPO / "templates" / TEMPLATE_NAME)
    return f"你已有模板文件夹 {current}，没有改设置，已把母版复制进去"


EXTRA = {}  # 母版额外复制到用户已有模板文件夹时，记下位置，更新时一起更新


def update_one(src, target, recorded, backup_dir, label, dry):
    """更新一个文件，返回结果说明；用户改过的先备份。"""
    new_hash = digest(src)
    if not target.exists():
        if not dry:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
        return "new", None
    old_hash = digest(target)
    if old_hash == new_hash:
        return "same", None
    backup = None
    if old_hash != recorded:  # 不是当初装进去的样子，说明用户改过，先备份
        backup = backup_dir / f"{target.stem}（{label}前我的版本）{target.suffix}"
        if not dry:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
    if not dry:
        shutil.copy2(src, target)
    return "updated", backup


def update(vault, dest, folder, dry):
    prefix = "[预演] " if dry else ""
    if not dest.is_dir():
        sys.exit(f"没有找到 {dest}。请用 --folder 指定当初安装的文件夹。")
    manifest = read_manifest(dest)
    recorded = manifest.get("files", {})
    log(f"{prefix}当前安装版本：{manifest.get('version', '未记录（旧版安装）')}，新版本：{VERSION}")
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    backup_dir = dest / "备份" / stamp
    counts = {"new": 0, "same": 0, "updated": 0}
    backups = []
    files = {}
    for f, rel in source_files():
        result, backup = update_one(f, dest / rel, recorded.get(rel), backup_dir, "更新", dry)
        counts[result] += 1
        files[rel] = digest(f)
        if backup:
            backups.append((rel, backup))
    extra = manifest.get("extra_template") or {}
    if extra.get("path"):
        target = vault / extra["path"]
        if target.exists():
            result, backup = update_one(REPO / "templates" / TEMPLATE_NAME, target, extra.get("hash"), backup_dir, "更新", dry)
            counts[result] += 1
            if backup:
                backups.append((extra["path"], backup))
        extra = {"path": extra["path"], "hash": digest(REPO / "templates" / TEMPLATE_NAME)}
    write_manifest(dest, files, extra, dry)
    log(f"{prefix}换成新版 {counts['updated']} 个，新增 {counts['new']} 个，本来就是最新的 {counts['same']} 个")
    if backups:
        log(f"{prefix}其中 {len(backups)} 个你改过，旧内容已备份到 {backup_dir.relative_to(vault)}：")
        for rel, _ in backups:
            log(f"  - {rel}")
    log("已经写好的论文笔记不受影响，没有改动。")
    log("")
    if dry:
        log("预演结束，没有修改任何文件。确认无误后，去掉 --dry-run 再运行一次即可正式更新。")
    else:
        log(f"更新完成，现在是 v{VERSION}。改了什么见 CHANGELOG.md。")


def find_existing(vault, dest):
    """在知识库里找已有的同名母版（不算本次的安装位置），找到就返回路径。"""
    skip = {".obsidian", ".git", ".trash"}
    for path in vault.rglob(TEMPLATE_NAME):
        rel = path.relative_to(vault).parts
        if rel[0] in skip:
            continue
        if path.resolve() == (dest / "templates" / TEMPLATE_NAME).resolve():
            continue
        return path
    return None


def main():
    ap = argparse.ArgumentParser(description="安装主动阅读母版到 Obsidian 知识库")
    ap.add_argument("--vault", required=True, help="Obsidian 知识库根目录（里面有 .obsidian 文件夹）")
    ap.add_argument("--folder", default="论文阅读", help="安装到知识库里的哪个文件夹，默认“论文阅读”")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的同名文件")
    ap.add_argument("--dry-run", action="store_true", help="只显示会做什么，不真正修改")
    ap.add_argument("--update", action="store_true", help="更新已安装的母版和说明到新版，改过的文件先备份")
    a = ap.parse_args()

    vault = Path(a.vault).expanduser().resolve()
    obsidian = vault / ".obsidian"
    if not obsidian.is_dir():
        sys.exit(f"{vault} 里没有 .obsidian 文件夹。请确认这是 Obsidian 知识库的根目录，并且至少用 Obsidian 打开过一次。")
    folder = a.folder.replace("\\", "/").strip("/")
    dest = vault / folder
    prefix = "[预演] " if a.dry_run else ""

    if a.update:
        update(vault, dest, folder, a.dry_run)
        return

    if not a.force:
        existing = find_existing(vault, dest)
        if existing:
            log(f"知识库里已经有母版：{existing.relative_to(vault)}")
            log("看起来之前装过了，为避免出现两个同名文件，这次什么都没改。")
            log("新建笔记时直接插入这个母版就行；要更新到新版请加 --update；确实要再装一份，请加 --force。")
            return

    installed = {}
    if dest.resolve() == REPO:  # 项目本身就放在知识库的这个位置，不用再复制
        log(f"{prefix}项目已在 {dest}，跳过复制")
    else:
        c, s = copy_tree(dest, a.force, a.dry_run, installed)
        log(f"{prefix}复制 {c} 个文件到 {dest}" + (f"，跳过 {s} 个已存在的文件" if s else ""))
    log(prefix + enable_templates_plugin(obsidian, a.dry_run))
    log(prefix + set_template_folder(obsidian, vault, folder, a.dry_run, a.force))
    if dest.resolve() != REPO:
        write_manifest(dest, installed, dict(EXTRA), a.dry_run)
    log("")
    if a.dry_run:
        log("预演结束，没有修改任何文件。确认无误后，去掉 --dry-run 再运行一次即可正式安装。")
        return
    log(f"完成，安装的是 v{VERSION}。如果插入模板时找不到母版，请完全关闭并重新打开 Obsidian。")
    log(f"然后新建一篇笔记，按 Ctrl/Cmd+P，输入“模板”，选“插入模板 → {TEMPLATE_NAME[:-3]}”。")
    log(f"第一次用请先读：{folder}/docs/01-新手操作教程.md")


if __name__ == "__main__":
    main()
