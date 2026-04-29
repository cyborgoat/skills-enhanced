---
name: product-docs-author
description: Use this skill when creating, updating, reviewing, or validating product documentation. It covers product doc folder layout, route mapping, frontmatter, root and subpage structure, navigation expectations, and the bilingual technical writing style used by the repository.
---

# Product Docs Author

## Overview

Use this skill to draft or revise product documentation for the `core-web` repository. It encodes the conventions from `docs/content-authoring/products.md` and observed examples in `data/products`.

Before changing content, read the relevant existing product files so the new page matches that product/version's terminology, language, and navigation depth.

## Source Of Truth

Use repo files first:

- `docs/content-authoring/products.md` for routing, folder, frontmatter, and checklist rules.
- Existing files under `{data_path}/products/<version>/<product-slug>/` for local voice, page depth, and cross-links.

## Workflow

1. Identify the target version and product slug.
   - Path: `data/products/<version>/<product-slug>/`
   - Root route: `/products/<version>/<product-slug>`
   - Subpage route: `/products/<version>/<product-slug>/<path>`
2. Confirm the product slug is a specific product name, not a section or task name such as `<setup-page>`, `<design-section>`, `<monitoring-section>`, or `<auth-section>`.
3. Put all product-owned content under that product directory. Do not scatter files elsewhere under `data/products`.
4. Use `README.md` as the root overview page. Do not create an `overview/` folder just to hold overview content.
5. Choose section folders by purpose:
   - `architecture/` for system design and flows
   - `operations/` for runbooks, rollout, incident, and command-center procedures
   - `reference/` for release notes, evidence packs, APIs, rendering samples, and stable lookup material
   - `concepts/` for operating models and domain concepts
   - `subsystems/` for component-level pages
6. Write valid YAML frontmatter at the top of every page.
7. Keep headings meaningful, paragraphs short, and route/file names slug-safe.
8. If the work changes navigation-sensitive content, preview or test the product route locally when practical.

## Frontmatter

Root `README.md` recommended fields:

```yaml
---
title: "Overview"
date: "<YYYY-MM-DD>"
excerpt: "Short summary shown in product lists."
slug: "<product-slug>"
description: "Longer description for metadata and summaries."
status: "<status>"
tags: ["<tag-1>", "<tag-2>"]
---
```

Subpage recommended fields:

```yaml
---
title: "<Subpage Title>"
date: "<YYYY-MM-DD>"
excerpt: "Short summary for this page."
slug: "<subpage-slug>"
---
```

Rules:

- Use quoted date strings in `YYYY-MM-DD` form.
- Root pages should include `slug`, `description`, and `status` when available.
- Subpage `slug` should mirror the route below the product root, such as `<subpage-slug>`, `<section>/<topic>`, or `<workflow-section>/<procedure>`.
- `title` and `description` or `excerpt` are recommended. Missing titles fall back to humanized filenames, but explicit titles are preferred.

## Page Shapes

Root pages usually contain:

1. Overview: what this version/product is for.
2. Scope or version focus: what it owns and excludes.
3. Capabilities, requirements, or contracts.
4. Recommended reading links using repo-relative doc paths such as `` `<subpage>.md` ``.

Procedural subpages usually contain:

1. Purpose or scenario.
2. Prerequisites.
3. Numbered steps.
4. Verification or expected result.
5. Troubleshooting when failure modes are meaningful.

Architecture, concept, and reference pages can use diagrams, tables, and concise bullets when they clarify system behavior. Mermaid diagrams are acceptable when existing nearby pages use them.

## Writing Style

- Match the product's existing language. Many product docs in this repo are written in Chinese with English product names and technical terms.
- Prefer concrete operational wording over marketing copy.
- Explain boundaries, signals, approvals, rollback, validation, and auditability when relevant to operational or runtime products.
- Use short paragraphs and focused lists. Avoid placeholder language.
- Keep UI/rendering test pages realistic enough to exercise Markdown features, but label them as demo or reference material when that is their purpose.

## Quality Checklist

Before finishing:

- The product directory has a root `README.md`.
- All new files are nested under the correct `data/products/<version>/<product-slug>/` directory.
- File and folder names are lowercase slug-safe unless the existing version folder intentionally uses another format.
- Frontmatter is valid YAML and begins at the first line.
- Root summaries use `description`, with `excerpt` as a shorter list summary.
- Procedural pages include prerequisites and verification when applicable.
- Cross-links point to existing or newly created files.
- The resulting route follows the filesystem path exactly.
