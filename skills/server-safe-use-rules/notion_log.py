#!/usr/bin/env python3
"""Log an experiment to the Notion Experiments database. One command, no curl juggling.

Usage:
  python3 notion_log.py \
      --name EXP-2026-0927-lr2e4 --status 成功 --agent Claude \
      --verdict 得出结论 --nature 调参实验 --project CloseLoopHOI \
      --start "2026-09-26 09:12" --end "2026-09-26 15:48" --hours 6.6 \
      --device-model "RTX 6000 Ada" --device-count 2 --device-hours 6.6 --device-mem 41.2 \
      --dataset GSM8K --dataset-path /mnt/nas/SharedDatasets/gsm8k/ \
      --metric gsm8k_acc --metric-value 0.612 --baseline 0.594 --delta 0.018 \
      --hypothesis "..." --method "..." --metrics-json '{"acc":0.612}' \
      --summary "..." --conclusion "..." --code-path ... --log-path ... \
      --env "MBZUAI H200 x1" --tags baseline,hyperparam --link "https://..." \
      --attach curve.png --attach demo.mp4 --page "/path/to/detail.md"

Everything is optional except --name. Times accept "YYYY-MM-DD HH:MM" (UTC) or ISO 8601.
Single/multi-select: pass the real value; if it is not an existing option, the script
creates it. Compute-device fields work for CPUs too (e.g. --device-model "CPU (AMD)").

--page optionally writes a markdown body onto the row's own page (experiment design,
how to reproduce, results and analysis). Use it for experiments that made progress.
"""
import argparse
import datetime
import json
import mimetypes
import os
import sys
import urllib.request

BASE = "https://api.notion.com/v1"
VERSION = "2026-03-11"

# Credentials and target come from the environment.
TOKEN = os.environ.get("NOTION_TOKEN", "")
DATA_SOURCE = os.environ.get("NOTION_DATA_SOURCE_ID", "")

if not TOKEN or not DATA_SOURCE:
    sys.exit("Set NOTION_TOKEN and NOTION_DATA_SOURCE_ID in the environment first.")


def api(method, path, body=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Authorization": f"Bearer {TOKEN}", "Notion-Version": VERSION,
                 "Content-Type": ctype},
        method=method)
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: HTTP {e.code} {e.read().decode()[:500]}")


def to_iso(s):
    if s is None:
        return None
    s = s.strip()
    if s.isdigit():  # epoch ms
        return datetime.datetime.fromtimestamp(int(s) / 1000, datetime.timezone.utc).isoformat()
    if "T" in s:  # already ISO
        return s
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).replace(
                tzinfo=datetime.timezone.utc).isoformat()
        except ValueError:
            pass
    raise SystemExit(f"bad time: {s!r} (use 'YYYY-MM-DD HH:MM' UTC, ISO 8601, or epoch ms)")


def rt(s):
    return {"rich_text": [{"text": {"content": s[:2000]}}]}


def upload(path):
    fn = os.path.basename(path)
    if not os.path.exists(path):
        raise SystemExit(f"attachment not found: {path}")
    if os.path.getsize(path) > 20 * 1024 * 1024:
        sys.exit(f"{fn} is larger than 20 MB; Notion needs a multi-part upload for this.")
    ct = mimetypes.guess_type(fn)[0] or "application/octet-stream"
    up = api("POST", "/file_uploads", {"filename": fn, "content_type": ct})
    uid = up["id"]
    boundary = "----notionlogboundary"
    raw = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
           f"filename=\"{fn}\"\r\nContent-Type: {ct}\r\n\r\n").encode() + \
          open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
    res = api("POST", f"/file_uploads/{uid}/send", raw=raw,
              ctype=f"multipart/form-data; boundary={boundary}")
    if res.get("status") != "uploaded":
        raise RuntimeError(f"upload not completed for {fn}: {res.get('status')}")
    return uid


