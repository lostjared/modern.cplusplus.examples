#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".hh",
    ".md",
    ".txt",
    ".mk",
}

DIRECT_FILE_NAMES = {"Makefile", "makefile", "GNUmakefile"}
EXCLUDED_DIRS = {
    ".git",
    "docs",
    "website_generator",
    "build",
    "bin",
    "obj",
}

FEATURE_PATTERNS = {
    "if constexpr": [r"\bif\s+constexpr\b"],
    "structured bindings": [
        r"\b(?:auto|const\s+auto)\s*(?:&|&&)?\s*\[[^\]]+\]\s*=",
    ],
    "std::optional": [r"\bstd::optional\b"],
    "std::variant": [r"\bstd::variant\b", r"\bstd::visit\b"],
    "std::any": [r"\bstd::any\b", r"\bstd::any_cast\b"],
    "std::string_view": [r"\bstd::string_view\b"],
    "std::filesystem": [r"\bstd::filesystem::"],
    "parallel algorithms": [r"\bstd::execution::"],
    "nested namespaces": [r"\bnamespace\s+\w+(?:::\w+)+\s*\{"],
    "[[nodiscard]]": [r"\[\[\s*nodiscard\s*\]\]"],
    "[[maybe_unused]]": [r"\[\[\s*maybe_unused\s*\]\]"],
    "[[fallthrough]]": [r"\[\[\s*fallthrough\s*\]\]"],
    "std::invoke": [r"\bstd::invoke\b"],
    "std::apply": [r"\bstd::apply\b"],
    "if / switch with initializer": [
        r"\bif\s*\([^)]*;[^)]*\)",
        r"\bswitch\s*\([^)]*;[^)]*\)",
    ],
    "std::clamp": [r"\bstd::clamp\b"],
    "std::byte": [r"\bstd::byte\b"],
    "std::from_chars / to_chars": [r"\bstd::from_chars\b", r"\bstd::to_chars\b"],
    "std::size / std::empty / std::data": [
        r"\bstd::size\b",
        r"\bstd::empty\b",
        r"\bstd::data\b",
    ],
}

KEYWORD_NOTES = [
    (r"^\s*#\s*include\s*[<\"]([^>\"]+)", "Brings in header `{match}` needed by this example."),
    (r"^\s*class\s+(\w+)", "Declares class `{match}` that models the core data or behavior."),
    (r"^\s*struct\s+(\w+)", "Declares struct `{match}` used for lightweight grouped data."),
    (r"\bint\s+main\s*\(", "Program entry point: execution starts here."),
    (r"\bstd::sort\b", "Sorts a container to demonstrate ordering with comparators."),
    (r"\bstd::async\b", "Launches asynchronous work on a separate task/future."),
    (r"\bstd::thread\b", "Creates a thread to run work concurrently."),
    (r"\bstd::regex\b", "Builds a regular expression pattern for text matching."),
    (r"\bstd::move\b", "Transfers ownership/resources instead of copying."),
    (r"\breturn\b", "Returns a value or exits the current function scope."),
    (r"\bfor\s*\(", "Loops over data to apply repeated processing."),
    (r"\bwhile\s*\(", "Repeats logic while a condition remains true."),
    (r"\bif\s*\(", "Branches behavior based on a condition."),
    (r"\bswitch\s*\(", "Selects one branch from multiple labeled cases."),
    (r"\btemplate\s*<", "Introduces a template to generalize code across types."),
]

INDEX_HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <title>C++17 Examples Documentation</title>
  <link rel="stylesheet" href="assets/highlightjs/github-dark.min.css?v={CACHE_VER}" />
  <link rel="stylesheet" href="assets/styles.css?v={CACHE_VER}" />
