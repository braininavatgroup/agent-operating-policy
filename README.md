# Agent operating policy

An operating policy for coding agents, plus the skills and Claude Code hooks that implement it. Extracted from a one-person company's production setup, minus the company-specific parts.

## What is in here

- `policy/`. Six markdown sources. `universal.md` says when an agent may act without asking: the real-blockers test, the decision ladder, and ticket-derived authority. `coding.md` covers investigation, browser routing, the verification ladder, and git. `orchestration.md` sets one mutation owner per workstream. `review.md` is the code review standard: what a finding must carry, and three severities. Two short files route per harness.
- `generated/`. `CLAUDE.md` and `AGENTS.md`, rendered from those sources; never hand-edited.
- `skills/`. orchestration, handoff, brainstorm, clean-my-ai-harness, unslop, parallel-web-verification, wizard.
- `hooks/`. A PreToolUse guard that refuses unmanaged browser launches from Bash, a SessionEnd checklist, and an example settings block.
- `tools/`. Renderer, installer, tests.

## Policy as source

The harness files are build output. `tools/adapters/render_policy.py` concatenates the harness routing file with the four shared sources and stamps the result with a generation hash, the SHA-256 of the source bytes. `check_generation.py` fails when a committed rendering differs from its sources; CI runs it on every pull request and on pushes to `main`. A downstream repository can vendor a rendering and pin the expected generation, so a stale copy fails its own build instead of drifting.

Skills use the same idea. A skill that must name its harness writes `{{HARNESS_NAME}}`, `{{AGENT_INSTRUCTIONS_FILE}}`, or `{{SKILLS_DIR}}`. `render_skills.py` substitutes per harness and rejects any other brace-wrapped uppercase name, so a typo cannot ship. `install_skills.py` copies the committed `skills/` tree from HEAD into a runtime directory, and refuses to overwrite a directory it did not create.

## Try it in an isolated directory

This is a starting point for people who already use coding agents and want to inspect or adapt their operating rules. It assumes one operator and includes a broad ticket-authority model. Read [policy/universal.md](policy/universal.md), especially "Production authority", before adopting it. Markdown instructions and shell hooks do not replace credential isolation or your agent runtime's permission controls.

The tools require Git and Python 3.12 or newer. The Claude hooks use Bash and `python3`. Clone the repository, then render a skill copy outside your checkout before changing a live agent setup:

```sh
git clone https://github.com/bradleyberkman/agent-operating-policy.git
cd agent-operating-policy
python3 tools/adapters/check_generation.py
python3 tools/adapters/install_skills.py --harness codex --output-dir ../policy-preview-codex
```

Use `--harness claude` and a different output directory to inspect the Claude version. The installer reads committed skill content from `HEAD`, so commit your source changes before trying an adapted version. It refuses an existing nonempty output directory it did not create. It also refuses a refresh that would remove locally added files, but it can replace edits to paths that belong to the projection. Keep your canonical edits in `skills/`.

## Adopt the parts you want

Back up your existing instruction files, settings, hooks, and skills first. Compare the generated policy with your current instructions and reconcile the rules you want to retain. Copying a generated file over your global instructions replaces them for every project that loads that file.

For Claude Code, the generated policy goes in `~/.claude/CLAUDE.md`. Put the reviewed hook scripts in `~/.claude/hooks/`, preserve their executable permissions, and merge [hooks/settings.example.json](hooks/settings.example.json) into your existing `~/.claude/settings.json`. The example adds a Bash browser-launch guard and a session-end checklist. Review both scripts before enabling them.

For Codex, the generated policy goes in `~/.codex/AGENTS.md`. The Claude hook settings do not configure Codex hooks.

After reviewing the isolated projection, run the installer with `--harness claude --output-dir ~/.claude/skills` or `--harness codex --output-dir ~/.agents/skills` only if that destination is suitable for this installer. If you already maintain skills there, keep the isolated projection and copy the selected rendered skill directories into your existing setup yourself.

To undo adoption, restore your backups and remove the hook entries and skill directories you added. The installer does not have an uninstall command.

## Contributing

Edit the owning files in `policy/` or `skills/`, never the generated renderings. Re-render with
`python3 tools/adapters/render_policy.py` and commit the result, then run the same checks CI does:

```sh
python3 tools/adapters/check_generation.py
python3 -m unittest tools/tests/test_policy_tools.py tools/tests/test_skill_render.py
python3 skills/clean-my-ai-harness/tests/test_harness_evidence.py
```

The authoritative list is [.github/workflows/ci.yml](.github/workflows/ci.yml). For a policy proposal, explain the agent behavior it changes and give a concrete case where that behavior helps. Keep company identifiers, credentials, and private transcripts out of examples and issue reports.

Pull requests in this repository squash-merge after the required `ci` check passes on a branch
that is up to date with `main`.

## What was left out

Anything that only makes sense inside one company: skills bound to its CRM, ticket tracker, reporting pipelines; vendored third-party skills, which have their own upstreams; and the names, identifiers, and paths of the people and systems involved. "The operator" throughout means the one person whose judgment the policy defers to.

The wizard skill is Matt Pocock's, MIT, included with its license file.

Copyright 2026 Bradley Berkman. MIT.

<!-- Mac/personal environment proof, BIV-272 -->

<!-- Conductor/personal merge-leg proof under the owner-scoped PAT, BIV-272 -->
