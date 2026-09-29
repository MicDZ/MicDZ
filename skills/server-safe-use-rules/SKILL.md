---
name: server-safe-use-rules
description: Apply server safe use rules when working with server storage, personal workspaces, shared datasets, or GPU workloads, and keep the Notion databases of experiments, research ideas, and todos up to date.
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

## 5. Log every experiment to Notion

After an experiment, log it to the Notion Experiments database. Do this once per experiment, right after you have results. Keep it cheap: **use the bundled script and follow the rules below — do not probe the API, re-fetch the schema, read records back to verify, or write your own helper.**

### 5.1 The fast path — one command

There is a ready-made script next to this file: `notion_log.py` (same directory as this SKILL.md). Run it once per experiment. It handles the field names, ISO time conversion, select options, attachments, and the detail page. Pass only what you know.

```bash
python3 <skill_dir>/notion_log.py \
  --name EXP-2026-0927-lr2e4 \
  --status 成功 --agent Claude --verdict 得出结论 \
  --nature 调参实验 --project CloseLoopHOI \
  --start "2026-09-26 09:12" --end "2026-09-26 15:48" --hours 6.6 \
  --device-model "RTX 6000 Ada" --device-count 2 --device-hours 6.6 --device-mem 41.2 \
  --dataset GSM8K --dataset-path /mnt/nas/SharedDatasets/gsm8k/ \
  --metric gsm8k_acc --metric-value 0.612 --baseline 0.594 --delta 0.018 \
  --hypothesis "..." --method "..." --metrics-json '{"acc":0.612}' \
  --summary "..." --conclusion "..." \
  --code-path /path/to/config.yaml --log-path /path/to/run/ \
  --env "MBZUAI H200 x1, torch 2.5" --tags baseline,hyperparam \
  --attach curve.png --attach demo.mp4 \
  --page @detail.md
```

`--page` takes a path to a markdown file (`@file.md`). Use it only for experiments that made real progress (see 5.4). It prints `OK page_id: ...` and the URL when done — that's your confirmation, no need to read the row back.

Requires `NOTION_TOKEN` and `NOTION_DATA_SOURCE_ID` in the environment; both are already set on this machine.

### 5.2 Argument reference

Only `--name` is required. Everything else is optional; pass what you have, omit what you don't.

- `--name` → 实验名称. Short id like `EXP-2026-0927-llama3-lora-lr2e4`.
- `--status` → 状态. `计划中`/`运行中`/`成功`/`失败`/`已放弃`.
- `--agent` → 执行 Agent. `Claude` / `Codex` / `人工` (whichever you are).
- `--verdict` → 简明结论. `得出结论`/`得出部分结论`/`无法得出结论`/`待分析`.
- `--nature` → 实验性质 (repeatable). `主实验`/`消融实验`/`调参实验`/`预实验`/`复现验证`/`调试排错`.
- `--project` → 项目. Multi-select; comma-separated for more than one, e.g. `CloseLoopHOI,HOIEstimation`. Existing options: `CloseLoopHOI` `HOIEstimation`. New names are created automatically.
- `--start` / `--end` → 开始/结束时间. `"YYYY-MM-DD HH:MM"` (UTC), ISO 8601, or epoch ms.
- `--hours` → 时长(小时). Number.
- `--device-model` → 计算设备型号. **Pass the real device name.** For GPU work: `H200`, `A100`, `RTX 6000 Ada`, `RTX 5090`, etc. For CPU work: `CPU (Intel)`, `CPU (AMD)`, `CPU (Apple Silicon)`. If it isn't an existing option, the script creates the option — never fall back to `其他` just because the exact name isn't listed. Record CPU-only experiments too, with their CPU model.
- `--device-count` → 计算设备数量. Number (GPU count, or core/process count for CPU).
- `--device-hours` → 计算设备时长 = device-count × hours. Number. For GPU work this is card-hours.
- `--device-mem` → 计算设备显存(GB). Peak memory in GB. Optional — omit for CPU-only runs, where there is no meaningful number here.
- `--dataset` / `--dataset-path` → 数据集 / 数据集路径.
- `--metric` / `--metric-value` / `--baseline` / `--delta` → 主指标名称/主指标值/基线值/提升. The single most important metric.
- `--hypothesis` / `--method` / `--summary` / `--conclusion` → 假设与目标 / 方法与改动 / 结果摘要 / 结论与后续.
- `--metrics-json` → 指标(JSON). A JSON string of all metrics, e.g. `'{"acc":0.612}'`.
- `--code-path` / `--log-path` / `--env` → 代码/配置路径 / 日志/产物路径 / 运行环境.
- `--tags` → Tags, comma-separated, e.g. `baseline,hyperparam`. Existing options: `baseline` `ablation` `bug-fix` `data` `hyperparam` `model`.
- `--link` → 关联链接 (a URL, e.g. wandb).
- `--attach` → 可视化结果 (repeatable). Local image/video file; the script uploads it. Max 20 MB per file.
- `--page` → also write a detail page body (markdown file) onto the row's page.

### 5.3 Do not waste effort

- **Do not** GET the data source schema or query rows to "check fields" or "see what options exist" — the options are listed above.
- **Do not** re-implement the API calls with curl or your own Python. Use `notion_log.py`.
- **Do not** read the page back to confirm it was written. The script already errors out if the API rejected it; `OK page_id:` means success.
- **Do not** hand-build Notion JSON. Notion is picky (every property needs a `type` key, rich_text is an array of objects, dates are ISO strings). The script maps the simple flags above to the correct shape.

### 5.4 Detail docs for experiments that made progress

