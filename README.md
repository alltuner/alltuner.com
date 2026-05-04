# alltuner.com

The marketing website for [All Tuner Labs](https://alltuner.com). Hugo static site with Tailwind CSS v4, English / Catalan / Spanish content.

## Stack

| Layer | Tool |
|---|---|
| Static site generator | [Hugo](https://gohugo.io) |
| CSS | [Tailwind CSS v4](https://tailwindcss.com) |
| JS bundler | [bun](https://bun.sh) |
| Languages | English, Catalan, Spanish |

## Develop

```bash
bun install                # install JS dependencies
bun run dev                # build assets + run hugo serve with hot reload
```

Visit `http://localhost:1313/`.

Other useful targets:

```bash
bun run build              # production build (assets + hugo)
bun run css:watch          # rebuild Tailwind CSS on change
bun run js:watch           # rebuild theme JS on change
bun run clean              # remove the public/ output
```

## Layout

```
alltuner.com/
├── content/               # Markdown content (per-language subdirs under content/ca, content/es)
├── css/                   # Tailwind input
├── data/                  # Hugo data files
├── static/                # Static assets served as-is
├── themes/alltuner-theme/ # Hugo theme (templates, JS, partials)
└── hugo.toml              # Hugo config
```

See [`AGENTS.md`](AGENTS.md) for the conventions used by the theme and the editorial flow.
