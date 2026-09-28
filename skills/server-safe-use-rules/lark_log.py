#!/usr/bin/env python3
"""Log an experiment to the Lark Experiments bitable. One command, no curl juggling.

Usage:
  python3 lark_log.py \
      --name EXP-2026-0927-lr2e4 --status 成功 --agent Claude \
      --verdict 得出结论 --nature 调参实验 --project RCL-baseline \
      --start "2026-09-26 09:12" --end "2026-09-26 15:48" --hours 6.6 \
      --device-model "RTX 6000 Ada" --device-count 1 --device-hours 6.6 --device-mem 41.2 \
      --dataset GSM8K --dataset-path /mnt/nas/SharedDatasets/gsm8k/ \
      --metric gsm8k_acc --metric-value 0.612 --baseline 0.594 --delta 0.018 \
      --hypothesis "..." --method "..." --metrics-json '{"acc":0.612}' \
      --summary "..." --conclusion "..." --code-path ... --log-path ... \
      --env "MBZUAI H200 x1" --tags baseline,hyperparam --link "https://..." \
      --attach curve.png --attach demo.mp4 --doc "详细 markdown 文本或 @文件.md"

Everything is optional except --name. Times accept "YYYY-MM-DD HH:MM" (local) or epoch ms.
Single/multi-select fields: if you pass a value that is not an existing option, it is
created automatically (so 计算设备型号 can be any real device, project can be anything).

Compute device fields work for CPUs too: use e.g. --device-model "CPU (AMD)" for a
CPU-only experiment, and omit --device-mem (there is no meaningful VRAM for CPU work).
"""
import argparse
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request

BASE = "https://open.larksuite.com/open-apis"
# Credentials come from the environment. Set LARK_APP_ID and LARK_APP_SECRET before use.
APP_ID = os.environ.get("LARK_APP_ID", "")
APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
APP = "WaaSbiiKsadefOsXJfXjeT5DpFg"
TBL = "tblotS3v7mxzHfxy"

if not APP_ID or not APP_SECRET:
    sys.exit("Set LARK_APP_ID and LARK_APP_SECRET in the environment first.")

# field_name -> type. select fields map to their option-set so we can auto-create.
TEXT = ["数据集", "数据集路径", "假设与目标", "方法与改动", "指标(JSON)",
        "结果摘要", "结论与后续", "代码/配置路径", "日志/产物路径", "运行环境", "主指标名称"]
NUM = ["时长(小时)", "计算设备数量", "计算设备时长", "计算设备显存(GB)", "主指标值", "基线值", "提升"]
SINGLE = {"状态": "状态", "执行 Agent": "执行 Agent", "简明结论": "简明结论", "计算设备型号": "计算设备型号",
          "项目": "项目"}
MULTI = {"实验性质": "实验性质", "Tags": "Tags"}

_token = None


def token():
    global _token
    if _token is None:
        req = urllib.request.Request(
            f"{BASE}/auth/v3/tenant_access_token/internal",
            data=json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode(),
            headers={"Content-Type": "application/json"})
        _token = json.load(urllib.request.urlopen(req))["tenant_access_token"]
    return _token