def md_to_blocks(md):
    """Convert simple markdown into Notion block objects."""
    if md.startswith("@"):
        md = open(md[1:]).read()
    children = []
    for line in md.splitlines():
        t = line.rstrip()
        if not t:
            continue
        if t.startswith("### "):
            children.append({"object": "block", "type": "heading_3",
                             "heading_3": {"rich_text": [{"text": {"content": t[4:]}}]}})
        elif t.startswith("## "):
            children.append({"object": "block", "type": "heading_2",
                             "heading_2": {"rich_text": [{"text": {"content": t[3:]}}]}})
        elif t.startswith("# "):
            children.append({"object": "block", "type": "heading_1",
                             "heading_1": {"rich_text": [{"text": {"content": t[2:]}}]}})
        elif t.startswith("- "):
            children.append({"object": "block", "type": "bulleted_list_item",
                             "bulleted_list_item": {"rich_text": [{"text": {"content": t[2:]}}]}})
        else:
            children.append({"object": "block", "type": "paragraph",
                             "paragraph": {"rich_text": [{"text": {"content": t}}]}})
    return children


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--status"); p.add_argument("--agent"); p.add_argument("--verdict")
    p.add_argument("--nature", action="append"); p.add_argument("--project")
    p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--hours", type=float)
    p.add_argument("--device-model"); p.add_argument("--device-count", type=float)
    p.add_argument("--device-hours", type=float); p.add_argument("--device-mem", type=float)
    p.add_argument("--dataset"); p.add_argument("--dataset-path")
    p.add_argument("--metric"); p.add_argument("--metric-value", type=float)
    p.add_argument("--baseline", type=float); p.add_argument("--delta", type=float)
    p.add_argument("--hypothesis"); p.add_argument("--method"); p.add_argument("--metrics-json")
    p.add_argument("--summary"); p.add_argument("--conclusion")
    p.add_argument("--code-path"); p.add_argument("--log-path"); p.add_argument("--env")
    p.add_argument("--tags"); p.add_argument("--link")
    p.add_argument("--attach", action="append"); p.add_argument("--page")
    a = p.parse_args()

    props = {"实验名称": {"title": [{"text": {"content": a.name}}]}}
    if a.status: props["状态"] = {"select": {"name": a.status}}
    if a.agent: props["执行 Agent"] = {"select": {"name": a.agent}}
    if a.verdict: props["简明结论"] = {"select": {"name": a.verdict}}
    if a.device_model: props["计算设备型号"] = {"select": {"name": a.device_model}}
    if a.nature: props["实验性质"] = {"multi_select": [{"name": x} for x in a.nature]}
    if a.tags:
        props["Tags"] = {"multi_select": [
            {"name": t.strip()} for t in a.tags.split(",") if t.strip()]}
    for arg, key in ((a.project, "项目"), (a.dataset, "数据集"), (a.dataset_path, "数据集路径"),
                     (a.hypothesis, "假设与目标"), (a.method, "方法与改动"),
                     (a.metrics_json, "指标(JSON)"), (a.summary, "结果摘要"),
                     (a.conclusion, "结论与后续"), (a.code_path, "代码/配置路径"),
                     (a.log_path, "日志/产物路径"), (a.env, "运行环境"), (a.metric, "主指标名称")):
        if arg: props[key] = rt(arg)
    for arg, key in ((a.hours, "时长(小时)"), (a.device_count, "计算设备数量"),
                     (a.device_hours, "计算设备时长"), (a.device_mem, "计算设备显存(GB)"),
                     (a.metric_value, "主指标值"), (a.baseline, "基线值"), (a.delta, "提升")):
        if arg is not None: props[key] = {"number": arg}
    if a.start: props["开始时间"] = {"date": {"start": to_iso(a.start)}}
    if a.end: props["结束时间"] = {"date": {"start": to_iso(a.end)}}
    if a.link: props["关联链接"] = {"url": a.link}
    if a.attach:
        props["可视化结果"] = {"files": [
            {"type": "file_upload", "file_upload": {"id": upload(x)},
             "name": os.path.basename(x)} for x in a.attach]}

    page = api("POST", "/pages", {"parent": {"type": "data_source_id",
                                             "data_source_id": DATA_SOURCE},
                                  "properties": props})
    pid, url = page["id"], page.get("url")
    print("OK page_id:", pid)
    print("url:", url)

    if a.page:
        blocks = md_to_blocks(a.page)
        for i in range(0, len(blocks), 100):
            api("PATCH", f"/blocks/{pid}/children", {"children": blocks[i:i + 100]})
        print("detail body written:", len(blocks), "blocks")


if __name__ == "__main__":
    main()
