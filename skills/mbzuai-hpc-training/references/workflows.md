# Safe training workflows

Read [policy-and-safety.md](policy-and-safety.md) first for any state-changing task, then read [clusters.md](clusters.md) for the selected cluster.

## 1. Access and SSH

The configured account is:

- Cluster: CSCC by default.
- Username: `han.zhou`.
- CSCC/CIAI SSH access: use the existing `ciai-via-local` alias and forwarding setup.
- CSCC/CIAI login command: `ssh ciai-via-local`.
- When Jebel/H200 is selected: `ssh ciai-Jebel`, subject to the temporary-access deadline in [clusters.md](clusters.md).

For CSCC/CIAI, connect from `unit1.rcl.micdz.cn` through the existing `ciai-via-local` SSH alias and forwarding setup. Execute the connection only when the user's request authorizes remote access:

```bash
ssh ciai-via-local
```

Do not run `ssh-keygen`, `ssh-copy-id`, add `-i`, inspect key files, or modify `authorized_keys` for this account. If authentication later fails, report the error and wait for an explicit key-troubleshooting request.

The SCP example below targets CSCC/CIAI. For Jebel, use `ciai-Jebel:<verified-destination>` and check the temporary-access window first.

If SCP fails with `subsystem request failed`, use legacy SCP mode:

```bash
scp -O <local-file> ciai-via-local:<exact-destination>
```

Before any upload, verify the local source and exact remote destination and check whether an existing file would be overwritten. Never embed a password or key content.

## 2. Place data and environments

Use the placement table instead of putting everything in `$HOME`:

| Content | CSCC/CIAI | CAMD |
|---|---|---|
| Code, small configs, small logs | `$HOME` | `/vast/users/<confirmed-camd-username>` |
| Large datasets/checkpoints | `/l/users/han.zhou` | `/vast/users/<confirmed-camd-username>` |
| Per-job temporary data | compute-node `/tmp/han.zhou/...` | allocated-node local scratch only when confirmed |

For Jebel, storage paths, quotas, scratch behavior, and environment initialization are not recorded in the email. Discover or confirm them before uploads/installations; do not reuse `/l/users/han.zhou`, `/vast/users/...`, or `/apps/local/...` without verification. Plan an external backup and approved removal before testing access expires.

Compute-node `/tmp` is temporary. Copy only reproducible or backed-up inputs there, and copy required outputs/checkpoints to persistent storage before the allocation ends. This skill must not delete scratch or persistent files automatically.

Conda environments contain many small files. On CSCC/CIAI, prefer `$HOME` while the environment fits the home quota; contact HPC before placing a large small-file-heavy environment on `/l`.

Known CSCC/CIAI Conda initialization:

```bash
source /apps/local/conda_init.sh
conda create -p <approved-environment-path>
conda activate <approved-environment-path>
```

A second known initializer is `/apps/local/anaconda2023/conda_init.sh`. Use a read-only existence check to choose between the two. Do not guess or add `source` or `conda activate` to `.bashrc` automatically. Put explicit environment initialization inside the batch script. Do not install packages until the user approves the environment and path.

## 3. Design the resource request

Use CSCC unless the user explicitly names another cluster. Collect these requirements before writing directives:

- Target cluster and permitted workload class.
- Training command and framework.
- Single-node or distributed execution.
- GPUs per node and total GPUs.
- Processes per node and why they match GPU allocation.
- CPU workers/threads, system memory, wall time, and checkpoint cadence.
- Persistent dataset, output, and checkpoint paths.
- Whether the task is production batch, short debug, or Jupyter.

Use the smallest reasonable request. For distributed training, enforce:

- `GPUs per node <= physical GPUs per node`.
- `total GPUs = nodes x GPUs per node` unless an explicitly justified heterogeneous layout is supported.
- `--nproc_per_node` normally equals GPUs per node for one process per GPU.
- Total GPUs and concurrent jobs remain inside the limits in [clusters.md](clusters.md).
- CPU and memory requests fit the node and are justified by data loading or preprocessing.
- Wall time remains within the partition/QoS limit.

## 4. Build and lint the batch script

A production script should include an explicit job name, log path, partition, required QoS, wall time, node count, task/process layout, CPU count, memory, GPU count, environment activation, working directory, and training command.

Use this structure as a scaffold for clusters with a documented required QoS; replace every angle-bracket placeholder and validate it against the selected cluster. For Jebel, use the separate template below:

```bash
#!/bin/bash
#SBATCH --job-name=<name>
#SBATCH --output=<persistent-log-dir>/%x-%j.out
#SBATCH --nodes=<nodes>
#SBATCH --ntasks-per-node=<tasks-per-node>
#SBATCH --cpus-per-task=<cpus-per-task>
#SBATCH --mem=<system-memory>
#SBATCH --gres=gpu:<gpus-per-node>
#SBATCH --partition=<partition>
#SBATCH --qos=<qos>
#SBATCH --time=<HH:MM:SS>

set -euo pipefail
source <verified-conda-initializer>
conda activate <environment-path>
cd <project-directory>

<training-command>
```

For a CPU-only job, omit `--gres` and use the recorded CPU partition/QoS. CAMD submission is blocked until the user supplies administrator-confirmed QoS, wall-time, and total-GPU limits.

### Jebel H200 batch template