def api(method, path, body=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(f"{BASE}{path}", data=data,
                                 headers={"Authorization": f"Bearer {token()}", "Content-Type": ctype},
                                 method=method)
    for attempt in (0, 1):  # retry once on expired token
        try:
            r = json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as e:
            r = json.loads(e.read() or b"{}")
        if r.get("code") in (99991663, 99991661) and attempt == 0:  # token expired
            globals()["_token"] = None
            req.replace_header("Authorization" if hasattr(req, "replace_header") else "authorization",
                               f"Bearer {token()}")
            req.headers["Authorization"] = f"Bearer {token()}"
            continue
        if r.get("code") != 0:
            raise RuntimeError(f"{method} {path}: {r}")
        return r.get("data", {})
    raise RuntimeError(f"{method} {path}: token refresh failed")


def to_ms(s):
    if s is None:
        return None
    s = s.strip()
    if s.isdigit():
        return int(s)
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(s, fmt).replace(tzinfo=datetime.timezone.utc)
            return int(dt.timestamp() * 1000)
        except ValueError:
            pass
    raise SystemExit(f"bad time: {s!r} (use 'YYYY-MM-DD HH:MM' UTC or epoch ms)")


def ensure_options(field_name, values):
    """Add any missing options to a select field, return the final option names to write."""
    if not values:
        return values
    fields = api("GET", f"/bitable/v1/apps/{APP}/tables/{TBL}/fields?page_size=100")["items"]
    f = next(x for x in fields if x["field_name"] == field_name)
    prop = f.get("property") or {}
    opts = prop.get("options", [])
    have = {o["name"] for o in opts}
    missing = [v for v in values if v not in have]
    if missing:
        opts = opts + [{"name": m} for m in missing]
        api("PUT", f"/bitable/v1/apps/{APP}/tables/{TBL}/fields/{f['field_id']}",
            {"field_name": field_name, "type": f["type"], "property": {"options": opts}})
    return values


def upload(path):
    import mimetypes
    fn = os.path.basename(path)
    size = os.path.getsize(path)
    boundary = "----larklogboundary"
    mime = mimetypes.guess_type(fn)[0] or "application/octet-stream"
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file_name\"\r\n\r\n{fn}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"parent_type\"\r\n\r\nbitable_image\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"parent_node\"\r\n\r\n{APP}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"size\"\r\n\r\n{size}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fn}\"\r\n"
            f"Content-Type: {mime}\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--\r\n".encode()
    raw = head + open(path, "rb").read() + tail
    d = api("POST", "/drive/v1/medias/upload_all", raw=raw,
            ctype=f"multipart/form-data; boundary={boundary}")
    return d["file_token"]


def make_doc(title, md):
    doc = api("POST", "/docx/v1/documents", {"title": title, "folder_token": ""})["document"]
    did = doc["document_id"]
    if md.startswith("@"):
        md = open(md[1:]).read()
    blocks = []
    for line in md.splitlines():
        t = line.rstrip()
        if not t:
            continue
        if t.startswith("### "):
            blocks.append({"block_type": 5, "heading3": {"elements": [{"text_run": {"content": t[4:]}}]}})
        elif t.startswith("## "):
            blocks.append({"block_type": 4, "heading2": {"elements": [{"text_run": {"content": t[3:]}}]}})
        elif t.startswith("# "):
            blocks.append({"block_type": 3, "heading1": {"elements": [{"text_run": {"content": t[2:]}}]}})
        else:
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": t}}]}})
    for i in range(0, len(blocks), 50):
        api("POST", f"/docx/v1/documents/{did}/blocks/{did}/children", {"children": blocks[i:i + 50]})
    return did


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--status"); p.add_argument("--agent"); p.add_argument("--verdict")
    p.add_argument("--nature", action="append"); p.add_argument("--project")
    p.add_argument("--start"); p.add_argument("--end"); p.add_argument("--hours", type=float)
    # compute-device flags; --gpu-* kept as aliases for backward compatibility
    p.add_argument("--device-model", "--gpu-model", dest="device_model")
    p.add_argument("--device-count", "--gpu-count", dest="device_count", type=float)
    p.add_argument("--device-hours", "--gpu-hours", dest="device_hours", type=float)
    p.add_argument("--device-mem", "--vram", dest="device_mem", type=float,
                   help="peak memory in GB (GPU VRAM, or RAM for CPU runs)")
    p.add_argument("--dataset"); p.add_argument("--dataset-path")
    p.add_argument("--metric"); p.add_argument("--metric-value", type=float)
    p.add_argument("--baseline", type=float); p.add_argument("--delta", type=float)
    p.add_argument("--hypothesis"); p.add_argument("--method"); p.add_argument("--metrics-json")
    p.add_argument("--summary"); p.add_argument("--conclusion")
    p.add_argument("--code-path"); p.add_argument("--log-path"); p.add_argument("--env")
    p.add_argument("--tags"); p.add_argument("--link")
    p.add_argument("--attach", action="append"); p.add_argument("--doc")
    a = p.parse_args()

    f = {"实验名称": a.name}
    if a.status: f["状态"] = ensure_options("状态", [a.status])[0]
    if a.agent: f["执行 Agent"] = ensure_options("执行 Agent", [a.agent])[0]
    if a.verdict: f["简明结论"] = ensure_options("简明结论", [a.verdict])[0]
    if a.device_model: f["计算设备型号"] = ensure_options("计算设备型号", [a.device_model])[0]
    if a.nature: f["实验性质"] = ensure_options("实验性质", a.nature)
    if a.tags: f["Tags"] = ensure_options("Tags", [t.strip() for t in a.tags.split(",") if t.strip()])
    if a.project: f["项目"] = ensure_options("项目", [a.project])[0]  # 项目 is a single-select
    for arg, key in ((a.dataset, "数据集"), (a.dataset_path, "数据集路径"), (a.hypothesis, "假设与目标"),
                     (a.method, "方法与改动"), (a.metrics_json, "指标(JSON)"), (a.summary, "结果摘要"),
                     (a.conclusion, "结论与后续"), (a.code_path, "代码/配置路径"),
                     (a.log_path, "日志/产物路径"), (a.env, "运行环境"), (a.metric, "主指标名称")):
        if arg: f[key] = arg
    for arg, key in ((a.hours, "时长(小时)"), (a.device_count, "计算设备数量"),
                     (a.device_hours, "计算设备时长"), (a.device_mem, "计算设备显存(GB)"),
                     (a.metric_value, "主指标值"), (a.baseline, "基线值"), (a.delta, "提升")):
        if arg is not None: f[key] = arg
    if a.start: f["开始时间"] = to_ms(a.start)
    if a.end: f["结束时间"] = to_ms(a.end)
    if a.link: f["关联链接"] = {"text": a.link, "link": a.link}
    if a.attach:
        f["可视化结果"] = [{"file_token": upload(x)} for x in a.attach]
    if a.doc:
        did = make_doc(f"{a.name} 详情", a.doc)
        f["关联链接"] = {"text": f"{a.name} 详情", "link": f"https://vjpfcffllw7f.jp.larksuite.com/docx/{did}"}

    rec = api("POST", f"/bitable/v1/apps/{APP}/tables/{TBL}/records", {"fields": f})["record"]
    print("OK record_id:", rec["record_id"])
    if "关联链接" in f:
        print("doc/link:", f["关联链接"]["link"])


if __name__ == "__main__":
    main()
