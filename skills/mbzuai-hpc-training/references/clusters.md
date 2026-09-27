# Cluster selection, access, hardware, and limits

This file is the complete cluster-selection and limit reference for the skill. When a required value is not recorded, stop before state change and ask the user or the named administrator.

## Select the cluster deliberately

| Cluster | Permitted workload class | Account/job ceiling in policy | Accelerator |
|---|---|---|---|
| CSCC partition of CIAI | Small compute tasks | At most 2 GPU-node jobs and 4 GPUs per account | 4 x A100 SXM 40 GB per GPU node |
| CIAI | General and large-scale compute; small jobs are not allowed in this queue | At most 8 jobs and 12 GPUs per active account | 4 x A100 SXM 40 GB per GPU node |
| CAMD | Small, general, and large-scale compute | At most 3 jobs per active account | 8 x AMD MI210 per worker node |
| Jebel H200 testing | GPU training/testing during the temporary access window | At most 2 H200 GPUs total per user and 2 jobs total, including pending and running | NVIDIA H200; GPUs per node not specified |

Do not silently move a workload between clusters to obtain more resources. Access restrictions and the user's approved account determine availability.

Configured user profile:

- Default cluster: CSCC.
- Confirmed username: `han.zhou`.
- Confirmed temporary Jebel H200 login: `ssh ciai-Jebel`; see the expiry rules below.
- Confirmed CIAI login: `ssh ciai-via-local` using the existing SSH alias and forwarding setup.
- Do not assume that `han.zhou` is provisioned on CAMD; require explicit confirmation before using it there.

## CSCC

### Access

- Available to MBZUAI faculty, researchers, PhD students, Master's students, and visitors. First-year MSc students require supervisor approval.
- CIAI/CSCC access requires the HPC quiz, a score of at least 15/17, proof emailed to `hpc.admins@mbzuai.ac.ae`, and HPC-team verification.
- From `unit1.rcl.micdz.cn`, use the existing `ciai-via-local` SSH alias and forwarding setup.
- Use the SSH alias `ciai-via-local` for the configured account `han.zhou`. Do not switch to a `cscc` hostname unless the user explicitly provides and confirms one.

### GPU partition

- Partition: `cscc-gpu-p`
- Production QoS: `cscc-gpu-qos`
- Production wall time: at most 24 hours
- Minimum GPU request: 1 via `--gres=gpu:1`
- Account limit: at most 4 GPUs and 2 GPU-node jobs
- Debug/interactive QoS: `gpu-debug-qos`, at most 3 hours and 4 GPUs; use `srun`, never `salloc`

### CPU partition

- Partition: `cscc-cpu-p`
- QoS: `cscc-cpu-qos`
- At most 512 CPU cores, 2 running jobs, and 72 hours per job
- The cluster defaults to CPU if no partition is specified, but this skill always makes the partition explicit.

### Hardware and storage

- GPU node: 128 physical CPU cores, 256 GB RAM, 4 x A100 40 GB, local NVMe scratch.
- CPU node: 128 physical CPU cores, 256 GB RAM, local scratch.
- `/l/users/han.zhou`: Lustre, 2 TB default quota; use for large datasets and checkpoints. Contact HPC before storing many small files.
- `$HOME`: 100 GB default quota; use for code, logs, and small files.
- Compute-node `/tmp`: roughly 2-4 TB local, fast, unshared, and non-persistent; data is deleted after use.
- Read-only checks: `lfs quota -u han.zhou /l`, `du -sh "$HOME"`, and, only inside an allocated node where it exists, `du -sh /tmp/han.zhou`.

## CIAI

### Access

- Available only to regular MBZUAI faculty/PIs, one active CIAI account per PI.
- A PI may delegate access to students or postdocs via SSH keys and remains accountable for misuse.
- CIAI/CSCC access requires the quiz, score, proof, and HPC-team verification described above.
- A student using a PI-shared CIAI account must have the HPC team install the public key; never use `ssh-copy-id` for that account.
- From `unit1.rcl.micdz.cn`, connect with `ssh ciai-via-local` using the existing SSH alias and forwarding setup. Do not add key-management steps.

### GPU partition

- Partition: `long`
- QoS: `gpu-12`
- At most 72 hours per job
- At most 12 GPUs or 8 jobs per active account
- Minimum GPU request: 1
- Physical GPU density: 4 x A100 40 GB per node; never request more than 4 GPUs per node.

### CPU partition

- Partition: `cscc-cpu-p`, shared with CSCC
- QoS: `cscc-cpu-qos`
- At most 512 CPU cores, 2 running jobs, and 72 hours per job

### Hardware and storage

- GPU node: 128 physical CPU cores, 256 GB RAM, 4 x A100 40 GB, local NVMe scratch.
- CPU node: 128 physical CPU cores, 256 GB RAM, local scratch.
- `/l/users/han.zhou`: Lustre, 2 TB default quota; use for large datasets and checkpoints. Contact HPC before storing many small files.
- `$HOME`: 100 GB default quota; use for code, logs, and small files.
- Compute-node `/tmp`: fast, local, unshared, and non-persistent.
- Treat about 230 GB as the conservative allocatable system-memory ceiling per CIAI node. Do not request more without administrator confirmation.

## CAMD

### Access and networking

