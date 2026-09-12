# AstraUpdate

[Deutsch](README.md) | **English**

**Review and improve existing skills and Markdown agent instructions with Codex.**

AstraUpdate provides the **`skill-prompt-optimizer`** skill. It guides Codex through reading existing instructions, evaluating their meaning, and editing the original files directly. Backups are created before changes, and a report records what changed and what remains unresolved.

The project is based on Eric Provencher's OpenAI article [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra), published on September 11, 2026. This is an independent implementation, not an official OpenAI product.

## What does it improve?

The skill checks whether activation conditions are too broad, references are loaded unnecessarily for every task, or rigid procedures get in the way of the actual work. It can organize lengthy instructions more effectively and remove unnecessary approval or stopping loops while preserving domain requirements and intentional boundaries.

Example of an activation condition:

```text
Before: Always use this CSV import skill whenever data, files, or documents are mentioned.
After: Use this skill for a local import preview of orders from CSV.
```

The agent decides whether a change is useful based on the actual content. There is no fixed reduction target and no blanket replacement of words such as “always” or “must.”

## Requirements

- Codex with access to the installed skill and the local files to review.
- Write permissions for files that should actually be edited.
- Optionally, Python **3.9 or later** for the bundled helper script. No additional Python packages are required.
- Git for the installation commands below. Alternatively, download the repository as a ZIP archive if you have access to it.

The skill does not provide model access or switch the active model. Its recommendations target Astra, while instructions shared with other models must continue to meet their domain requirements.

## Installation

### Through Codex

Give Codex this request:

```text
Install the skill from https://github.com/zinolang-cell/astraupdate,
subdirectory skill-prompt-optimizer, into my personal skills directory.
```

For a private repository, the GitHub connection being used must have access to it.

### Manually on Windows / PowerShell

Run these commands from a working directory. They deliberately stop if the skill is already installed rather than overwriting it.

```powershell
git clone https://github.com/zinolang-cell/astraupdate.git
if ($LASTEXITCODE -ne 0) { throw 'Clone failed.' }

$skillHome = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME 'skills'
} else {
    Join-Path $HOME '.codex\skills'
}
$skillTarget = Join-Path $skillHome 'skill-prompt-optimizer'
if (Test-Path -LiteralPath $skillTarget) { throw 'Skill already exists: back up and compare before updating.' }
New-Item -ItemType Directory -Path $skillHome -Force | Out-Null
Copy-Item -LiteralPath '.\astraupdate\skill-prompt-optimizer' -Destination $skillTarget -Recurse
```

### Manually on macOS / Linux

```sh
git clone https://github.com/zinolang-cell/astraupdate.git && (
  skill_home="${CODEX_HOME:-$HOME/.codex}/skills"
  skill_target="$skill_home/skill-prompt-optimizer"
  if [ -e "$skill_target" ]; then
    echo "Skill already exists: back up and compare before updating."
    exit 1
  fi
  mkdir -p "$skill_home" && cp -R ./astraupdate/skill-prompt-optimizer "$skill_target"
)
```

After installation, check that `skill-prompt-optimizer/SKILL.md` exists inside your personal skills directory. If the skill does not appear in the current session, open a new Codex session or restart Codex.

## Using the skill in Codex

### Review and apply changes directly

```text
Use $skill-prompt-optimizer to review all my personal skills and Markdown
agent instructions within the available scope and apply suitable improvements
directly. Create backups and a change report.
```

**Invoking the skill without further qualification also defaults to applying changes.** It is not a report-only operation.

### Review without editing source files

```text
Use $skill-prompt-optimizer for an audit without changes.
Review my personal skills and this project's AGENTS.md.
```

“Review only” and “dry run” also mean that source files should remain unchanged. An inventory or report may still be created.

### Limit the scope to one project

```text
Use $skill-prompt-optimizer exclusively for the skills and Markdown agent
instructions under C:\Projects\MyProject.
Apply suitable improvements directly and document the changes.
```

These examples are **messages to Codex**, not terminal commands. Explicitly name the paths of any additional projects you want included.

## How does a review work?

1. **Establish scope:** Codex finds skills through the skill catalog and the filesystem. An explicitly restricted request takes precedence. A comprehensive request includes personal skill directories, existing global agent instructions, and the current or named project.
2. **Understand the content:** Codex reads descriptions, instructions, and relevant references. Discovering a file does not count as reviewing its content.
3. **Evaluate changes:** Codex distinguishes useful domain knowledge from unnecessary process requirements. In documents containing both instructions and other material, it focuses on the agent instructions.
4. **Back up originals:** Current contents are saved byte for byte before editing. Existing local changes are part of the starting state.
5. **Edit directly:** Useful changes are made where they belong. Linked references may be introduced when helpful; an identical optimization block is not appended to every file.
6. **Verify and report:** Codex reads the results back, checks diffs, references, and relevant behavioral cases, and records changed, unchanged, and unresolved files.

Results depend on the model, context, and quality of the original instructions. No particular token savings or measurable quality improvement is guaranteed.

## Which files are included?

| File or area | Treatment |
| --- | --- |
| Personal `SKILL.md` files and related instructional references | Review the content and apply suitable edits in implementation mode |
| `AGENTS.md`, `AGENTS.override.md`, and Markdown prompts | Review instructions while respecting their scope |
| READMEs, architecture documents, and other domain documents | Distinguish agent instructions from domain content |
| `agents/openai.yaml` | Check for conflicting metadata when behavior changes |
| System skills and active plugin cache versions | Review; by default, report findings and proposed changes without overwriting cache files |
| Other projects | Include when explicitly or unambiguously covered by the request |

