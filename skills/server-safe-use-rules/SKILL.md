---
name: server-safe-use-rules
description: Apply server safe use rules when working with server storage, personal workspaces, shared datasets, or GPU workloads.
---

# Server Safe Use Rules

## 1. Storage locations

- Store large files, such as datasets, model checkpoints, and generated outputs, in `/mnt/nas/Group/<username>/`, where `<username>` is the current server user returned by `whoami`.
    
- Store small program files and files that require fast or frequent reads and writes in `$HOME/Projects/`.
    
- Use `/mnt/nas/SharedDatasets/` only to read existing shared datasets. Do not store new files there.
    

## 2. Personal workspace boundaries

- Use only `/mnt/nas/Group/<username>/` as your personal NAS workspace. Create this directory if it does not exist.
    
- Do not list, read, modify, move, or delete files in other users’ directories without explicit permission.
    
- If the current server username cannot be determined, ask the user before accessing any personal workspace. Do not guess the username.
    

## 3. Shared datasets are read-only

- Treat `/mnt/nas/SharedDatasets/` and all its contents as strictly read-only. Shared datasets are organized by dataset name.
    
- Do not create, modify, rename, move, delete, or overwrite anything in this directory.
    
- Save derived data, preprocessing results, caches, indexes, and other generated files in your own workspace.
    
- Before running a tool that consumes shared datasets, configure any automatic writes to use your own workspace.
    

## 4. GPU usage and approval

- Short test runs, such as smoke tests or brief debugging checks, may proceed without user approval. Keep GPU usage minimal; do not split a larger workload into short runs to bypass approval.
    
- Before starting any other GPU workload, briefly state its purpose, GPU count, approximate runtime, and estimated total GPU-hours (`GPU count × runtime in hours`).
    
- A rough estimate is sufficient. Do not spend significant time refining it.
    
- Wait for explicit user approval before starting the proposed workload.
    
- Approval covers the described workload and estimated budget. If its scope changes materially or it is likely to exceed the approved budget, pause and request approval for a revised plan.
    
- CPU-only preparation may proceed while waiting for approval, provided it follows the storage and access rules above.

## 5. Log every experiment to Lark

After an experiment, log it to the Lark Experiments table. Do this once per experiment, right after you have results. Keep it cheap: **use the bundled script and follow the rules below — do not probe the API, re-fetch the schema, read records back to verify, or write your own helper.**

### 5.1 The fast path — one command

There is a ready-made script next to this file: `lark_log.py` (same directory as this SKILL.md). Run it once per experiment. It handles the token, the exact field names, epoch-millisecond time conversion, attachments, and the detail doc. Pass only what you know.

```bash
python3 <skill_dir>/lark_log.py \
  --name EXP-2026-0927-lr2e4 \
  --status 成功 --agent Claude --verdict 得出结论 \
  --nature 调参实验 --project RCL-baseline \
  --start "2026-09-26 09:12" --end "2026-09-26 15:48" --hours 6.6 \
  --device-model "RTX 6000 Ada" --device-count 2 --device-hours 6.6 --device-mem 41.2 \
  --dataset GSM8K --dataset-path /mnt/nas/SharedDatasets/gsm8k/ \
  --metric gsm8k_acc --metric-value 0.612 --baseline 0.594 --delta 0.018 \
  --hypothesis "..." --method "..." --metrics-json '{"acc":0.612}' \
  --summary "..." --conclusion "..." \
  --code-path /path/to/config.yaml --log-path /path/to/run/ \
  --env "MBZUAI H200 x1, torch 2.5" --tags baseline,hyperparam \
  --attach curve.png --attach demo.mp4 \
  --doc "# 实验设计\n...\n## 如何复现\n...\n## 结果与分析\n..."
```

`--doc` takes markdown text, or `@file.md` to read from a file. Use `--doc` only for experiments that made real progress (see 5.4). It prints `OK record_id: ...` when done — that's your confirmation, no need to read the row back.

### 5.2 Argument reference

Only `--name` is required. Everything else is optional; pass what you have, omit what you don't.

