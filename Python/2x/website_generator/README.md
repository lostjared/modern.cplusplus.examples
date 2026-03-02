# C++20/C++23 Examples Website Generator

This generator builds a static HTML5/JavaScript documentation website for the full `cplusplus2x.Examples` tree.

## Output

Running the generator writes the website to:

- `../docs/index.html`
- `../docs/assets/styles.css`
- `../docs/assets/app.js`
- `../docs/data.js`

## How to regenerate

From `cplusplus2x.Examples`:

```bash
/home/jared/.pyenv/versions/3.10.13/bin/python website_generator/generate_site.py
```

Or with your active Python 3 environment:

```bash
python website_generator/generate_site.py
```

## What gets generated

For each source/support file in the tree (excluding `docs`, `.git`, and build artifacts), the site includes:

- Directory-tree navigation
- Auto-generated summary and concept notes
- Detected C++/library features (heuristic)
- Include/header analysis
- Class/struct and function signature extraction
- Line-level commentary notes
- Full source display

The site is fully static and can be hosted on any web server or opened directly in a browser.