Contracts, customer data, historical logs, and domain examples are not rewritten just because they are Markdown files. Budget limits, privacy requirements, production approvals, and necessary technical procedures are preserved. An audit does not execute the workflows it reviews and does not authorize deployments, campaign changes, or external data transfers.

## The Python helper

[`audit_files.py`](skill-prompt-optimizer/scripts/audit_files.py) handles deterministic file operations. **It does not rewrite the reviewed originals or call a language model.** Codex performs the semantic optimization using the skill's instructions.

| Command | Purpose |
| --- | --- |
| `inventory` | Record Markdown files: path, category, managed status, byte count, SHA-256, and encoding |
| `snapshot` | Save explicitly selected text files as byte-exact `.bak` files with a manifest |
| `diff` | Compare saved originals with current files and produce a unified diff |

### Example: manual file operations

Run the following terminal commands from the repository directory. Replace the example paths with real paths on your machine. On some systems, Python is called `python3` or `py`.

```sh
mkdir .skill-optimizer-runs
python skill-prompt-optimizer/scripts/audit_files.py inventory --root /path/to/project --out .skill-optimizer-runs/inventory.json
```

Repeat `--root` to select multiple roots. `--file` adds individual Markdown files; `--managed-root` adds a root whose entire contents are marked as managed. No whole-disk search is performed implicitly.

To prepare a backup, create a UTF-8 file named `.skill-optimizer-runs/selection.json` containing the **absolute** paths of the existing files you want to save:

```json
[
  "/path/to/project/AGENTS.md",
  "/path/to/skills/my-skill/SKILL.md"
]
```

On Windows, an absolute path could be `C:/Projects/MyProject/AGENTS.md`. Then run:

```sh
python skill-prompt-optimizer/scripts/audit_files.py snapshot --files .skill-optimizer-runs/selection.json --out .skill-optimizer-runs/snapshot
```

After Codex or a person has made the actual edits:

```sh
python skill-prompt-optimizer/scripts/audit_files.py diff --run .skill-optimizer-runs/snapshot --out .skill-optimizer-runs/changes.diff
```

Inventory and diff outputs require existing parent directories and new output filenames. A snapshot requires a destination directory that does not yet exist. Use new names or separate run directories for subsequent runs.

### Limitations and exit codes

- Supported encodings are UTF-8, UTF-8 with a BOM, and UTF-16 with a BOM. Other or ambiguous encodings are reported.
- Symlinks and Windows junctions are not followed. After verification, required targets can be selected using their actual paths.
- Inventory excludes directories such as `.git`, `node_modules`, Python virtual environments, build directories, and `.skill-optimizer-runs`.
- Exit code `0` indicates success. Code `1` indicates processing errors, including missing current files during `diff`. Invalid CLI arguments may produce code `2`.
- An inventory may be available despite partial errors. Always inspect `errors` and `skipped`.
- A snapshot covers selected existing files. Newly created references must also be documented in the report and change record.

## Backups, reports, and restoration

Run artifacts are stored outside skill directories in a writable location under `.skill-optimizer-runs/<run-id>`. The manifest maps each backup to its original file and checksum.

A report records the search scope, source version, actual content review, changes, unchanged files, verification, and remaining limitations. “All reviewed” means all files within the documented scope, not automatically every file on the computer.

For restoration, Codex can use the manifest to copy back the selected originals. Changes made since the audit must be considered first. The helper does not provide automatic restoration or run a Git reset. Backups and reports may contain internal information; the included `.gitignore` excludes run artifacts from normal Git staging.

## Repository structure

```text
astraupdate/
├── README.md
├── README.en.md
├── LICENSE
├── tests/
│   └── test_audit_files.py
└── skill-prompt-optimizer/
    ├── SKILL.md
    ├── LICENSE
    ├── agents/openai.yaml
    ├── references/
    │   ├── pruefgrundlage.md
    │   └── dateiverarbeitung.md
    └── scripts/audit_files.py
```

`SKILL.md` defines the workflow for Codex. `pruefgrundlage.md` records the article's guidance and source date; `dateiverarbeitung.md` explains helper commands. `agents/openai.yaml` supplies the display name and example invocation. A license copy is included inside the skill directory so it remains available when the skill is installed separately.

`SKILL.md`, including its activation description, is written in concise English. Supporting reference documents and UI metadata remain in German. The skill instructs the agent to respond in the user's language.

## Tests

From the repository directory:

```sh
python -m unittest discover -s tests -p "test_*.py" -v
```

The tests check, among other things, that inventory leaves originals unchanged, backups preserve exact bytes, exclusions work, and diffs expose changes and errors. Platform-specific tests may be skipped when the necessary permissions are unavailable. These tests verify file operations, not the quality of every revision made by a model.

To evaluate the skill's behavior, also use an isolated example project: try a relevant request and an unrelated request, and check that domain requirements are preserved.

## Updates and license

To update, run `git pull --ff-only` in the cloned repository, back up your installed version, and compare it with the new version. Then copy the desired updated skill files into your skills directory. There is no automatic update process.

The code and original instructions in this repository are available under the [MIT License](LICENSE). The linked OpenAI article is an external source and is not relicensed by this project.
