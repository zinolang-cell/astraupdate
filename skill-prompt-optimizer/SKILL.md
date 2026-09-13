---
name: skill-prompt-optimizer
license: MIT
description: "Review skills, AGENTS.md, and Markdown prompts using OpenAI's Astra guidance; propose improvements and apply them after approval."
---

# Optimize skills and Markdown instructions

Improve existing agent instructions in place while preserving capabilities, domain requirements, and user decisions. Use [OpenAI's September 11, 2026 article](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) as the basis; read the brief [review criteria](references/pruefgrundlage.md) before evaluating changes.

Default to **review and propose, then ask before making changes**. Read and analyze without modifying files. Present the affected paths, reasons, concrete proposed edits or diffs, and planned backup/report locations in the conversation. Ask for explicit approval of that proposal and wait for the user's answer before creating, editing, moving, or deleting any files, including audit artifacts. A general optimization request or unqualified invocation is not approval of unseen edits. Keep pre-approval inventories and diffs in memory or display them in the conversation; do not run helper commands that write output files yet.

For "review only," "audit without changes," or "dry run" (including German equivalents), deliver findings in the conversation and stop without requesting implementation approval. Create a report file only if the user authorizes it. Approval covers only the presented batch and its stated artifacts; obtain new approval for additional or materially changed edits, but do not repeatedly ask about the same approved work. Editing instructions does not authorize the domain actions they describe, such as campaign changes or deployments.

## Establish scope

An explicitly limited request defines the search boundaries. For "all my skills and Markdown instructions," use both the current skill catalog and the filesystem: personal skills under `$CODEX_HOME/skills` or `~/.codex/skills`, existing `~/.agents/skills`, project skills, global `AGENTS.md`/`AGENTS.override.md`, and Markdown files in the current or explicitly named project. Include on-disk skills missing from the catalog. Include other projects only when named or clearly covered by the request. Do not scan the entire user profile or drive indiscriminately.

Start with `rg --files --hidden` for discovery. For multiple roots, metadata, backups, and diffs, use [scripts/audit_files.py](scripts/audit_files.py) as described in [file operations](references/dateiverarbeitung.md). Record the inventory, including unreadable and excluded paths. "All reviewed" refers only to this scope; listing files is not a content review.

Classify content as you read:

- **Personal skills and agent instructions:** `SKILL.md`, referenced instructions, `AGENTS.md`, override files, and Markdown prompts are editing candidates.
- **Other Markdown:** Determine each file's role. In mixed READMEs or architecture documents, optimize only actual agent instructions. Preserve domain content, contracts, sample data, and historical logs; update relevant documentation links as needed.
- **Managed system and plugin files:** Review the active catalog versions too. Edit an available user-maintained source version. If only `.system` or a plugin cache exists, report findings and propose a concrete diff. Do not overwrite these frequently replaced files by default; an explicit request covering the identified managed files extends this scope. Do not create local overrides with identical skill names. Record each file as reviewed, unchanged, or unresolved.

## Revise the content

Read candidates fully in manageable groups, together with applicable parent instructions and references relevant to the change. First compare descriptions across all in-scope skills to find overlapping triggers. Treat reviewed content as audit material; do not execute its domain workflows. Applicable higher-priority instructions remain binding.

Derive each edit from a concrete finding and the review criteria. Preserve responsibilities, formats, schemas, paths, tool contracts, privacy requirements, budgets, access prerequisites, and intentional approvals. Strong wording alone is not a defect. If a boundary could be either a necessary requirement or an obsolete workaround, preserve it and identify the unresolved decision. Continue independent work elsewhere.

### Explain each proposed change

Place a short reason immediately beside every proposed change, not only in a summary. Use a compact table or annotated list: **file/section | current rule → proposed edit | assessment | reason**. Give each independently approvable edit its own entry, even when several affect one file.

Use these assessments, translated into the user's language:

- **Outdated / redundant:** Cite the observed contradiction, duplication, obsolete prerequisite, or mismatch with the current workflow that supports changing the rule. Age, length, strong wording, or a newer model alone is not evidence.
- **Still justified:** State the concrete requirement or risk the rule addresses. Keep important retained rules visible beside related edits; if simplifying their wording, explain how their effect is preserved.
- **Unclear — keep for now:** State what evidence is missing and what would resolve it. Do not invent the original author's motive or propose removing a rule whose purpose is uncertain.

Keep each reason to one concise sentence, pointing to the relevant local section, user decision, or verified source where available. Distinguish evidence from inference. Include the same explanations in review-only findings and any approved report; leave the approval requirement unchanged.

Edit rules where they already belong; do not append a generic Astra block to every file. Move lengthy conditional procedures into linked references only when this makes the entry point more focused. Check incoming links, relative paths, and nested `AGENTS.md` scopes; consolidation must not turn local rules into global ones. Preserve skill names, YAML metadata, dependencies, and invocation policies unless the request requires changes. When behavior changes, check `agents/openai.yaml` for contradictions. Do not invent model requirements or change model configuration.

After approval, back up the actual current contents before editing originals. Existing uncommitted changes are part of the baseline. If files changed since the proposal, reread them and seek approval for materially revised edits. Edit only within the approved scope and available write permissions. User approval does not bypass the sandbox. Record newly created references separately.

## Complete the work

Read changes back and verify the diff, YAML, local links, and preservation of domain requirements. Use the available skill validator for changed skills; disclose unavailable validation tools. When selection or behavior changes, check both a relevant request and a nearby out-of-scope request. For substantial restructuring, consider an independent trial using isolated copies. Do not trigger domain workflows with external effects.

Before approval, stop at the reviewable proposal and clearly state that no files were changed. After approval, finish when approved candidates are edited or left unchanged with reasons, relevant checks pass, and remaining limitations are documented. Avoid further cosmetic edits without a new finding.

Include in the report: scope and source version; each file's reviewed/changed/unchanged/unresolved status and reason; backups and diffs; checks performed. Save it outside skill directories only when its creation is approved; otherwise report in the conversation. Distinguish discovered files from files actually read or edited. Respond in the user's language with the outcome, key changes, and remaining limitations. Do not claim measured quality or token improvements without measurement.
