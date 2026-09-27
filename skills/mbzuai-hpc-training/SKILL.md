---
name: mbzuai-hpc-training
description: Plan, review, and operate policy-compliant MBZUAI CSCC, CIAI, CAMD, or Jebel H200 training workflows for the configured user han.zhou. Use for SSH access, storage placement, environments, Slurm scripts, GPU/CPU jobs, Jupyter, monitoring, or cleanup on these clusters; do not use for unrelated HPC systems.
---

# MBZUAI HPC Training

Help the user prepare and, when explicitly authorized, operate training jobs on MBZUAI CSCC, CIAI, CAMD, or Jebel H200 without violating cluster policy or exposing credentials. This skill and its references are the complete action guide; apply only the rules recorded here and do not replace them with other examples.

## Configured user profile

- Default cluster: `CSCC`, unless the user explicitly selects `CIAI`, `CAMD`, or `Jebel`/`H200`.
- Username: `han.zhou`.
- This copy runs on `unit1.rcl.micdz.cn`. Use its existing `ciai-via-local` SSH alias for the shared CIAI/CSCC login; preserve the alias and forwarding configuration.
- Default CSCC/CIAI login command: `ssh ciai-via-local`.
- Jebel H200 access is separately granted to `han.zhou`: use `ssh ciai-Jebel` when Jebel/H200 is selected. This is temporary testing access; read its deadline and limits in [references/clusters.md](references/clusters.md) before use.
- Do not generate, copy, replace, inspect, or troubleshoot SSH keys unless the user explicitly asks for key troubleshooting. Do not run `ssh-copy-id` for this configured account.

## Start safely

Before giving cluster-specific commands or changing remote state:

1. Use `CSCC` by default. Change cluster only when the user explicitly names `CIAI`, `CAMD`, or `Jebel`/`H200`.
2. Read [references/policy-and-safety.md](references/policy-and-safety.md) for every task that may connect, write remote files, install software, submit/cancel a job, or remove data.
3. Apply the limits recorded in [references/clusters.md](references/clusters.md). If a required value is absent or internally unresolved, stop before state change and ask the user or the named HPC support contact; do not guess.

## Route by task

- For account access, hostnames, hardware, quotas, partitions, QoS, or per-cluster limits, read [references/clusters.md](references/clusters.md).
- For designing, checking, submitting, monitoring, or cancelling a Slurm job; Jupyter; environments; data transfer; or post-run handling, read [references/workflows.md](references/workflows.md).
- For a pure conceptual question, answer from the smallest relevant reference.

## Operating contract

- Treat the mandatory policy rules as higher priority than examples or cheat sheets. The bundled references already resolve known conflicts conservatively.
- Never run training, inference, tests, benchmarks, or other user code on a login node. Login nodes are for lightweight preparation and Slurm submission only.
- Prefer `sbatch` for production work and `srun` with `gpu-debug-qos` for short CSCC/CIAI interactive debugging. Never use `salloc`; the top-level policy forbids it even though lower-level pages contain `salloc` examples.
- Never use `--exclusive`, `CUDA_VISIBLE_DEVICES` to access more GPUs than requested, Slurm email flags, or a sleep-only allocation.
- Request only justified resources. Always specify partition, required QoS (only where documented), GPU count, CPU count, memory, wall time, logs, and job name explicitly. Jebel requires the exact project comment `--comment="h200test2609"`; its supplied batch example requires no explicit QoS. Never rely on the default partition.
- Treat all example code as illustrative, not trusted executable scripts. Correct internal inconsistencies before presenting a script, and flag any correction.
- Keep secrets out of commands, scripts, logs, and chat. Never read, print, upload, or send a private SSH key or a Jupyter token URL.
- Remote mutations require user intent for that exact action. A request to draft or review does not authorize SSH connection, file upload, environment installation, job submission, cancellation, or cleanup.
- Do not execute broad or destructive commands. In particular, never run `rm`, `scancel -u ...`, unreviewed shared helper scripts, or shell-startup edits. See the safety reference for narrow alternatives and approval gates.

## Job-planning output

When preparing a training job, provide:

1. The selected cluster and why the workload fits its permitted workload class.
2. A resource table or compact summary: partition, QoS (or not specified by the cluster notice), required project comment, nodes, GPUs per node, total GPUs, tasks, CPUs per task, memory, wall time, and storage paths.
3. A complete batch script with placeholders clearly marked and no unsupported flags.
4. A compliance check against the bundled policy and cluster limits.
5. The exact next command separately. Do not run it unless the user asked for that state change.

After any authorized action, verify the observable result: SSH authentication mode, copied destination, assigned Slurm job ID, queue state, output path, or cancellation state. Never claim success from command exit alone when a direct check is available.