If an experiment got a real, keep-worthy result, pass `--page @file.md` with a body covering at minimum: **实验设计** (what & why), **如何复现** (data, config, command, environment), **结果与分析**. The script creates a **standalone detail doc** nested under the row's page, fills it, and points the row's 关联链接 at it — so the row links straight to the full write-up. For routine/failed/abandoned experiments, skip `--page`.

The markdown body supports `#`/`##`/`###` headings, `- ` bullets, and plain paragraphs.

### 5.5 Fallback API facts

Only if `notion_log.py` is missing or broken: base URL `https://api.notion.com/v1`, header `Notion-Version: 2026-03-11`. Rows are created with `POST /pages` and parent `{"type":"data_source_id","data_source_id":<id>}` — **not** `database_id` (Notion's 2025-09 data-source model). Query rows with `PATCH /data_sources/{id}/query`. If you hit something the script can't do, tell the user rather than rebuilding it.

## 6. Log research ideas to Notion

When you formulate a research idea worth keeping — a new method, a gap you spotted in the literature, a direction worth pursuing — log it to the Ideas database with `notion_idea.py` (next to this SKILL.md). Same rules as section 5: one command, no probing, no hand-rolled API calls.

This is for ideas, not results. Experiments go to the Experiments table (section 5).

```bash
python3 <skill_dir>/notion_idea.py \
  --name "IDEA-2026-0928-01 视频扩散骨干手物联合前馈" \
  --status 待评估 --priority P0 --source 文献调研 --agent Claude --project HOIEstimation \
  --direction 前馈估计 --direction 视频扩散骨干 \
  --claim "..." --gap "..." --method "..." --data-eval "..." --risk "..." \
  --competitors "..." --assets "..." --venue "CVPR 2027" --compute "8x80GB, 1-2 周" \
  --next "..." --date 2026-09-28 --link "https://..." --tags survey,feedforward
```

Only `--name` is required; pass what you have. Takes `NOTION_TOKEN` and `NOTION_IDEAS_DATA_SOURCE_ID` from the environment (already set on this machine).

- `--name` → 想法名称. Short id + one-line title, like `IDEA-2026-0928-01 视频扩散骨干手物联合前馈`.
- `--status` → 状态. `待评估`/`评估中`/`已采纳`/`进行中`/`已完成`/`已放弃`.
- `--priority` → 优先级. `P0`/`P1`/`P2`/`P3`.
- `--source` → 来源. `文献调研`/`实验观察`/`讨论`/`审稿意见`/`其他`.
- `--agent` → 提出者. `Claude`/`Codex`/`人工` (whichever you are).
- `--project` → 项目. Multi-select; comma-separated for more than one. Existing options: `CloseLoopHOI` `HOIEstimation`. New names are created automatically.
- `--direction` → 方向 (repeatable). Existing: `前馈估计` `视频扩散骨干` `生成式先验` `可靠性与不确定性` `物理仿真` `数据引擎` `评测基准` `铰接/可变形` `MLLM` `长时程跟踪`.
- `--claim` → 核心 claim. `--gap` → 为什么是空白. `--method` → 方法骨架.
- `--data-eval` → 数据与评测. `--risk` → 风险. `--competitors` → 竞品/相关工作.
- `--assets` → 资产衔接. `--venue` → 目标会议. `--compute` → 预估算力. `--next` → 下一步.
- `--date` → 提出日期. `--link` → 关联链接 (a URL). `--tags` → Tags, comma-separated. Existing: `survey` `feedforward` `generative` `benchmark` `physics` `data` `uncertainty`.

## 7. Track todos in Notion

Keep the Todos database current as you work: add a todo when you or the user agrees on something to do, and flip it to `已完成` when you finish it. Use `notion_todo.py` (next to this SKILL.md). Same rules as section 5 — one command, no probing, no hand-rolled API calls.

```bash
# create
python3 <skill_dir>/notion_todo.py \
  --task "给 MPPI teacher 加动作代价项" \
  --status 待办 --priority P1 --agent Claude --project CloseLoopHOI \
  --type 编码 --type 实验 --due 2026-09-30 --estimate 3 \
  --description "..." --experiment EXP-2026-0927-dagger-v2 \
  --link "https://..." --tags quick-win

# update an existing one (mark done, reprioritize, ...)
python3 <skill_dir>/notion_todo.py --page-id <uuid> --status 已完成 --done-time 2026-09-29
```

Takes `NOTION_TOKEN` and `NOTION_TODO_DATA_SOURCE_ID` from the environment (already set on this machine). `--page-id` comes from the `OK page_id:` line of the create call, or from the row's URL.

- `--task` → 任务 (title). Required when creating.
- `--page-id` → update this existing todo instead of creating a new one.
- `--status` → 状态. `待办`/`进行中`/`已完成`/`已阻塞`/`已取消`.
- `--priority` → 优先级. `P0`/`P1`/`P2`/`P3`.
- `--agent` → 执行 Agent. `Claude`/`Codex`/`人工`.
- `--project` → 项目. Multi-select, comma-separated. Existing: `CloseLoopHOI` `HOIEstimation`.
- `--type` → 任务类型 (repeatable). `实验`/`编码`/`阅读`/`写作`/`数据`/`部署`/`调试`.
- `--due` / `--done-time` → 截止日期 / 完成时间. `YYYY-MM-DD` (UTC) or ISO 8601.
- `--estimate` → 预估时长(小时). Number.
- `--description` → 描述. `--experiment` → 关联实验 (an experiment name, free text).
- `--link` → 关联链接 (a URL). `--tags` → Tags, comma-separated. Existing: `blocker` `quick-win` `long-term` `review` `paper`.

Only create todos that were actually agreed on — don't invent work items. Keep statuses accurate; a stale board is worse than none.