This adapts the supplied 1-GPU/4-hour example with explicit error logging, fail-fast behavior, and a working-directory placeholder. The resource values remain the email's example values; adjust only to justified needs within the Jebel limits. The example assumes `python` is available in a verified environment; add verified environment initialization if needed.

```bash
#!/bin/bash
#SBATCH --job-name=gpu-test
#SBATCH --output=output-%j.txt
#SBATCH --error=error-%j.txt
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=40G
#SBATCH --gres=gpu:1
#SBATCH --partition=h200
#SBATCH --time=04:00:00
#SBATCH --comment="h200test2609"

set -euo pipefail
cd <verified-jebel-project-directory>
hostname
nvidia-smi
python test.py
```

Replace the directory placeholder and `python test.py` with the verified project path and intended training command. Submit from a verified writable directory so Slurm can create the relative log files; Slurm opens them before the script's `cd`. No explicit QoS is required by the notice. For two-GPU distributed training, request 2 GPUs only if the user's existing allocations leave that capacity and use the framework's matching process layout.

Reject a script containing any of these:

- `salloc`, `--exclusive`, Slurm email flags, or a sleep-only workload.
- An attempt to set `CUDA_VISIBLE_DEVICES` to bypass allocation.
- A missing or implicit partition.
- A missing required QoS on CSCC/CIAI.
- A Jebel job missing the exact `h200test2609` comment, exceeding 2 GPUs total per user or 2 pending-plus-running jobs, requesting more than 8 hours, or extending beyond the testing window and necessary backup/cleanup time.
- A GPU/node/process mismatch.
- Resource totals or wall time beyond [clusters.md](clusters.md).
- Training, testing, or benchmarking commands intended for the login node.
- Secrets, private-key content, Jupyter token URLs, or passwords.
- Unreviewed remote helper scripts or destructive cleanup.

Also flag internally inconsistent examples rather than preserving their comments or numbers.

## 5. Debug and Jupyter

For CSCC/CIAI interactive GPU debugging, use `srun` with `gpu-debug-qos`, no more than 3 hours, and only the needed GPUs. Never use `salloc`.

For CAMD, never use `salloc`. The mandatory policy requires `gpu-debug-qos`, but CAMD availability is unresolved in this skill. Obtain administrator confirmation before any stateful interactive `srun`; do not guess a QoS or silently omit it.

For Jebel, the notice documents batch testing only. Confirm interactive/Jupyter policy before using those modes; do not inherit another cluster's debug QoS.

Jupyter must run on an allocated compute node, not on the login node. Required workflow:

1. Prepare a cluster-correct batch script with explicit partition, QoS when required, CPU, memory, GPU if needed, time, and log path.
2. Within the allocation, initialize the environment and start `jupyter lab --no-browser` on a random high port.
3. Submit with `sbatch` only when authorized.
4. Use VS Code Remote SSH and "Existing Jupyter Server" to connect to the compute-node server.
5. Verify from a notebook that the hostname is a compute node.

Treat the Jupyter URL as a bearer secret because it contains a token. Do not paste it into chat, commit it, or include it in a shared log.

## 6. Submit and verify

Draft submission separately from the script:

```bash
sbatch <reviewed-script.sh>
```

For Jebel, first check the access window, total current GPU allocations, and all pending/running jobs with `squeue --me` and, where needed, `scontrol show job <job-id>`. Account for the new job and recheck near submission; a prior queue snapshot does not reserve capacity.

Execute only after the user authorizes submission. Record the numeric job ID returned by Slurm, then use a read-only check:

```bash
squeue -j <job-id>
```

or:

```bash
squeue --me
```

For completed jobs, use `sacct -j <job-id>` where available and inspect the exact output/error files. Prefer one-shot checks or a modest monitoring interval over a one-second `watch` loop.

## 7. Diagnose failures

Diagnose without immediately resubmitting:

- Pending: inspect Slurm reason, partition/QoS, resource size, and estimated start time (`squeue --start`).
- OOM: distinguish system-memory failure from GPU-memory failure; change only the relevant request or training configuration.
- CUDA mismatch on CSCC/CIAI or Jebel: compare the allocated node's driver/toolkit with the framework build.
- ROCm issue on CAMD: target ROCm 6.3, use `rocm-smi`, and check ROCm-compatible framework/package builds.
- Distributed hang: validate nodes, tasks, GPUs per node, process count, rendezvous host/port, and framework backend.
- Storage failure: inspect the correct quota and path; do not delete files automatically.
- Network/package failure on CAMD: request approved domain whitelisting; never bypass the proxy policy.

Do not submit repeated retries unless the user requested a fix-and-rerun workflow and the root cause has been addressed.

## 8. Cancel or finish

To cancel, first resolve the exact job with `squeue --me`. Never use account-wide cancellation. After explicit confirmation, the only permitted cancellation shape is:

```bash
scancel <exact-job-id>
```

Verify that the job is gone or enters the expected terminal state.

After training:

- Confirm required checkpoints, outputs, and logs are in persistent storage.
- Report storage usage and candidate cleanup paths.
- Remind the user that the cluster does not provide backup and that employee data is deleted on departure.
- On Jebel, export required data to a verified destination outside Jebel, check the backup, and complete separately authorized removal before the testing deadline. Access will be revoked afterward; persistent cluster storage is not a sufficient backup.
- Never delete the candidates automatically; cleanup requires a separate, exact authorization.