</head>
<body>
  <header class=\"topbar\">
    <div>
      <h1>C++17 Examples Documentation</h1>
      <p id=\"siteMeta\"></p>
    </div>
    <input id=\"search\" type=\"search\" placeholder=\"Search files, folders, or concepts...\" />
  </header>

  <main class=\"layout\">
    <aside class=\"sidebar\">
      <h2>Directory Tree</h2>
      <nav id=\"tree\" class=\"tree\"></nav>
    </aside>

    <section class=\"content\" id=\"content\">
      <div class=\"welcome\">
        <h2>Project Index</h2>
        <p>This site documents Jared Bruni's C++17 examples repository and provides generated walkthroughs for each source file.</p>
        <p>
          GitHub: <a class=\"ext-link\" href=\"https://github.com/lostjared/cplusplus17.Examples/\" target=\"_blank\" rel=\"noopener noreferrer\">https://github.com/lostjared/cplusplus17.Examples/</a>
        </p>
        <h3>Clone the Repository</h3>
        <pre><code>git clone https://github.com/lostjared/cplusplus17.Examples.git
      cd cplusplus17.Examples</code></pre>
        <h3>Build Notes</h3>
        <pre><code># Linux / macOS
      make</code></pre>
        <p>Select an example from the left tree to open generated explanations, line commentary, and syntax-highlighted source.</p>
        <ul id=\"quickStats\"></ul>
        <h3>Top-Level Example Projects</h3>
        <div id=\"projectCards\" class=\"project-cards\"></div>
      </div>
    </section>
  </main>

  <script src="data.js?v={CACHE_VER}"></script>
  <script src="assets/highlightjs/highlight.min.js?v={CACHE_VER}"></script>
  <script src="assets/app.js?v={CACHE_VER}"></script>
</body>
</html>
"""

STYLES_CSS = """:root {
  color-scheme: light dark;
  --bg: #0b1220;
  --panel: #111b2e;
  --panel-2: #15233b;
  --text: #e6edf7;
  --muted: #9fb1cf;
  --accent: #6ea8fe;
  --accent-2: #8ef0cc;
  --border: #274063;
  --code: #0a1020;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: Inter, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  background: linear-gradient(180deg, #0b1220 0%, #0f1829 100%);
  color: var(--text);
  min-height: 100vh;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
  padding: 1.1rem 1.5rem;
  border-bottom: 1px solid var(--border);
  background: rgba(10, 18, 30, 0.94);
  position: sticky;
  top: 0;
  backdrop-filter: blur(8px);
  z-index: 10;
}

.topbar h1 { margin: 0; font-size: 1.25rem; }
.topbar p { margin: 0.3rem 0 0; color: var(--muted); font-size: 0.9rem; }

#search {
  width: min(500px, 48vw);
  padding: 0.65rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: 0.6rem;
  background: var(--panel-2);
  color: var(--text);
}

.layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  height: calc(100vh - 74px);
}

.sidebar {
  border-right: 1px solid var(--border);
  padding: 1rem;
  background: rgba(17, 27, 46, 0.72);
  overflow: auto;
}

.sidebar h2 {
  margin: 0 0 0.8rem;
  font-size: 1rem;
  color: var(--accent-2);
}

.tree details { margin-left: 0.5rem; }
.tree summary {
  cursor: pointer;
  color: var(--text);
  font-weight: 600;
  margin: 0.2rem 0;
}

.tree .file {
  display: block;
  color: var(--muted);
  text-decoration: none;
  margin: 0.18rem 0 0.18rem 1.1rem;
  border-left: 2px solid transparent;
  padding-left: 0.45rem;
}

.tree .file:hover,
.tree .file.active {
  color: var(--accent-2);
  border-left-color: var(--accent-2);
}

.content {
  padding: 1.2rem 1.4rem 2rem;
  overflow: auto;
}

.panel {
  background: rgba(21, 35, 59, 0.86);
  border: 1px solid var(--border);
  border-radius: 0.9rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.6rem;
  margin-top: 0.8rem;
}

