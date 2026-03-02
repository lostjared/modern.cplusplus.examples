# Jared's Modern C++ Examples

A unified documentation hub for three generations of Jared Bruni's C++ example repositories:

- `11/` → C++11 examples
- `17/` → C++17 examples
- `2x/` → C++20 and C++23 examples

This project is designed as a **single landing experience** with an in-depth index page and three fully browsable, offline-ready documentation sites underneath it.

---

## Why this repository exists

Modern C++ evolves significantly across standards. A lot of feature discussions online are fragmented by version, and examples are often hard to compare side-by-side.

`modern.cplusplus.examples` solves that by:

1. Organizing examples by language era
2. Preserving the same docs interface across all standards
3. Making everything browsable locally (no CDN dependency)
4. Keeping generated metadata (feature detection, summaries, line notes) close to source code

---

## Repository layout

```text
modern.cplusplus.examples/
├── index.html         # Main landing page ("Jared's Modern C++ Examples")
├── README.md          # This file
├── 11/                # Generated docs for cplusplus11.Examples
│   ├── index.html
│   ├── data.js
│   └── assets/
├── 17/                # Generated docs for cplusplus17.Examples
│   ├── index.html
│   ├── data.js
│   └── assets/
└── 2x/                # Generated docs for cplusplus2x.Examples (C++20/C++23)
    ├── index.html
    ├── data.js
    └── assets/
```

---

## Subfolder guide (in depth)

## `11/` — C++11 Foundation Track

This section captures the beginning of “Modern C++” as most teams understand it today. C++11 introduced many of the language and library mechanisms that made safer, more expressive, and more performant code practical without custom frameworks.

### What you should expect here

- Core ownership patterns: move semantics and smart pointers
- Functional-style building blocks: lambdas and callable objects
- Type simplification with `auto`
- Range-based loops and stronger STL usage
- Concurrency primitives (`std::thread`, futures, mutexes)
- Better enum semantics (`enum class`) and compile-time features (`constexpr` basics)

### Why this folder matters

If someone is coming from pre-C++11 code, this is the transition zone where manual lifetime patterns and verbose type-heavy code start giving way to modern idioms. Even in C++20/23 codebases, many day-to-day patterns still rest on these C++11 fundamentals.

### Typical learning value

- Understanding ownership transfer and non-copying APIs
- Reading and writing lambda-heavy STL pipelines
- Recognizing modernized alternatives to legacy C++98 style

---

## `17/` — C++17 Maturity Track

C++17 is often the “pragmatic modern baseline” in production environments. It keeps the C++11 direction, but makes code cleaner, more readable, and easier to structure.

### What you should expect here

- `if constexpr` for cleaner compile-time branching
- Structured bindings for tuple-like decomposition
- Vocabulary types: `std::optional`, `std::variant`, `std::any`
- Improved filesystem support (`std::filesystem`)
- More practical generic programming patterns with less template noise

### Why this folder matters

C++17 tends to reduce boilerplate while preserving control. Many organizations that cannot yet move to C++20 still use C++17 as their standard baseline for serious cross-platform work.

### Typical learning value

- Refactoring verbose template branches into clear `if constexpr`
- Representing nullable or alternative values safely with `optional`/`variant`
- Building portable path/file tooling with standard filesystem APIs

---

## `2x/` — C++20/C++23 Advanced Track

This section covers the newest standards in the set: C++20 and C++23. The focus is not only “new syntax,” but richer abstraction tools that make constraints, ranges, async flows, and formatting more explicit and maintainable.

### What you should expect here

- Concepts and `requires` constraints for cleaner generic APIs
- Ranges/views pipelines for composable data processing
- Coroutines (`co_await`, `co_yield`, `co_return`) where applicable
- Three-way comparison (`<=>`) and modern comparison semantics
- Newer library features such as `std::span`, `std::format`, and related C++23 additions

### Why this folder matters

C++20/23 is where modern C++ starts to feel significantly more expressive by default. Constraint-based templates and range pipelines can make advanced code easier to reason about than older SFINAE-heavy styles.

### Typical learning value

- Designing template interfaces with explicit constraints
- Building readable transformation pipelines with ranges/views
- Adopting newer standard-library utilities that replace custom helpers

---

## Shared documentation interface (all three folders)

Each docs site in `11/`, `17/`, and `2x/` uses the same generated UI and capabilities:

- Searchable directory tree
- Per-file generated summary and concept notes
- Detected C++ feature badges (heuristic-based)
- Includes, class/struct, and function signature extraction
- Line-by-line commentary table
- Full source with line numbers
- Local syntax highlighting assets (offline support)

This consistency makes it easier to compare coding style and feature usage across standards.

---

## Deployment (upload-ready)

This folder is self-contained and can be uploaded directly:

- Upload `modern.cplusplus.examples/` as-is
- Keep `index.html` at the folder root
- Keep subfolders `11/`, `17/`, and `2x/` alongside it

No build step or external CDN is required for browsing.

---

## How to browse locally

Open the hub landing page:

- `index.html`

Then navigate into:

- `11/index.html`
- `17/index.html`
- `2x/index.html`

Because assets are bundled locally, no internet connection is required once files are present.

---

## Source repositories represented

These docs are generated from the corresponding repositories:

- `cplusplus11.Examples`
- `cplusplus17.Examples`
- `cplusplus2x.Examples`

The generated content in this hub mirrors those projects’ files at generation time.

---

## Regeneration workflow (maintainers)

If upstream examples change, regenerate each source repo docs first, then refresh this hub copy.

### 1) Regenerate source docs

From each source repository root:

```bash
python website_generator/generate_site.py
```

### 2) Sync into this hub

Copy docs output into subfolders:

```bash
cp -r ../cplusplus11.Examples/docs/. ./11/
cp -r ../cplusplus17.Examples/docs/. ./17/
cp -r ../cplusplus2x.Examples/docs/. ./2x/
```

---

## Notes on feature labels

Feature badges are heuristic detections, not compiler-grade semantic analysis. They are best used as guidance for exploration, not strict proof of language-standard usage.

---

## Audience

This hub is useful for:

- Developers learning modern C++ by era
- Engineers migrating legacy C++ to newer idioms
- Teams reviewing example-driven patterns before standard upgrades
- Anyone wanting an offline, searchable C++ reference set

---
