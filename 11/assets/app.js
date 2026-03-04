/* build:20260304081752 */
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
    return `<a class="file" href="#${encodeURIComponent(node.path)}" data-path="${esc(node.path)}">${esc(node.name)}</a>`;
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

      return `<article class="project-card">        <h4>${esc(project)}</h4>        <p><strong>Files:</strong> ${info.files}</p>        <p><strong>Total lines:</strong> ${info.lines}</p>        <p><strong>Main file types:</strong> ${esc(topTypes || 'N/A')}</p>      </article>`;
    })
    .join('');

  container.innerHTML = cards || '<p class="empty">No project folders found.</p>';
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
  const normalized = String(source).replace(/\r/g, '');
  const lines = normalized.split('\n');

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

  html = html.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a class="ext-link" href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  html = html.replace(/@@CODE(\d+)@@/g, (_, index) => `<code>${codeChunks[Number(index)]}</code>`);
  return html;
}

function renderMarkdownDocument(source) {
  const lines = String(source || '').replace(/\r/g, '').split('\n');
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
      if (/^\s*```/.test(line)) {
        const codeText = esc(codeLines.join('\n'));
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

    const fenceMatch = line.match(/^\s*```\s*([A-Za-z0-9_+.-]+)?\s*$/);
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

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      closeLists();
      const level = heading[1].length;
      out.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    if (/^(?:\*\s*\*\s*\*|-{3,}|_{3,})\s*$/.test(line.trim())) {
      flushParagraph();
      closeLists();
      out.push('<hr/>');
      continue;
    }

    const ulItem = line.match(/^\s*[-*+]\s+(.+)$/);
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

    const olItem = line.match(/^\s*\d+\.\s+(.+)$/);
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

    const quote = line.match(/^>\s?(.*)$/);
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
    const codeText = esc(codeLines.join('\n'));
    const langClass = codeLang ? ` class="language-${esc(codeLang)}"` : '';
    out.push(`<pre><code${langClass}>${codeText}</code></pre>`);
  }

  return out.join('\n');
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
    ? file.features.map(f => `<span class="badge">${esc(f)}</span>`).join('')
    : '<span class="empty">No specific C++11 pattern heuristics detected.</span>';

  const includes = file.includes.length
    ? `<ul>${file.includes.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`
    : '<p class="empty">No include directives found.</p>';

  const functions = file.functions.length
    ? `<ul>${file.functions.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`
    : '<p class="empty">No function signatures detected.</p>';

  const classes = file.classes.length
    ? `<ul>${file.classes.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`
    : '<p class="empty">No class/struct declarations detected.</p>';

  const lineNotes = file.lineNotes.length
    ? `<table class="table"><thead><tr><th>Line</th><th>Commentary</th></tr></thead><tbody>${file.lineNotes.map(n => `<tr><td>${n.line}</td><td>${esc(n.note)}</td></tr>`).join('')}</tbody></table>`
    : '<p class="empty">No line-level notes generated for this file.</p>';

  const numberedSource = renderCodeWithLineNumbers(file.code, file);

  content.innerHTML = `
    <article class="panel">
      <h2>${esc(file.path)}</h2>
      <p>${esc(file.summary)}</p>
      <div class="meta">
        <div><strong>Directory:</strong><br/>${esc(file.directory)}</div>
        <div><strong>Extension:</strong><br/>${esc(file.extension)}</div>
        <div><strong>Lines:</strong><br/>${file.lineCount}</div>
        <div><strong>Approx complexity:</strong><br/>${esc(file.complexity)}</div>
      </div>
    </article>

    <section class="panel">
      <h3>What This Example Demonstrates</h3>
      <ul>${file.demonstrates.map(d => `<li>${esc(d)}</li>`).join('')}</ul>
    </section>

    <section class="panel">
      <h3>Detected C++ Features</h3>
      <div>${features}</div>
    </section>

    <section class="panel">
      <h3>Headers / Includes</h3>
      ${includes}
    </section>

    <section class="panel">
      <h3>Classes and Structs</h3>
      ${classes}
    </section>

    <section class="panel">
      <h3>Functions</h3>
      ${functions}
    </section>

    <section class="panel">
      <h3>Line-by-Line Commentary</h3>
      ${lineNotes}
    </section>

    <section class="panel">
      <h3>Full Source</h3>
      ${numberedSource}
    </section>
  `;

  content.scrollTop = 0;
  window.scrollTo(0, 0);
  document.querySelectorAll('.file').forEach(el => el.classList.remove('active'));
  const active = document.querySelector(`.file[data-path="${CSS.escape(file.path)}"]`);
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
  treeRoot.innerHTML = filtered ? renderTreeNode(filtered) : '<p class="empty">No matches found.</p>';
}

document.getElementById('siteMeta').textContent = `Generated ${data.generatedAt} • ${data.files.length} files indexed`;
initTree();
renderOverview();
openFromHash();

window.addEventListener('hashchange', openFromHash);
search.addEventListener('input', () => initTree(search.value));
