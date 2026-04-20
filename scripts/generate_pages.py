#!/usr/bin/env python3
"""
generate_pages.py
-----------------
Reads all category Markdown files from categories/ and regenerates
docs/index.html — a single-page searchable GitHub Pages site.

Run from the repo root:
    python3 scripts/generate_pages.py
"""

import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORIES_DIR = os.path.join(REPO_ROOT, "categories")
OUT_PATH = os.path.join(REPO_ROOT, "docs", "index.html")


def parse_categories() -> list[dict]:
    """Parse all category Markdown files and return a flat list of company dicts."""
    companies = []
    for fname in sorted(os.listdir(CATEGORIES_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(CATEGORIES_DIR, fname)
        with open(fpath, encoding="utf-8") as f:
            content = f.read()

        # Category heading
        heading_m = re.search(r"^# (.+)$", content, re.MULTILINE)
        category = (
            heading_m.group(1).strip()
            if heading_m
            else fname.replace(".md", "").replace("-", " ").title()
        )

        # Parse table rows
        row_pattern = re.compile(
            r"<tr><td><strong><a href=\"([^\"]+)\">([^<]+)</a></strong></td>"
            r"<td>(.*?)</td>"   # description
            r"<td>(.*?)</td>"   # oss project
            r"<td>(.*?)</td>"   # website
            r"<td>(.*?)</td>"   # headlines (legacy img cell — may be present)
            r"<td>(.*?)</td></tr>",  # technologies
            re.DOTALL,
        )

        for m in row_pattern.finditer(content):
            cossmology_url = m.group(1).strip()
            name = m.group(2).strip()
            description = m.group(3).strip()
            oss_cell = m.group(4).strip()
            website_cell = m.group(5).strip()
            # group(6) = legacy headlines img cell (ignored — we regenerate it)
            tech_cell = m.group(7).strip()

            oss_m = re.search(r'<a href="([^"]+)">([^<]+)</a>', oss_cell)
            oss_url = oss_m.group(1) if oss_m else ""
            oss_name = oss_m.group(2) if oss_m else ""

            web_m = re.search(r'<a href="([^"]+)">', website_cell)
            website_url = web_m.group(1) if web_m else ""

            tech_tags = re.findall(r"<code>([^<]+)</code>", tech_cell)

            shortname_m = re.search(r"/organizations/([^/\"]+)", cossmology_url)
            shortname = shortname_m.group(1) if shortname_m else ""

            companies.append(
                {
                    "name": name,
                    "shortname": shortname,
                    "category": category,
                    "description": description,
                    "cossmology_url": cossmology_url,
                    "oss_url": oss_url,
                    "oss_name": oss_name,
                    "website_url": website_url,
                    "tech_tags": tech_tags,
                }
            )

    return companies


def deduplicate(companies: list[dict]) -> list[dict]:
    """Keep one entry per shortname (first encountered, alphabetically by category)."""
    seen: dict[str, dict] = {}
    result = []
    for c in companies:
        key = c["shortname"]
        if key not in seen:
            seen[key] = c
            result.append(c)
    return result


def build_html(companies: list[dict]) -> str:
    companies = sorted(companies, key=lambda c: c["name"].lower())
    all_categories = sorted(set(c["category"] for c in companies))
    data_json = json.dumps(companies, ensure_ascii=False)

    category_options = "\n      ".join(
        f'<option value="{cat}">{cat}</option>' for cat in all_categories
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Awesome OSS Companies | Cossmology</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}

    :root {{
      --navy:   #00274c;
      --yellow: #ffcb05;
      --green:  #16a34a;
      --bg:     #f9fafb;
      --white:  #ffffff;
      --text:   #111827;
      --muted:  #6b7280;
      --border: #e5e7eb;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background: var(--bg);
      color: var(--text);
    }}

    header {{
      background: var(--navy);
      padding: 0 24px;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}

    .header-top {{
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      padding: 14px 0 10px;
      border-bottom: 1px solid rgba(255,203,5,0.25);
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      text-decoration: none;
      flex-shrink: 0;
    }}
    .brand-text {{ display: flex; flex-direction: column; }}
    .brand-name {{
      font-size: 1.25rem;
      font-weight: 800;
      color: var(--yellow);
      letter-spacing: -0.01em;
      line-height: 1.1;
    }}
    .brand-sub {{
      font-size: 0.7rem;
      color: rgba(255,255,255,0.55);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}

    .header-title {{ flex: 1; min-width: 0; }}
    .header-title h1 {{
      margin: 0;
      font-size: 1.3rem;
      font-weight: 800;
      color: var(--yellow);
      letter-spacing: -0.01em;
      line-height: 1.15;
    }}
    .header-title p {{
      margin: 3px 0 0;
      font-size: 0.75rem;
      color: rgba(255,255,255,0.6);
    }}
    .header-title p a {{
      color: rgba(255,255,255,0.85);
      text-decoration: underline;
      text-underline-offset: 2px;
    }}
    .header-title p a:hover {{ color: var(--yellow); }}

    .github-link {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--navy);
      background: var(--yellow);
      text-decoration: none;
      border-radius: 6px;
      padding: 6px 12px;
      white-space: nowrap;
      flex-shrink: 0;
      transition: opacity 0.15s;
    }}
    .github-link:hover {{ opacity: 0.88; }}

    /* Measure sticky header height so table thead can offset correctly */
    header {{ --header-height: 0px; }}

    .controls {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      padding: 10px 0 12px;
    }}

    .controls input[type="search"] {{
      flex: 1;
      min-width: 200px;
      max-width: 480px;
      padding: 8px 12px;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 6px;
      font-size: 0.875rem;
      outline: none;
      background: rgba(255,255,255,0.1);
      color: var(--white);
    }}
    .controls input[type="search"]::placeholder {{ color: rgba(255,255,255,0.45); }}
    .controls input[type="search"]:focus {{
      border-color: var(--yellow);
      background: rgba(255,255,255,0.15);
      box-shadow: 0 0 0 3px rgba(255,203,5,0.2);
    }}

    .controls select {{
      padding: 8px 10px;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 6px;
      font-size: 0.875rem;
      background: rgba(255,255,255,0.1);
      color: var(--white);
      cursor: pointer;
      outline: none;
      max-width: 240px;
    }}
    .controls select option {{ background: var(--navy); color: var(--white); }}
    .controls select:focus {{ border-color: var(--yellow); }}

    .clear-btn {{
      padding: 8px 12px;
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 6px;
      font-size: 0.82rem;
      background: transparent;
      cursor: pointer;
      color: rgba(255,255,255,0.7);
      transition: all 0.15s;
    }}
    .clear-btn:hover {{ background: rgba(255,255,255,0.1); color: var(--white); }}

    .stats {{
      font-size: 0.8rem;
      color: rgba(255,255,255,0.55);
      white-space: nowrap;
      padding: 8px 0;
    }}

    main {{
      padding: 20px 24px;
      max-width: 1500px;
      margin: 0 auto;
    }}

    .table-wrap {{
      border: 1px solid var(--border);
      border-radius: 8px;
    }}

    /* Round the first/last th and td corners to match the wrapper border-radius */
    thead tr:first-child th:first-child {{ border-top-left-radius: 7px; }}
    thead tr:first-child th:last-child  {{ border-top-right-radius: 7px; }}
    tbody tr:last-child td:first-child  {{ border-bottom-left-radius: 7px; }}
    tbody tr:last-child td:last-child   {{ border-bottom-right-radius: 7px; }}

    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      background: var(--white);
      font-size: 0.855rem;
      table-layout: fixed;
    }}

    .thead-hint td {{
      position: sticky;
      top: var(--header-height, 0px);
      z-index: 10;
      background: var(--navy);
      padding: 5px 12px 4px;
      text-align: center;
      font-size: 0.78rem;
      font-style: italic;
      color: rgba(255,255,255,0.65);
      font-weight: 400;
      letter-spacing: 0.01em;
      border-bottom: none;
      box-shadow: none;
    }}

    thead th {{
      position: sticky;
      top: calc(var(--header-height, 0px) + 29px);
      z-index: 10;
      background: var(--navy);
      color: var(--yellow);
      border-bottom: 2px solid var(--yellow);
      padding: 10px 12px;
      text-align: left;
      font-weight: 700;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }}

    th:nth-child(1), td:nth-child(1) {{ width: 12%; }}
    th:nth-child(2), td:nth-child(2) {{ width: 22%; }}
    th:nth-child(3), td:nth-child(3) {{ width: 10%; }}
    th:nth-child(4), td:nth-child(4) {{ width: 10%; }}
    th:nth-child(5), td:nth-child(5) {{ width: 9%;  }}
    th:nth-child(6), td:nth-child(6) {{ width: 9%; text-align: center; }}
    th:nth-child(7), td:nth-child(7) {{ width: 28%; }}

    tbody tr td {{
      border-bottom: 1px solid var(--border);
    }}
    tbody tr:last-child td {{ border-bottom: none; }}
    tbody tr {{
      transition: background 0.1s;
    }}
    tbody tr:hover {{ background: #fffbeb; }}

    td {{
      padding: 10px 12px;
      vertical-align: top;
      word-wrap: break-word;
      overflow-wrap: break-word;
    }}

    td a {{ color: #004a9f; text-decoration: none; font-weight: 500; }}
    td a:hover {{ color: var(--navy); text-decoration: underline; }}

    .company-name {{ font-weight: 700; color: var(--navy); }}

    td.headlines-cell {{
      text-align: center;
    }}
    .headlines-link {{
      display: inline-block;
      text-decoration: none !important;
      transition: opacity 0.15s;
      line-height: 0;
    }}
    .headlines-link img {{
      width: 64px;
      height: 64px;
      display: block;
    }}
    .headlines-link:hover {{ opacity: 0.8; }}

    .tag {{
      display: inline-block;
      background: #fffbeb;
      color: #7d4e00;
      border: 1px solid #fde68a;
      border-radius: 4px;
      padding: 1px 6px;
      font-size: 0.71rem;
      margin: 1px 2px 1px 0;
      white-space: nowrap;
    }}

    .category-badge {{
      display: inline-block;
      background: #e0f0ff;
      color: #003a7a;
      border: 1px solid #b3d4f5;
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 0.76rem;
      font-weight: 600;
    }}

    .no-results {{
      text-align: center;
      padding: 60px 20px;
      color: var(--muted);
      font-size: 1rem;
    }}

    @media (max-width: 1100px) {{
      th:nth-child(7), td:nth-child(7) {{ display: none; }}
    }}
    @media (max-width: 860px) {{
      main {{ padding: 12px; }}
      header {{ padding: 0 12px; }}
      th:nth-child(3), td:nth-child(3) {{ display: none; }}
    }}
    @media (max-width: 600px) {{
      th:nth-child(4), td:nth-child(4) {{ display: none; }}
      th:nth-child(5), td:nth-child(5) {{ display: none; }}
    }}
  </style>
</head>
<body>

<header>
  <div class="header-top">
    <div class="header-title">
      <h1>Awesome OSS Companies</h1>
      <p>Maintained by <a href="https://chinstrap.community" target="_blank" rel="noopener">Chinstrap Community</a> and <a href="https://puter.com" target="_blank" rel="noopener">Puter</a>. Data mirrored from <a href="https://cossmology.com" target="_blank" rel="noopener">Cossmology</a>.</p>
    </div>
    <a class="github-link" href="https://github.com/Chinstrap-Community/Awesome-OSS-Companies" target="_blank" rel="noopener">
      <svg height="15" viewBox="0 0 16 16" width="15" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      View on GitHub
    </a>
  </div>
  <div class="controls">
    <input type="search" id="searchInput" placeholder="Search companies, descriptions, technologies..." autocomplete="off">
    <select id="categoryFilter">
      <option value="">All categories ({len(all_categories)})</option>
      {category_options}
    </select>
    <button class="clear-btn" id="clearBtn">Clear</button>
    <span class="stats" id="stats"></span>
  </div>
</header>

<main>
  <div class="table-wrap">
  <table id="companiesTable">
    <thead>
      <tr class="thead-hint">
        <td colspan="7">Click on a company&#8217;s name to see its Cossmology profile!</td>
      </tr>
      <tr>
        <th>Company</th>
        <th>Description</th>
        <th>Category</th>
        <th>Core OSS Repo</th>
        <th>Website</th>
        <th>Headlines</th>
        <th>Technologies</th>
      </tr>
    </thead>
    <tbody id="tableBody"></tbody>
  </table>
  </div>
  <div class="no-results" id="noResults" style="display:none;">No companies match your search.</div>
</main>

<script>
const COMPANIES = {data_json};

const tbody = document.getElementById('tableBody');
const searchInput = document.getElementById('searchInput');
const categoryFilter = document.getElementById('categoryFilter');
const clearBtn = document.getElementById('clearBtn');
const statsEl = document.getElementById('stats');
const noResults = document.getElementById('noResults');
const table = document.getElementById('companiesTable');

function buildRow(c) {{
  const techTags = c.tech_tags.map(t => `<span class="tag">${{t}}</span>`).join('');
  const ossCell = c.oss_url
    ? `<a href="${{c.oss_url}}" target="_blank" rel="noopener">${{c.oss_name || c.oss_url}}</a>`
    : '';
  const websiteCell = c.website_url
    ? `<a href="${{c.website_url}}" target="_blank" rel="noopener">${{c.name}}</a>`
    : '';
  const headlinesUrl = `https://cossmology.com/organizations/${{c.shortname}}/headlines`;
  const headlinesCell = `<a class="headlines-link" href="${{headlinesUrl}}" target="_blank" rel="noopener" title="View headlines on Cossmology"><img src="https://cossmology.com/cossmology_headlines_transparent_bg_154.png" alt="Headlines" loading="lazy"></a>`;
  const companyCell = `<a class="company-name" href="${{c.cossmology_url}}" target="_blank" rel="noopener">${{c.name}}</a>`;
  const categoryCell = `<span class="category-badge">${{c.category}}</span>`;

  return `<tr data-name="${{c.name.toLowerCase()}}" data-desc="${{c.description.toLowerCase()}}" data-cat="${{c.category.toLowerCase()}}" data-tags="${{c.tech_tags.join(' ').toLowerCase()}}">
    <td>${{companyCell}}</td>
    <td>${{c.description}}</td>
    <td>${{categoryCell}}</td>
    <td>${{ossCell}}</td>
    <td>${{websiteCell}}</td>
    <td class="headlines-cell">${{headlinesCell}}</td>
    <td>${{techTags}}</td>
  </tr>`;
}}

tbody.innerHTML = COMPANIES.map(buildRow).join('');
const allRows = Array.from(tbody.querySelectorAll('tr'));

function updateStats(shown, total) {{
  statsEl.textContent = shown === total
    ? `${{total.toLocaleString()}} companies`
    : `${{shown.toLocaleString()}} of ${{total.toLocaleString()}} companies`;
}}

function filterTable() {{
  const query = searchInput.value.toLowerCase().trim();
  const cat = categoryFilter.value.toLowerCase();
  let shown = 0;

  for (const row of allRows) {{
    const matchSearch = !query ||
      row.dataset.name.includes(query) ||
      row.dataset.desc.includes(query) ||
      row.dataset.tags.includes(query) ||
      row.dataset.cat.includes(query);
    const matchCat = !cat || row.dataset.cat === cat;

    if (matchSearch && matchCat) {{
      row.style.display = '';
      shown++;
    }} else {{
      row.style.display = 'none';
    }}
  }}

  updateStats(shown, allRows.length);
  noResults.style.display = shown === 0 ? 'block' : 'none';
  table.style.display = shown === 0 ? 'none' : '';
}}

searchInput.addEventListener('input', filterTable);
categoryFilter.addEventListener('change', filterTable);
clearBtn.addEventListener('click', () => {{
  searchInput.value = '';
  categoryFilter.value = '';
  filterTable();
  searchInput.focus();
}});

filterTable();

// Set sticky offsets: hint row sits just below the sticky nav header;
// column-name th row sits below the hint row.
function setHeaderHeight() {{
  const navH = document.querySelector('header').getBoundingClientRect().height;
  const hintRow = document.querySelector('.thead-hint td');
  if (hintRow) {{
    hintRow.style.top = navH + 'px';
    // Measure hint row height after positioning
    const hintH = hintRow.getBoundingClientRect().height;
    document.querySelectorAll('thead th').forEach(th => {{
      th.style.top = (navH + hintH) + 'px';
    }});
  }} else {{
    document.querySelectorAll('thead th').forEach(th => {{
      th.style.top = navH + 'px';
    }});
  }}
}}
setHeaderHeight();
window.addEventListener('resize', setHeaderHeight);
</script>
</body>
</html>
"""


def main():
    print("Parsing category files...")
    companies = parse_categories()
    print(f"  Found {len(companies)} total entries")

    companies = deduplicate(companies)
    print(f"  After deduplication: {len(companies)} unique companies")

    html = build_html(companies)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"Written: {OUT_PATH} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