- Available only to regular MBZUAI faculty/PIs, one active CAMD account per PI. A PI may delegate via SSH keys and remains accountable.
- New access requires cluster-owner approval and an email containing only the SSH public key to `support.aicloud@core42.ai`. Core42 provides a User Request Form for digital owner approval.
- Login nodes: `172.27.112.247` and `172.27.112.248`. Use the separately confirmed CAMD username and private-key path with `ssh -i`; never point `-i` at `.pub` and never reveal the key contents.
- Compute and login nodes cannot access the internet by default. Repository/domain proxy whitelisting requires Core42 Support plus prior cluster-owner approval.

### Compute and software

- Approximately 125 worker nodes with 8 x AMD MI210 GPUs each.
- ROCm target: 6.3.
- PyTorch `cuda` device APIs generally map through HIP; distributed `backend="nccl"` maps to RCCL.
- Use `rocm-smi` instead of `nvidia-smi`; use `nvtop` rather than `nvitop`.
- FlashAttention has no prebuilt wheel in the documented environment; building from source is stateful and potentially expensive. Prefer PyTorch `scaled_dot_product_attention` when suitable.

### Slurm and storage

- The mandatory policy limits an active CAMD account to 3 jobs.
- CAMD uses partition `gpu`, but this skill does not contain a confirmed QoS, wall-time ceiling, or total GPU cap. CAMD submission is blocked until the user provides administrator-confirmed values; do not invent or omit them.
- The mandatory policy requires `gpu-debug-qos` for interactive/debug work, but this skill does not confirm that CAMD provides it. Do not start an interactive CAMD allocation until Core42 Support resolves this conflict.
- Each GPU node has 8 GPUs. Keep `--gres=gpu:<n>` at 8 or fewer per node.
- VAST home/shared storage path: `/vast/users/<confirmed-camd-username>`.
- The sample quota display shows about 1.5 TB soft and 2 TB hard, but treat it as illustrative; use `bash /etc/update-motd.d/99-vast-quota` for the account's current values.
- Do not invoke helper scripts in another user's directory without inspecting them and receiving explicit authorization.


## Jebel H200 testing

### Source, access, and expiry

- Source: the MBZUAI Research Infrastructure Team's H200 testing access email supplied by the user on 2026-09-22. These are temporary testing limits, not permanent Jebel entitlements.
- Access has been granted to `han.zhou`. Select this cluster when the user names Jebel, H200, or partition `h200`; otherwise keep CSCC as the default.
- Login: `ssh ciai-Jebel`. Use the user-specified existing `ciai-Jebel` SSH alias and preserve its configuration. Do not replace it with `ciai-via-local` or a direct-IP connection. The access email lists `han.zhou@10.127.79.251` as the endpoint; network reachability and authentication have not been tested by this skill update.
- Notice deadline, verbatim: **5:00 PM on 26 September**; testing account access will be revoked afterward. The notice requires users to **back up and remove their data before the deadline**.
- The email omits the year and timezone. For planning in this conversation, provisionally interpret it as **2026-09-26 17:00 Asia/Dubai (UTC+04:00)** based on the current date and institution location; this is an assumption, not an administrator-confirmed timestamp. Confirm it with the user or HPC team before a schedule depends on the exact cutoff.
- Recheck the current date before remote use. At or after the provisional cutoff, treat this grant as expired unless the user provides renewed access and limits. Do not carry these testing entitlements forward to a later year.
- Plan training completion, checkpoint export, verified backup outside Jebel, and authorized removal before expiry. The 8-hour job limit does not extend access. Include queue delay and time for backup/cleanup; if completion before the cutoff cannot be established, do not submit the job.

### Slurm limits and required project ID

- Partition: `h200` (always explicit).
- Required Project ID: **`h200test2609`**, supplied exactly as `#SBATCH --comment="h200test2609"` or `sbatch --comment="h200test2609"`. Keep the value unchanged; do not substitute `--account` or infer an account/QoS from it.
- Maximum GPU allocation: **2 H200 GPUs in total per user**, across jobs, not 2 per job. Use `--gres=gpu:1` or `--gres=gpu:2` as appropriate; multi-node requests must also stay within 2 GPUs total and verified node capacity.
- Maximum jobs: **2 total, counting both pending and running jobs**. Before submission, inspect the user's existing Jebel jobs and GPU allocations. Two occupied job slots block another submission even if one or both jobs are pending. Job arrays must fit this job-count limit as well.
- Maximum wall time: **8 hours per job** (`--time=08:00:00` or less).
- The supplied administrator example omits `--qos`; omit it for Jebel batch jobs unless an administrator supplies a required value. Do not copy `cscc-gpu-qos`, `gpu-12`, or `gpu-debug-qos` from other clusters.
- The supplied example uses 1 node, 1 task, 8 CPUs, 40 GB system RAM, 1 GPU, and 4 hours. These are example request sizes, not CPU/RAM/node limits or mandatory allocations.

### Storage, software, and unconfirmed features

- The notice does not specify storage paths/quotas, node CPU/RAM capacity, H200 memory size, GPUs per node, Conda/module paths, internet availability, a CPU partition, or interactive/Jupyter policy. Do not inherit these from CSCC/CIAI/CAMD.
- When the user authorizes remote preparation, use lightweight read-only discovery to identify usable project/storage paths, software, partition/node capacity, and existing jobs. Resolve any missing value actually needed for a write or allocation with the user or HPC team; an unspecified QoS alone does not block the documented batch workflow.
- Use batch jobs for the documented training/testing workflow. Confirm Jebel's interactive/Jupyter rules before starting those services; do not invent a debug QoS.
- Keep checkpoints recoverable outside this temporary account. The expiry notice requires removal, but does not authorize the skill to delete data without an exact user-approved cleanup scope. See [policy-and-safety.md](policy-and-safety.md).
