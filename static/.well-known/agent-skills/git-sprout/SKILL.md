---
name: git-sprout
description: Create git worktrees that share disk blocks with an existing checkout instead of copying the whole tree. Use when creating a worktree (`git worktree add`), when worktrees are eating disk, when a harness or script spawns one worktree per task or per agent, or when a large repository makes every checkout expensive. On the Linux kernel one worktree drops from 1816 MB to 36 MB.
---

# git-sprout

[`git-sprout`](https://sprout.alltuner.com) is a drop-in replacement for
`git worktree add`. It materialises the new worktree with filesystem
copy-on-write clones of a checkout you already have, instead of inflating every
blob out of the object store into fresh blocks. The clone shares disk blocks
with the source until something writes to them.

```bash
git sprout add ../myrepo-feature -b feature
```

Same flags, same stdout, same exit codes, same hooks, same resulting files and
index as `git worktree add`. **The pitch is disk, not speed** — on the Linux
kernel it is 1816 MB → 36 MB with no meaningful wall-clock difference. Reach for
it whenever something creates worktrees repeatedly: one per task, per agent, per
CI job.

## Invocation

```bash
git sprout add <path> [-b <new-branch>] [<commit-ish>]   # or: git worktree-fast add
```

Anything `git worktree add` accepts, `git sprout add` accepts. Any flag or
combination it does not fully understand is not an error: it hands the whole
command to git and exits with git's status.

Only `add` is accelerated. Other subcommands (`list`, `remove`, `prune`, …) pass
straight through to git, so `git sprout list` and `git worktree list` are the
same thing. There is no reason to route them through sprout.

## Install

```bash
brew install alltuner/tap/git-sprout      # macOS / Linux
cargo install git-sprout
```

Or a binary from [the releases page](https://github.com/alltuner/git-sprout/releases).

## When it actually shares blocks

Two things must be true, and sprout checks both itself:

1. **The filesystem supports block cloning** — APFS on macOS; btrfs, XFS with
   reflinks, or bcachefs on Linux; a ReFS volume or Windows 11 Dev Drive on
   Windows. On ext4, NTFS and anything else, it runs plain `git worktree add`.
2. **The repository does not convert files on checkout** — a file can only be
   shared when checking it out would not rewrite its bytes. `core.autocrlf`
   (on by default in Git for Windows) or `* text=auto eol=crlf` means there is
   nothing to share, and sprout passes through to git.

Neither case is an error and neither needs handling: you get a correct worktree
either way. Never gate a script on "is this filesystem supported" — just call
`git sprout add` and let it decide.

## The one gotcha that silently disables it

**A repository that arrived as a copy accelerates nothing until its stat cache is
rebuilt.** sprout clones a file only when git already considers the source copy
unmodified, which git decides from the inode, size and mtime in the index. A
`cp -r`, an rsync, a container image layer, a restored CI cache or an unpacked
tarball gives every file a new inode and a fresh mtime, so every entry looks
modified even though every byte is identical. Nothing is shared, the worktree is
still correct, and there is no error to notice.

Run this once in the source repository first:

```bash
git update-index --refresh
```

This matters most in exactly the places worktrees get created automatically: CI
runners with restored caches, containers, and freshly unpacked checkouts.

## Confirming it worked

`SPROUT_STATS=1` prints one JSON line to **stderr**:

```console
$ SPROUT_STATS=1 git sprout add ../wt -b feature
sprout-stats: {"checked_out_by_git":0,"clone_backend":"apfs","cloned":1,"cloned_directories":0,"fallback_reason":null,"fell_back":false,"skipped":0,"source":"/path/to/repo"}
```

- `cloned` — files that shared blocks. `0` with `fell_back: false` is the stat
  cache gotcha above.
- `fell_back` / `fallback_reason` — it ran plain `git worktree add`, and why.
- `clone_backend` — `apfs`, `reflink`, `none`.
- `checked_out_by_git` — files sprout could not share, left to git.

`SPROUT_STATS_FILE=<path>` writes the same JSON to a file instead, for scripts
that need to keep stderr clean.

Do not measure the saving with `du` on the worktree; it reports the logical
size, not the blocks actually allocated. Use the stats line, or the
filesystem's own sharing accounting (`btrfs filesystem du`, `du --apparent-size`
comparisons will mislead you).

## Turning it off

```bash
SPROUT_DISABLE=1 git sprout add ../wt -b feature   # forces plain git worktree add
```

Useful to A/B a suspicious result, or to rule sprout out while debugging
something else.

## Making it automatic

Git ignores an alias that shadows a builtin, and builtins never go through
`GIT_EXEC_PATH` or `PATH`, so `git worktree add` cannot be redirected by
configuration. A shell function covers what a human types:

```bash
# bash / zsh — ~/.bashrc, ~/.zshrc
git() {
  if [ "${1:-}" = worktree ] && [ "${2:-}" = add ]; then
    shift 2
    command git sprout add "$@"
  else
    command git "$@"
  fi
}
```

A shell function does **not** cover editors, worktree managers, CI jobs or agent
harnesses — they spawn `git` themselves and never see it. Covering those needs a
`git` wrapper script placed ahead of the real git on `PATH`, which is a
deliberate, user-installed thing. Do not install one on a user's machine without
asking.

## Gotchas

- **Cloned files keep the source checkout's mtimes**, not the moment the
  worktree was created. Nothing in git depends on this, but `make` and anything
  else driven by modification times can behave differently.
- **Less output than git**: on a big repository `git worktree add` prints a
  progress meter while writing files. sprout has almost nothing left to write,
  so git never starts one. Fewer lines means less happened, not something wrong.
- **Untracked and ignored files are not copied** — exactly as `git worktree add`
  does not copy them. sprout is not a way to duplicate a dirty tree.
- **Your repository's configuration is never modified.**
