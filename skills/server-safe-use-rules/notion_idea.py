#!/usr/bin/env python3
"""Log a research idea to the Notion Ideas database. Sibling of notion_log.py.

Usage:
  python3 notion_idea.py \
      --name "IDEA-2026-0928-01 视频扩散骨干手物联合前馈" \
      --status 待评估 --priority P0 --source 文献调研 --agent Claude --project HOIEstimation \
      --direction 前馈估计 --direction 视频扩散骨干 \
      --claim "..." --gap "..." --method "..." --data-eval "..." --risk "..." \
      --competitors "..." --assets "..." --venue "CVPR 2027" --compute "8x80GB, 1-2 周" \
      --next "..." --date 2026-09-28 --link "https://..." --tags survey,feedforward

Only --name is required. Select options that don't exist yet are created automatically.
Credentials/target come from NOTION_TOKEN and NOTION_IDEAS_DATA_SOURCE_ID in the environment.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

BASE = "https://api.notion.com/v1"
VERSION = "2026-03-11"
TOKEN = os.environ.get("NOTION_TOKEN", "")
DATA_SOURCE = os.environ.get("NOTION_IDEAS_DATA_SOURCE_ID", "")

if not TOKEN or not DATA_SOURCE:
    sys.exit("Set NOTION_TOKEN and NOTION_IDEAS_DATA_SOURCE_ID in the environment first.")


def api(method, path, body=None):
    req = urllib.request.Request(
        f"{BASE}{path}", data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Notion-Version": VERSION,
                 "Content-Type": "application/json"}, method=method)
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: HTTP {e.code} {e.read().decode()[:500]}")


def to_iso(s):
    s = s.strip()
    if s.isdigit():
        return datetime.datetime.fromtimestamp(int(s) / 1000, datetime.timezone.utc).isoformat()
    if "T" in s:
        return s
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).replace(
                tzinfo=datetime.timezone.utc).isoformat()
        except ValueError:
            pass
    raise SystemExit(f"bad date: {s!r}")


def rt(s):
    return {"rich_text": [{"text": {"content": s[:2000]}}]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--status"); p.add_argument("--priority"); p.add_argument("--source")
    p.add_argument("--agent"); p.add_argument("--project")
    p.add_argument("--direction", action="append")
    p.add_argument("--claim"); p.add_argument("--gap"); p.add_argument("--method")
    p.add_argument("--data-eval"); p.add_argument("--risk"); p.add_argument("--competitors")
    p.add_argument("--assets"); p.add_argument("--venue"); p.add_argument("--compute")
    p.add_argument("--next"); p.add_argument("--date"); p.add_argument("--link")
    p.add_argument("--tags")
    a = p.parse_args()

    props = {"想法名称": {"title": [{"text": {"content": a.name}}]}}
    for arg, key in ((a.status, "状态"), (a.priority, "优先级"),
                     (a.source, "来源"), (a.agent, "提出者")):
        if arg: props[key] = {"select": {"name": arg}}
    if a.direction:
        props["方向"] = {"multi_select": [{"name": x} for x in a.direction]}
    if a.tags:
        props["Tags"] = {"multi_select": [
            {"name": t.strip()} for t in a.tags.split(",") if t.strip()]}
    for arg, key in ((a.project, "项目"), (a.claim, "核心 claim"), (a.gap, "为什么是空白"),
                     (a.method, "方法骨架"), (a.data_eval, "数据与评测"), (a.risk, "风险"),
                     (a.competitors, "竞品/相关工作"), (a.assets, "资产衔接"),
                     (a.venue, "目标会议"), (a.compute, "预估算力"), (a.next, "下一步")):
        if arg: props[key] = rt(arg)
    if a.date: props["提出日期"] = {"date": {"start": to_iso(a.date)}}
    if a.link: props["关联链接"] = {"url": a.link}

    page = api("POST", "/pages", {"parent": {"type": "data_source_id",
                                             "data_source_id": DATA_SOURCE},
                                  "properties": props})
    print("OK page_id:", page["id"])
    print("url:", page.get("url"))


if __name__ == "__main__":
    main()
