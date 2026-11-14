# product-docs-author

An Agent Skill for creating, reviewing, and validating product documentation using core-web conventions: product-owned directories, file-based routes, YAML frontmatter, navigation, and bilingual technical writing.

## Install

```bash
npx skills add cyborgoat/skills-enhanced --skill product-docs-author
```

No runtime packages are required.

## Target repository

The skill expects access to the documentation project being edited. In core-web, its sources of truth are:

- `docs/content-authoring/products.md`: authoring and routing rules.
- `data/products/<version>/<product-slug>/`: existing product documentation.

These files belong to the target project and are not bundled with the skill. For another project, inspect its authoring guide and route implementation, then agree on the intended layout before applying core-web conventions. Do not assume these paths exist in every repository.

## Use

Ask your agent to use `product-docs-author` to draft or review product documentation. In Claude Code:

```text
/product-docs-author Review the product documentation structure, frontmatter, and navigation
```

See [SKILL.md](SKILL.md) for the workflow, page shapes, and quality checklist.

## License

[MIT](LICENSE).
