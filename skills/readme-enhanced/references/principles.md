# What a good README does

## The five questions, in this order
1. **What is it?** One or two sentences: "X is a <category> that <does Y> for <audience>."
2. **Why this one?** The problem it solves and how it differs from the obvious alternative. Skip if there is none.
3. **Does it work?** Evidence: a screenshot, a terminal recording, real output, a benchmark with its method.
4. **How do I try it?** Install and one command or code sample that works in two minutes.
5. **Where next?** Links to docs, examples, issues, contributing.

## First-screen test
About 25 lines, no scrolling: title, pitch, a visual or a result, and the start of install. If a reader still cannot say what the project does, rewrite the pitch.

## Writing
- Concrete beats adjectives. "Renders a 100-slide deck in 4 seconds (M2, see benchmark)" beats "blazing fast".
- Present tense, second person, one idea per paragraph, sentence-case headings, consistent terms.
- Be honest about maturity (stable, beta, experimental) and platform support. No promises about the future.
- Explain acronyms once. Name the audience's task, not your architecture.

## Commands
- One block per step, no `$` prompts, the working directory stated (`cd project`), versions where they matter.
- Show the expected output under the command. Test the block in a clean directory.
- Prefer `pip install .` / `npm install` from source in a README, and add the registry line only if the package is published.

## Evidence and diagrams
- Screenshots and GIFs: keep under 1 MB, add alt text. A terminal recording (VHS, asciinema) beats a screenshot of text.
- Benchmarks and charts: state data, hardware and method; generate charts with `dataviz-enhanced`.
- Diagrams: Mermaid code blocks render on GitHub; keep them to about 10 nodes.

## Links and badges
Relative links for files in the repo; no dead links; anchors must match headings. Badges only where a reader acts on them (licence, CI status, version, coverage); at most five, one line, under the title.

## Anti-patterns
A wall of badges; a README that is the whole manual (move it to `docs/`); marketing copy; an "Introduction" heading with nothing in it; a table of contents on a 60-line README; install steps that no longer work; screenshots of text; generated filler ("This project aims to..."); a licence named in the README but missing from the repo.

## Companion files
LICENSE (required to be open source), CONTRIBUTING (how to send a change), CODE_OF_CONDUCT (community projects), SECURITY (how to report vulnerabilities), CHANGELOG (user-visible changes). Link them from the README only if they exist.

## Maintenance
Change the README in the same pull request as the behaviour it describes. Run the linter in CI: `python readme-enhanced/scripts/lint_readme.py README.md --strict`.

## Other languages
Keep one structure; put translations in `README.<lang>.md` and add a language switcher on the first line (`English | [简体中文](README.zh-CN.md)`).