.meta div {
  background: rgba(10, 16, 32, 0.8);
  border: 1px solid var(--border);
  border-radius: 0.6rem;
  padding: 0.45rem 0.6rem;
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

h2, h3 {
  margin: 0.2rem 0 0.7rem;
  overflow-wrap: anywhere;
  word-break: break-word;
}
p { margin-top: 0; line-height: 1.45; }
ul { margin: 0.2rem 0 0; padding-left: 1.2rem; line-height: 1.45; }

code, pre {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, Monaco, monospace;
}

pre {
  background: var(--code);
  border: 1px solid #20324c;
  border-radius: 0.8rem;
  padding: 0.85rem;
  overflow-x: auto;
}

.code-wrap {
  background: var(--code);
  border: 1px solid #20324c;
  border-radius: 0.8rem;
  overflow: auto;
}

.code-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.code-table td {
  vertical-align: top;
  border-bottom: 1px solid rgba(39, 64, 99, 0.35);
}

.code-table tr:last-child td {
  border-bottom: none;
}

.code-table .ln {
  width: 64px;
  text-align: right;
  padding: 0.08rem 0.7rem;
  color: var(--muted);
  user-select: none;
  border-right: 1px solid rgba(39, 64, 99, 0.6);
}

.code-table .lc {
  padding: 0.08rem 0.8rem;
}

.code-table .lc code {
  display: block;
  white-space: pre;
}

.code-table .lc code.hljs {
  display: block;
  margin: 0;
  padding: 0;
  background: transparent;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
  table-layout: fixed;
}

.table th, .table td {
  text-align: left;
  border-bottom: 1px solid var(--border);
  padding: 0.45rem 0.35rem;
  vertical-align: top;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.table th:first-child,
.table td:first-child {
  width: 72px;
  white-space: nowrap;
}

.badge {
  display: inline-block;
  background: rgba(110, 168, 254, 0.2);
  color: #b8d4ff;
  border: 1px solid rgba(110, 168, 254, 0.5);
  border-radius: 999px;
  padding: 0.12rem 0.52rem;
  margin: 0.1rem 0.18rem 0.1rem 0;
  font-size: 0.8rem;
}

.empty { color: var(--muted); font-style: italic; }

.ext-link {
  color: var(--accent-2);
  text-decoration: none;
}

.ext-link:hover {
  text-decoration: underline;
}

.project-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0.8rem;
}

.project-card {
  background: rgba(10, 16, 32, 0.78);
  border: 1px solid var(--border);
  border-radius: 0.7rem;
  padding: 0.75rem 0.85rem;
}

.project-card h4 {
  margin: 0 0 0.45rem;
  color: var(--accent-2);
  font-size: 0.98rem;
}

.project-card p {
  margin: 0.2rem 0;
  color: var(--muted);
  font-size: 0.9rem;
}

.markdown-body {
  line-height: 1.55;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin: 0.4rem 0 0.7rem;
}

.markdown-body p {
  margin: 0.55rem 0;
}

.markdown-body ul,
.markdown-body ol {
  margin: 0.35rem 0 0.75rem;
  padding-left: 1.25rem;
}

.markdown-body blockquote {
  margin: 0.7rem 0;
  padding: 0.1rem 0 0.1rem 0.8rem;
  border-left: 3px solid rgba(110, 168, 254, 0.55);
  color: var(--muted);
}

.markdown-body hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.8rem 0;
}

@media (max-width: 980px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { max-height: 36vh; border-right: none; border-bottom: 1px solid var(--border); }
  #search { width: 100%; }
  .topbar { align-items: stretch; flex-direction: column; }
}
"""

APP_JS = """/* build:{CACHE_VER} */
const data = window.EXAMPLES_DATA;
const treeRoot = document.getElementById('tree');
const content = document.getElementById('content');
const search = document.getElementById('search');

function esc(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

function byPath(path) {
  return data.files.find(f => f.path === path);
}

function renderTreeNode(node, depth = 0) {
  if (node.type === 'file') {
    return `<a class=\"file\" href=\"#${encodeURIComponent(node.path)}\" data-path=\"${esc(node.path)}\">${esc(node.name)}</a>`;
  }

  const children = node.children.map(child => renderTreeNode(child, depth + 1)).join('');
  const openAttr = depth === 0 ? ' open' : '';
  return `<details${openAttr}><summary>${esc(node.name)}</summary>${children}</details>`;
}

function countByExtension(files) {
  const count = {};
  for (const f of files) {
    count[f.extension] = (count[f.extension] || 0) + 1;
  }
  return Object.entries(count)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([ext, c]) => `${ext || '(none)'}: ${c}`);
}

function renderOverview() {
  const stats = document.getElementById('quickStats');
  const topExt = countByExtension(data.files);
  const uniqueDirs = new Set(data.files.map(f => f.directory)).size;
  stats.innerHTML = `
    <li><strong>Total files indexed:</strong> ${data.files.length}</li>
    <li><strong>Root:</strong> ${esc(data.rootName)}</li>
    <li><strong>Total directories represented:</strong> ${uniqueDirs}</li>
    <li><strong>Most common file types:</strong> ${esc(topExt.join(' | '))}</li>
  `;

  renderProjectCards();
}

function getTopLevelProject(path) {
  const parts = String(path || '').split('/').filter(Boolean);
  return parts.length ? parts[0] : '(root)';
}

