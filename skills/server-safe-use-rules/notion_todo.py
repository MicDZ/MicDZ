#!/usr/bin/env python3
"""Log or update a todo in the Notion Todos database.

Usage (create):
  python3 notion_todo.py \
      --task "给 MPPI teacher 加动作代价项" \
      --status 待办 --priority P1 --agent Claude --project CloseLoopHOI \
      --type 编码 --type 实验 --due 2026-09-30 --estimate 3 \
      --description "..." --experiment EXP-2026-0927-dagger-v2 --link "https://..." \
      --tags quick-win

Usage (update an existing one — e.g. mark it done):
  python3 notion_todo.py --page-id <uuid> --status 已完成 --done-time 2026-09-29

Only --task (or --page-id) is required. Select options that don't exist yet are
created automatically. Credentials/target come from NOTION_TOKEN and
NOTION_TODO_DATA_SOURCE_ID in the environment.
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
DATA_SOURCE = os.environ.get("NOTION_TODO_DATA_SOURCE_ID", "")

if not TOKEN or not DATA_SOURCE:
    sys.exit("Set NOTION_TOKEN and NOTION_TODO_DATA_SOURCE_ID in the environment first.")


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
    if not s:
        return None
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
    p.add_argument("--task")
    p.add_argument("--page-id", help="update this existing todo instead of creating one")
    p.add_argument("--status"); p.add_argument("--priority"); p.add_argument("--agent")
    p.add_argument("--project"); p.add_argument("--type", action="append")
    p.add_argument("--due"); p.add_argument("--done-time")
    p.add_argument("--estimate", type=float)
    p.add_argument("--description"); p.add_argument("--experiment")
    p.add_argument("--link"); p.add_argument("--tags")
    a = p.parse_args()

    if not a.task and not a.page_id:
        sys.exit("give --task (create) or --page-id (update)")

    props = {}
    if a.task: props["任务"] = {"title": [{"text": {"content": a.task}}]}
    for arg, key in ((a.status, "状态"), (a.priority, "优先级"), (a.agent, "执行 Agent")):
        if arg: props[key] = {"select": {"name": arg}}
    if a.project:
        props["项目"] = {"multi_select": [
            {"name": x.strip()} for x in a.project.split(",") if x.strip()]}
    if a.type:
        props["任务类型"] = {"multi_select": [{"name": x} for x in a.type]}
    if a.tags:
        props["Tags"] = {"multi_select": [
            {"name": t.strip()} for t in a.tags.split(",") if t.strip()]}
    if a.due: props["截止日期"] = {"date": {"start": to_iso(a.due)}}
    if a.done_time: props["完成时间"] = {"date": {"start": to_iso(a.done_time)}}
    if a.estimate is not None: props["预估时长(小时)"] = {"number": a.estimate}
    for arg, key in ((a.description, "描述"), (a.experiment, "关联实验")):
        if arg: props[key] = rt(arg)
    if a.link: props["关联链接"] = {"url": a.link}

    if a.page_id:
        page = api("PATCH", f"/pages/{a.page_id}", {"properties": props})
    else:
        page = api("POST", "/pages", {"parent": {"type": "data_source_id",
                                                 "data_source_id": DATA_SOURCE},
                                      "properties": props})
    print("OK page_id:", page["id"])
    print("url:", page.get("url"))


if __name__ == "__main__":
    main()