- `--name` → 实验名称. Short id like `EXP-2026-0927-llama3-lora-lr2e4`.
- `--status` → 状态. `计划中`/`运行中`/`成功`/`失败`/`已放弃`.
- `--agent` → 执行 Agent. `Claude` / `Codex` / `人工` (whichever you are).
- `--verdict` → 简明结论. `得出结论`/`得出部分结论`/`无法得出结论`/`待分析`.
- `--nature` → 实验性质 (repeatable). `主实验`/`消融实验`/`调参实验`/`预实验`/`复现验证`/`调试排错`.
- `--project` → 项目. Plain text project name.
- `--start` / `--end` → 开始/结束时间. `"YYYY-MM-DD HH:MM"` (UTC) or epoch ms.
- `--hours` → 时长(小时). Number.
- `--device-model` → 计算设备型号. **Pass the real device name.** For GPU work: `H200`, `A100`, `RTX 6000 Ada`, `RTX 5090`, etc. For CPU work: `CPU (Intel)`, `CPU (AMD)`, `CPU (Apple Silicon)`. If it isn't an existing option, the script creates the option — never fall back to `其他` just because the exact name isn't listed. Record CPU-only experiments too, with their CPU model.
- `--device-count` → 计算设备数量. Number (GPU count, or core/process count for CPU).
- `--device-hours` → 计算设备时长 = device-count × hours. Number. For GPU work this is card-hours.
- `--device-mem` → 计算设备显存(GB). Peak memory in GB. Optional — omit for CPU-only runs, where there is no meaningful number here.
- The older `--gpu-model/--gpu-count/--gpu-hours/--vram` flags still work as aliases.
- `--dataset` / `--dataset-path` → 数据集 / 数据集路径.
- `--metric` / `--metric-value` / `--baseline` / `--delta` → 主指标名称/主指标值/基线值/提升. The single most important metric.
- `--hypothesis` / `--method` / `--summary` / `--conclusion` → 假设与目标 / 方法与改动 / 结果摘要 / 结论与后续.
- `--metrics-json` → 指标(JSON). A JSON string of all metrics, e.g. `'{"acc":0.612}'`.
- `--code-path` / `--log-path` / `--env` → 代码/配置路径 / 日志/产物路径 / 运行环境.
- `--tags` → Tags, comma-separated, e.g. `baseline,hyperparam`. Existing options: `baseline` `ablation` `bug-fix` `data` `hyperparam` `model`.
- `--link` → 关联链接 (a URL, e.g. wandb). Ignored if `--doc` is set (the doc link wins).
- `--attach` → 可视化结果 (repeatable). Local image/video file; the script uploads it.
- `--doc` → also create a detail doc and link it from the row.

### 5.3 Do not waste effort

- **Do not** GET the table fields/records to "check the schema" or "see what options exist" — the options are listed above, and the script auto-creates anything missing.
- **Do not** re-implement the API calls with curl or your own Python. Use `lark_log.py`.
- **Do not** read the record back to confirm it was written. The script already errors out if the API rejected it; `OK record_id:` means success.
- **Do not** fetch a token by hand — the script does it and refreshes on expiry.
- Field names contain parentheses (`时长(小时)`, `指标(JSON)`, …). That's exactly why you should not hand-roll the JSON or pass them as Python kwargs. The script already maps the simple flags above to the correct names.

### 5.4 Detail docs for experiments that made progress

If an experiment got a real, keep-worthy result, pass `--doc` with a markdown body covering at minimum: **实验设计** (what & why), **如何复现** (data, config, command, environment), **结果与分析**. The script creates the doc, fills it, and puts its link into the row's 关联链接. For routine/failed/abandoned experiments, skip `--doc`.

### 5.5 If you truly cannot use the script

Only if `lark_log.py` is missing or broken, fall back to raw API: get a token by POSTing your `LARK_APP_ID`/`LARK_APP_SECRET` to `https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal`, then POST records to `.../bitable/v1/apps/WaaSbiiKsadefOsXJfXjeT5DpFg/tables/tblotS3v7mxzHfxy/records` with `{"fields":{...}}`. Dates are epoch ms. If you hit something the script can't do, tell the user rather than rebuilding it.