function renderProjectCards() {
  const container = document.getElementById('projectCards');
  if (!container) return;

  const groups = new Map();

  for (const file of data.files) {
    const project = getTopLevelProject(file.path);
    if (!groups.has(project)) {
      groups.set(project, { files: 0, lines: 0, extCount: {} });
    }

    const entry = groups.get(project);
    entry.files += 1;
    entry.lines += Number(file.lineCount || 0);
    entry.extCount[file.extension] = (entry.extCount[file.extension] || 0) + 1;
  }

  const cards = Array.from(groups.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([project, info]) => {
      const topTypes = Object.entries(info.extCount)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([ext, count]) => `${ext || '(none)'}: ${count}`)
        .join(' | ');

      return `<article class=\"project-card\">\
        <h4>${esc(project)}</h4>\
        <p><strong>Files:</strong> ${info.files}</p>\
        <p><strong>Total lines:</strong> ${info.lines}</p>\
        <p><strong>Main file types:</strong> ${esc(topTypes || 'N/A')}</p>\
      </article>`;
    })
    .join('');

  container.innerHTML = cards || '<p class=\"empty\">No project folders found.</p>';
}

function languageForFile(file) {
  const ext = String(file.extension || '').toLowerCase();
  if (['.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.hh'].includes(ext)) return 'cpp';
  if (ext === '.md') return 'markdown';
  if (ext === '.mk' || file.name === 'Makefile' || file.name === 'makefile' || file.name === 'GNUmakefile') return 'makefile';
  if (ext === '.txt') return 'plaintext';
  return 'plaintext';
}

function highlightLine(line, file) {
  const safeLine = line === '' ? ' ' : line;

  if (window.hljs) {
    const language = languageForFile(file);
    try {
      return window.hljs.highlight(safeLine, { language, ignoreIllegals: true }).value || '&nbsp;';
    } catch (_) {
      try {
        return window.hljs.highlightAuto(safeLine).value || '&nbsp;';
      } catch (_) {
        return esc(safeLine);
      }
    }
  }

  return esc(safeLine);
}

function renderCodeWithLineNumbers(source, file) {
  const normalized = String(source).replace(/\\r/g, '');
  const lines = normalized.split('\\n');

  while (lines.length > 1 && lines[lines.length - 1] === '') {
    lines.pop();
  }

  const rows = lines
    .map((line, index) => `<tr><td class="ln">${index + 1}</td><td class="lc"><code class="hljs">${highlightLine(line, file)}</code></td></tr>`)
    .join('');

  return `<div class="code-wrap"><table class="code-table"><tbody>${rows}</tbody></table></div>`;
}

function isReadmeFile(file) {
  return String(file.name || '').toLowerCase() === 'readme.md';
}

