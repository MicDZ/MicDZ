# Policy and safety rules

Read this file before any task that may change local or remote state. These are the complete mandatory policy and safety rules for this skill.

## Rule precedence

Apply rules in this order:

1. Mandatory rules in this file.
2. Cluster-specific limits in [clusters.md](clusters.md).
3. Workflow gates in [workflows.md](workflows.md).
4. Examples and user-provided scripts.

If two instructions conflict, use the stricter interpretation and tell the user. If this skill does not resolve a value needed for a state-changing action, stop and ask the user or the named administrator.

The Jebel H200 testing email supplied by the user adds the cluster-specific access window, resource caps, and mandatory project comment in [clusters.md](clusters.md). CSCC/CIAI-specific access, QoS, storage, and software settings do not apply to Jebel. Shared safety practices below remain this skill's operating safeguards; the email does not independently confirm every older cluster rule.

Normalized policy decisions:

- `salloc` is forbidden even if an example or cheat sheet contains it.
- A CIAI DDP example allocates 3 GPUs per node but launches 4 processes per node and describes 12 GPUs across 3 nodes. Reject or repair this mismatch before use.
- OpenSSH identity selection must use a private-key path, never a `.pub` path. For the configured CIAI account, no `-i` flag is needed because `ssh ciai-via-local` uses the existing SSH configuration.
- A CSCC example comment says its QoS enables up to 8 GPUs, while the policy and partition page limit the account to 4 GPUs. Enforce the 4-GPU limit.
- Two Conda initialization paths are recorded. Check the actual readable path; do not modify shell startup files to guess.

## Mandatory cluster rules

- Do not run jobs or user code directly on login nodes.
- CIAI/CSCC login-node user slices are limited to 1 CPU core, 1,000 tasks, and 4 GB RAM.
- Do not submit sleep-only jobs that reserve unused resources.
- Use `gpu-debug-qos` for interactive and debugging jobs on CSCC/CIAI.
- Do not use `salloc`; use `srun` or `sbatch`.
- Do not leave idle bash sessions open.
- On CSCC/CIAI, never use `CUDA_VISIBLE_DEVICES` to access more GPUs than Slurm allocated. This can cause account termination.
- Do not use `--exclusive` with `srun` or `sbatch`.
- Slurm email flags such as `--mail-type` and `--mail-user` are unavailable.
- If a dataset has many small files on `/l`, contact `hpc.admins@mbzuai.ac.ae` before placing it there.
- Users must back up their own data. Cluster data is not a backup.
- Unneeded data should be cleaned up after training, but this skill must not delete it automatically.
- Special compute requests, custom node images, major storage increases, or exclusive reservations go to `hpc.admins@mbzuai.ac.ae`.

Policy violations may cause temporary suspension; repeated violations may terminate the account.

## Never execute automatically

Do not execute any of these actions automatically:

- `rm ...` or any deletion command.
- `scancel -u han.zhou`, `scancel -u <name>`, or another broad cancellation.
- `echo ... >> ~/.bashrc` or another shell-startup modification.
- `cat > file`, shell redirection that could overwrite a file, or an unreviewed in-place edit.
- An unreviewed shared script such as `/vast/users/guangyi.chen/slurm_tools/*.sh`.
- `ssh-copy-id`, key generation, key replacement, key inspection, or `authorized_keys` modification. The configured CIAI key already works.
- `pip install`, `conda create`, repository cloning, or downloads without explicit authorization and a chosen environment/path.
- `sbatch`, stateful `srun`, file upload, `scp`, `rsync`, or an SSH command when the user asked only to plan or review.

Generate or review commands when useful, but keep them inert until the user authorizes the state change.

## Narrow action gates

### SSH keys

- Only the `.pub` file is shareable. It should be one line beginning with a public-key type such as `ssh-ed25519`.
- Never read or display the private-key contents. A private OpenSSH key begins with `-----BEGIN OPENSSH PRIVATE KEY-----`.
- For CSCC/CIAI, the configured account is `han.zhou@ciai.mbzuai.ac.ae`; use the existing SSH alias and forwarding setup. Use the exact command `ssh ciai-via-local` when connection is authorized.
- Do not generate, copy, replace, or inspect keys unless the user explicitly changes scope to key troubleshooting.
- A student accessing a PI-shared CIAI account must send the public key to the HPC team; do not use `ssh-copy-id`.
- Jebel temporary access is granted for `han.zhou@10.127.79.251`. Use `ssh ciai-Jebel` through the user-specified existing SSH alias when authorized; preserve its configuration and do not add key-provisioning steps.
- CAMD access is provisioned by Core42 Support after cluster-owner approval; do not self-install keys there.
- If a private key is compromised, stop. Do not delete anything automatically. Explain that the key must be revoked and replaced, identify exact affected files/accounts, and obtain explicit approval before any local removal or remote key change.

### Job submission

Before `sbatch` or a stateful `srun`:

1. Validate the target cluster against [clusters.md](clusters.md).
2. Lint for forbidden flags and resource mismatches. For Jebel, also check access expiry, the exact `h200test2609` comment, the 8-hour wall-time cap, and the per-user totals of at most 2 GPUs and 2 pending-plus-running jobs.
3. Show the exact script and submission command.
4. Require a user request that clearly authorizes submission.
5. Capture the returned job ID and verify it with `squeue --me` or `squeue -j <job-id>`.

### Cancellation

- Prefer diagnosis and checkpointing before cancellation.
- List the user's jobs with `squeue --me` and resolve the exact numeric job ID.
- `scancel <exact-job-id>` is destructive. Execute it only after the user explicitly identifies or confirms that job.
- Never broaden a single-job cancellation into account-wide cancellation.

### Cleanup and overwrites

- First list exact candidate paths, sizes, ownership, and backup status with read-only commands.
- Do not delete checkpoints, datasets, environments, logs, or scratch files automatically.
- Jebel testing requires backup and removal before access expires. Plan that work in advance, verify the backup outside Jebel, and obtain authorization for exact removal paths; the deadline alone is not permission to delete.
- Do not overwrite an existing remote file without showing the target and obtaining authorization.
- Remember that compute-node `/tmp` is non-persistent. Stage only reproducible or backed-up data there.

### Software installation

- Keep environments isolated. Do not modify shared software.
- Avoid automatic `.bashrc` edits; source and activate Conda explicitly in the job script.
- Do not run framework tests or builds on login nodes. If installation/building is resource-intensive, perform it through an appropriate Slurm allocation or ask HPC support for guidance.
- On CAMD, internet access is disabled by default. Do not attempt bypasses; request domain whitelisting through Core42 Support with cluster-owner approval.