function renderInlineMarkdown(text) {
  const codeChunks = [];
  let html = esc(String(text || ''));

  html = html.replace(/`([^`]+)`/g, (_, code) => {
    codeChunks.push(code);
    return `@@CODE${codeChunks.length - 1}@@`;
  });

  html = html.replace(/\\[([^\\]]+)\\]\\(([^)\\s]+)\\)/g, '<a class="ext-link" href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  html = html.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
  html = html.replace(/\\*([^*]+)\\*/g, '<em>$1</em>');

  html = html.replace(/@@CODE(\\d+)@@/g, (_, index) => `<code>${codeChunks[Number(index)]}</code>`);
  return html;
}

function renderMarkdownDocument(source) {
  const lines = String(source || '').replace(/\\r/g, '').split('\\n');
  const out = [];
  let paragraph = [];
  let inUl = false;
  let inOl = false;
  let inCode = false;
  let codeLang = '';
  let codeLines = [];

  function closeLists() {
    if (inUl) {
      out.push('</ul>');
      inUl = false;
    }
    if (inOl) {
      out.push('</ol>');
      inOl = false;
    }
  }

  function flushParagraph() {
    if (!paragraph.length) return;
    out.push(`<p>${renderInlineMarkdown(paragraph.join(' '))}</p>`);
    paragraph = [];
  }

  for (const rawLine of lines) {
    const line = String(rawLine);

    if (inCode) {
      if (/^\\s*```/.test(line)) {
        const codeText = esc(codeLines.join('\\n'));
        const langClass = codeLang ? ` class="language-${esc(codeLang)}"` : '';
        out.push(`<pre><code${langClass}>${codeText}</code></pre>`);
        inCode = false;
        codeLang = '';
        codeLines = [];
      } else {
        codeLines.push(line);
      }
      continue;
    }

    const fenceMatch = line.match(/^\\s*```\\s*([A-Za-z0-9_+.-]+)?\\s*$/);
    if (fenceMatch) {
      flushParagraph();
      closeLists();
      inCode = true;
      codeLang = fenceMatch[1] || '';
      codeLines = [];
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      closeLists();
      continue;
    }

    const heading = line.match(/^(#{1,6})\\s+(.+)$/);
    if (heading) {
      flushParagraph();
      closeLists();
      const level = heading[1].length;
      out.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    if (/^(?:\\*\\s*\\*\\s*\\*|-{3,}|_{3,})\\s*$/.test(line.trim())) {
      flushParagraph();
      closeLists();
      out.push('<hr/>');
      continue;
    }

    const ulItem = line.match(/^\\s*[-*+]\\s+(.+)$/);
    if (ulItem) {
      flushParagraph();
      if (inOl) {
        out.push('</ol>');
        inOl = false;
      }
      if (!inUl) {
        out.push('<ul>');
        inUl = true;
      }
      out.push(`<li>${renderInlineMarkdown(ulItem[1])}</li>`);
      continue;
    }

    const olItem = line.match(/^\\s*\\d+\\.\\s+(.+)$/);
    if (olItem) {
      flushParagraph();
      if (inUl) {
        out.push('</ul>');
        inUl = false;
      }
      if (!inOl) {
        out.push('<ol>');
        inOl = true;
      }
      out.push(`<li>${renderInlineMarkdown(olItem[1])}</li>`);
      continue;
    }

    const quote = line.match(/^>\\s?(.*)$/);
    if (quote) {
      flushParagraph();
      closeLists();
      out.push(`<blockquote><p>${renderInlineMarkdown(quote[1])}</p></blockquote>`);
      continue;
    }

    closeLists();
    paragraph.push(line.trim());
  }

  flushParagraph();
  closeLists();

  if (inCode) {
    const codeText = esc(codeLines.join('\\n'));
    const langClass = codeLang ? ` class="language-${esc(codeLang)}"` : '';
    out.push(`<pre><code${langClass}>${codeText}</code></pre>`);
  }

  return out.join('\\n');
}

function renderFile(file) {
  if (isReadmeFile(file)) {
    content.innerHTML = `
      <article class="panel markdown-body">
        ${renderMarkdownDocument(file.code)}
      </article>
    `;
    content.scrollTop = 0;
    window.scrollTo(0, 0);

    document.querySelectorAll('.file').forEach(el => el.classList.remove('active'));
    const active = document.querySelector(`.file[data-path="${CSS.escape(file.path)}"]`);
    if (active) active.classList.add('active');
    return;
  }

  const features = file.features.length
    ? file.features.map(f => `<span class=\"badge\">${esc(f)}</span>`).join('')
    : '<span class=\"empty\">No specific C++17 pattern heuristics detected.</span>';

  const includes = file.includes.length
    ? `<ul>${file.includes.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`
    : '<p class=\"empty\">No include directives found.</p>';

  const functions = file.functions.length
    ? `<ul>${file.functions.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`
    : '<p class=\"empty\">No function signatures detected.</p>';

  const classes = file.classes.length
    ? `<ul>${file.classes.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`
    : '<p class=\"empty\">No class/struct declarations detected.</p>';

  const lineNotes = file.lineNotes.length
    ? `<table class=\"table\"><thead><tr><th>Line</th><th>Commentary</th></tr></thead><tbody>${file.lineNotes.map(n => `<tr><td>${n.line}</td><td>${esc(n.note)}</td></tr>`).join('')}</tbody></table>`
    : '<p class=\"empty\">No line-level notes generated for this file.</p>';

  const numberedSource = renderCodeWithLineNumbers(file.code, file);

  content.innerHTML = `
    <article class=\"panel\">
      <h2>${esc(file.path)}</h2>
      <p>${esc(file.summary)}</p>
      <div class=\"meta\">
        <div><strong>Directory:</strong><br/>${esc(file.directory)}</div>
        <div><strong>Extension:</strong><br/>${esc(file.extension)}</div>
        <div><strong>Lines:</strong><br/>${file.lineCount}</div>
        <div><strong>Approx complexity:</strong><br/>${esc(file.complexity)}</div>
      </div>
    </article>

    <section class=\"panel\">
      <h3>What This Example Demonstrates</h3>
      <ul>${file.demonstrates.map(d => `<li>${esc(d)}</li>`).join('')}</ul>
    </section>

    <section class=\"panel\">
      <h3>Detected C++ Features</h3>
      <div>${features}</div>
    </section>

    <section class=\"panel\">
      <h3>Headers / Includes</h3>
      ${includes}
    </section>

    <section class=\"panel\">
      <h3>Classes and Structs</h3>
      ${classes}
    </section>

    <section class=\"panel\">
      <h3>Functions</h3>
      ${functions}
    </section>

    <section class=\"panel\">
      <h3>Line-by-Line Commentary</h3>
      ${lineNotes}
    </section>

    <section class=\"panel\">
      <h3>Full Source</h3>
      ${numberedSource}
    </section>
  `;

  content.scrollTop = 0;
  window.scrollTo(0, 0);
  document.querySelectorAll('.file').forEach(el => el.classList.remove('active'));
  const active = document.querySelector(`.file[data-path=\"${CSS.escape(file.path)}\"]`);
  if (active) active.classList.add('active');
}

function openFromHash() {
  const hash = decodeURIComponent(location.hash.replace(/^#/, ''));
  if (!hash) return;
  const file = byPath(hash);
  if (file) renderFile(file);
}

function initTree(filter = '') {
  const normalized = filter.trim().toLowerCase();

  function cloneAndFilter(node) {
    if (node.type === 'file') {
      const match = !normalized || node.path.toLowerCase().includes(normalized) || node.name.toLowerCase().includes(normalized);
      return match ? node : null;
    }

    const nextChildren = node.children
      .map(cloneAndFilter)
      .filter(Boolean);

    const selfMatch = !normalized || node.name.toLowerCase().includes(normalized) || node.path.toLowerCase().includes(normalized);
    if (selfMatch || nextChildren.length > 0) {
      return { ...node, children: nextChildren };
    }
    return null;
  }

  const filtered = cloneAndFilter(data.tree);
  treeRoot.innerHTML = filtered ? renderTreeNode(filtered) : '<p class=\"empty\">No matches found.</p>';
}

document.getElementById('siteMeta').textContent = `Generated ${data.generatedAt} • ${data.files.length} files indexed`;
initTree();
renderOverview();
openFromHash();

window.addEventListener('hashchange', openFromHash);
search.addEventListener('input', () => initTree(search.value));
"""


def should_include_file(path: Path) -> bool:
    if path.name in DIRECT_FILE_NAMES:
        return True
    return path.suffix.lower() in SOURCE_EXTENSIONS


def is_excluded(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in EXCLUDED_DIRS for part in rel_parts)


def extract_header_comment(lines: List[str]) -> str:
    if not lines:
        return ""

    first_nonempty_index = 0
    while first_nonempty_index < len(lines) and not lines[first_nonempty_index].strip():
        first_nonempty_index += 1

    if first_nonempty_index >= len(lines):
        return ""

    block_start = lines[first_nonempty_index].strip()
    if block_start.startswith("/*"):
        collected: List[str] = []
        for line in lines[first_nonempty_index:]:
            collected.append(line)
            if "*/" in line:
                break
        text = "\n".join(collected)
        text = re.sub(r"^\s*/\*+", "", text)
        text = re.sub(r"\*+/\s*$", "", text)
        cleaned = [re.sub(r"^\s*\*\s?", "", ln).strip() for ln in text.splitlines()]
        return " ".join(part for part in cleaned if part)

    if block_start.startswith("//"):
        collected: List[str] = []
        for line in lines[first_nonempty_index:]:
            if line.strip().startswith("//"):
                collected.append(re.sub(r"^\s*//\s?", "", line).strip())
            else:
                break
        return " ".join(part for part in collected if part)

    return ""


def _strip_comments_and_strings(code: str) -> str:
    """Remove comments and string literals so feature regexes only match real code."""
    return re.sub(
        r'R"([A-Za-z_]*)\([\s\S]*?\)\1"'   # raw string literals
        r'|"(?:\\.|[^"\\])*"'                # regular strings
        r"|'(?:\\.|[^'\\])*'"                  # char literals
        r'|//[^\n]*'                             # single-line comments
        r'|/\*[\s\S]*?\*/',                    # multi-line comments
        lambda m: ' ' if m.group(0)[:2] in ('//', '/*') else '""',
        code,
    )


def detect_features(code: str) -> List[str]:
    cleaned = _strip_comments_and_strings(code)
    found: List[str] = []
    for feature, patterns in FEATURE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, cleaned, flags=re.MULTILINE):
                found.append(feature)
                break
    return sorted(found)


def extract_includes(lines: List[str]) -> List[str]:
    items: List[str] = []
    for line in lines:
        match = re.match(r"\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", line)
        if match:
            items.append(match.group(1))
    return sorted(dict.fromkeys(items))


def extract_classes(code: str) -> List[str]:
    matches = re.findall(r"\b(class|struct)\s+([A-Za-z_][A-Za-z0-9_]*)", code)
    labels = [f"{kind} {name}" for kind, name in matches]
    return sorted(dict.fromkeys(labels))[:40]


def extract_functions(lines: List[str]) -> List[str]:
    signatures: List[str] = []
    pattern = re.compile(
        r"^\s*(?:template\s*<[^>]+>\s*)?"
        r"(?:[\w:&<>,\*\s~]+)\s+"
        r"([A-Za-z_][A-Za-z0-9_:~]*)\s*\(([^\)]*)\)\s*(?:const)?\s*(?:\{|;)?\s*$"
    )
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("if ") or stripped.startswith("for ") or stripped.startswith("while ") or stripped.startswith("switch "):
            continue
        match = pattern.match(line)
        if match:
            name, args = match.groups()
            if name in {"if", "for", "while", "switch"}:
                continue
            compact_args = re.sub(r"\s+", " ", args.strip())
            signatures.append(f"{name}({compact_args})")
    return sorted(dict.fromkeys(signatures))[:80]


def complexity_label(lines: List[str]) -> str:
    counter = Counter()
    joined = "\n".join(lines)
    counter["loops"] = len(re.findall(r"\b(for|while)\s*\(", joined))
    counter["branches"] = len(re.findall(r"\b(if|switch|case)\b", joined))
    counter["functions"] = len(extract_functions(lines))

    score = counter["loops"] * 2 + counter["branches"] + counter["functions"]
    if score <= 6:
        return "Low"
    if score <= 18:
        return "Medium"
    return "High"


def derive_topic(rel_path: str) -> str:
    parts = rel_path.split("/")
    if len(parts) <= 1:
        return "general C++17 language features"
    folder = parts[0]
    cleaned = folder.replace("_", " ")
    if cleaned.upper() == "UNIX":
        return "UNIX and POSIX system programming"
    if cleaned.upper() == "SDL2":
        return "SDL2 graphics and event-driven programming"
    return cleaned


def line_level_notes(lines: List[str]) -> List[Dict[str, Any]]:
    notes: List[Dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        for pattern, message in KEYWORD_NOTES:
            match = re.search(pattern, line)
            if match:
                key = match.group(1) if match.groups() else match.group(0).strip()
                notes.append({"line": idx, "note": message.format(match=key)})
                break
        if len(notes) >= 40:
            break
    return notes


def summarize_file(rel_path: str, header_comment: str, features: List[str], functions: List[str], classes: List[str]) -> str:
    topic = derive_topic(rel_path)
    if header_comment:
        return f"This example in {topic} focuses on: {header_comment}"

    elements = []
    if classes:
        elements.append(f"{len(classes)} type declaration(s)")
    if functions:
        elements.append(f"{len(functions)} function signature(s)")
    if features:
        elements.append(f"{len(features)} detected C++ feature pattern(s)")

    if not elements:
        return f"This file appears to be a support artifact for {topic}, included in the C++17 examples set."

    joined = ", ".join(elements)
    return f"This {topic} example includes {joined} and is intended as a focused learning snippet."


def demonstrates_points(rel_path: str, features: List[str], includes: List[str], functions: List[str], classes: List[str]) -> List[str]:
    points: List[str] = []
    points.append(f"Topic area: {derive_topic(rel_path)}.")
    if features:
        points.append("Modern C++ patterns detected: " + ", ".join(features) + ".")
    if includes:
        points.append("Primary dependencies appear in headers like: " + ", ".join(includes[:6]) + ("..." if len(includes) > 6 else "") + ".")
    if classes:
        points.append("Data modeling or behavior is organized with declarations such as: " + ", ".join(classes[:4]) + ("..." if len(classes) > 4 else "") + ".")
    if functions:
        points.append("Execution flow is defined through functions including: " + ", ".join(functions[:5]) + ("..." if len(functions) > 5 else "") + ".")
    points.append("Use this file as a focused reference for the concept shown by its directory and symbol names.")
    return points


def collect_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if is_excluded(path, root):
            continue
        if should_include_file(path):
            files.append(path)
    return files


def tree_insert(node: Dict[str, Any], parts: List[str], rel_path: str) -> None:
    if not parts:
        return
    head, *tail = parts
    if not tail:
        node.setdefault("children", []).append({"type": "file", "name": head, "path": rel_path})
        return

    children = node.setdefault("children", [])
    for child in children:
        if child["type"] == "dir" and child["name"] == head:
            tree_insert(child, tail, rel_path)
            return

    new_child = {"type": "dir", "name": head, "path": "/".join(parts[:-1]) if len(parts) > 1 else head, "children": []}
    children.append(new_child)
    tree_insert(new_child, tail, rel_path)


def sort_tree(node: Dict[str, Any]) -> None:
    children = node.get("children", [])
    for child in children:
        if child.get("type") == "dir":
            sort_tree(child)
    children.sort(key=lambda c: (0 if c["type"] == "dir" else 1, c["name"].lower()))


def build_dataset(root: Path) -> Dict[str, Any]:
    files = collect_files(root)
    tree: Dict[str, Any] = {"type": "dir", "name": root.name, "path": root.name, "children": []}
    entries: List[Dict[str, Any]] = []

    for file_path in files:
        rel_path = file_path.relative_to(root).as_posix()
        text = file_path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()

        includes = extract_includes(lines)
        features = detect_features(text)
        classes = extract_classes(text)
        functions = extract_functions(lines)
        header_comment = extract_header_comment(lines)
        summary = summarize_file(rel_path, header_comment, features, functions, classes)
        demonstrates = demonstrates_points(rel_path, features, includes, functions, classes)
        notes = line_level_notes(lines)

        entry = {
            "path": rel_path,
            "name": file_path.name,
            "directory": str(file_path.parent.relative_to(root)).replace("\\", "/"),
            "extension": file_path.suffix.lower() or file_path.name,
            "lineCount": len(lines),
            "summary": summary,
            "demonstrates": demonstrates,
            "features": features,
            "includes": includes,
            "classes": classes,
            "functions": functions,
            "complexity": complexity_label(lines),
            "lineNotes": notes,
            "code": text,
        }
        entries.append(entry)
        tree_insert(tree, rel_path.split("/"), rel_path)

    sort_tree(tree)

    return {
        "rootName": root.name,
        "generatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": sorted(entries, key=lambda e: e["path"].lower()),
        "tree": tree,
    }


def write_site(root: Path, output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    highlight_assets_dir = assets_dir / "highlightjs"
    assets_dir.mkdir(parents=True, exist_ok=True)
    highlight_assets_dir.mkdir(parents=True, exist_ok=True)

    dataset = build_dataset(root)

    cache_ver = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    index_html = INDEX_HTML.replace("{CACHE_VER}", cache_ver)
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")
    (assets_dir / "styles.css").write_text(STYLES_CSS, encoding="utf-8")
    (assets_dir / "app.js").write_text(APP_JS.replace("{CACHE_VER}", cache_ver), encoding="utf-8")

    vendor_dir = root / "website_generator" / "vendor" / "highlightjs"
    shutil.copy2(vendor_dir / "highlight.min.js", highlight_assets_dir / "highlight.min.js")
    shutil.copy2(vendor_dir / "github-dark.min.css", highlight_assets_dir / "github-dark.min.css")

    data_js = "window.EXAMPLES_DATA = " + json.dumps(dataset, ensure_ascii=False) + ";\n"
    (output_dir / "data.js").write_text(data_js, encoding="utf-8")


def main() -> None:
    script_path = Path(__file__).resolve()
    root = script_path.parents[1]
    output_dir = root / "docs"
    write_site(root, output_dir)
    print(f"Generated site at: {output_dir}")


if __name__ == "__main__":
    main()
