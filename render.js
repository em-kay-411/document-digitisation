#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const inputPath = process.argv[2];
if (!inputPath) {
  console.error('Usage: node render.js <path-to-output.json>');
  process.exit(1);
}

const resolved = path.resolve(inputPath);
if (!fs.existsSync(resolved)) {
  console.error(`File not found: ${resolved}`);
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(resolved, 'utf8'));
const outputPath = path.join(path.dirname(resolved), 'form.html');

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderField(field) {
  const id = esc(field.field_id);
  const label = esc(field.label);
  const placeholder = esc(field.placeholder || '');
  const helpText = field.help_text ? `<p class="help-text">${esc(field.help_text)}</p>` : '';
  const required = field.required ? ' required' : '';
  const requiredMark = field.required ? ' <span class="req">*</span>' : '';
  const maxlength = field.validation?.max_length ? ` maxlength="${field.validation.max_length}"` : '';
  const pattern = field.validation?.pattern ? ` pattern="${esc(field.validation.pattern)}"` : '';

  let input = '';

  switch (field.type) {
    case 'text':
      input = `<input type="text" id="${id}" name="${id}" placeholder="${placeholder}"${maxlength}${pattern}${required}>`;
      break;

    case 'date':
      input = `<input type="date" id="${id}" name="${id}" placeholder="${placeholder}"${required}>`;
      break;

    case 'checkbox':
      return `<div class="field checkbox-field">
        <label class="checkbox-label"><input type="checkbox" id="${id}" name="${id}"${required}> ${label}${requiredMark}</label>
        ${helpText}
      </div>`;

    case 'radio': {
      const options = field.options || ['Option 1', 'Option 2', 'Option 3'];
      const radios = options.map((opt, i) =>
        `<label class="radio-label"><input type="radio" name="${id}" value="${esc(opt)}"${i === 0 ? required : ''}> ${esc(opt)}</label>`
      ).join('\n          ');
      return `<div class="field">
        <label class="field-label">${label}${requiredMark}</label>
        <div class="radio-group">${radios}</div>
        ${helpText}
      </div>`;
    }

    case 'dropdown': {
      const options = (field.options || []).map(opt =>
        `<option value="${esc(opt)}">${esc(opt)}</option>`
      ).join('');
      input = `<select id="${id}" name="${id}"${required}>
          ${options || `<option value="">-- Select --</option>`}
        </select>`;
      break;
    }

    case 'signature':
      input = `<input type="text" id="${id}" name="${id}" class="signature-input" placeholder="Sign here"${required}>`;
      break;

    default:
      input = `<input type="text" id="${id}" name="${id}" placeholder="${placeholder}"${maxlength}${pattern}${required}>`;
  }

  return `<div class="field">
    <label class="field-label" for="${id}">${label}${requiredMark}</label>
    ${input}
    ${helpText}
  </div>`;
}

function renderSection(section) {
  const sid = esc(section.section_id);
  const title = esc(section.title);
  const fields = (section.fields || []).map(renderField).join('\n');
  return `<section id="${sid}" class="form-section">
    <h2 class="section-heading">${title}</h2>
    ${fields}
  </section>`;
}

const sections = data.sections || [];

const sidebarLinks = sections.map(s =>
  `<a href="#${esc(s.section_id)}" class="sidebar-link" data-section="${esc(s.section_id)}">${esc(s.title)}</a>`
).join('\n        ');

const sectionsHtml = sections.map(renderSection).join('\n');

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(data.title || 'Form')}</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #1a1a1a;
  background: #f5f5f5;
  line-height: 1.5;
}

.sidebar {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: 240px;
  background: #fafafa;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  padding: 24px 0;
  z-index: 10;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 20px 16px;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 8px;
}

.sidebar-link {
  display: block;
  padding: 8px 20px;
  color: #444;
  text-decoration: none;
  font-size: 14px;
  border-left: 3px solid transparent;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.sidebar-link:hover {
  background: #eee;
  color: #111;
}

.sidebar-link.active {
  border-left-color: #2563eb;
  color: #2563eb;
  background: #eff6ff;
  font-weight: 500;
}

.main {
  margin-left: 240px;
  padding: 32px 40px;
}

.main-inner {
  max-width: 720px;
  margin: 0 auto;
}

.form-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 32px;
  color: #111;
}

.form-section {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 24px 28px;
  margin-bottom: 24px;
}

.section-heading {
  font-size: 18px;
  font-weight: 600;
  color: #111;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.field {
  margin-bottom: 20px;
}

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 6px;
}

.req {
  color: #dc2626;
  font-weight: 700;
}

input[type="text"],
input[type="date"],
select {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #1a1a1a;
  transition: border-color 0.15s, box-shadow 0.15s;
  font-family: inherit;
}

input[type="text"]:focus,
input[type="date"]:focus,
select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.15);
}

select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

.signature-input {
  font-family: "Brush Script MT", "Segoe Script", cursive;
  font-size: 20px;
  padding: 10px 14px;
  border-style: dashed;
}

.checkbox-field {
  padding: 4px 0;
}

.checkbox-label,
.radio-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 0;
}

input[type="checkbox"],
input[type="radio"] {
  width: 16px;
  height: 16px;
  accent-color: #2563eb;
  flex-shrink: 0;
}

.help-text {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .sidebar {
    position: static;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
    padding: 12px 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0;
    overflow-x: auto;
  }

  .sidebar-title {
    width: 100%;
    padding: 0 16px 8px;
    border-bottom: 1px solid #e0e0e0;
    margin-bottom: 4px;
  }

  .sidebar-link {
    border-left: none;
    border-bottom: 2px solid transparent;
    padding: 6px 14px;
    white-space: nowrap;
    font-size: 13px;
  }

  .sidebar-link.active {
    border-left-color: transparent;
    border-bottom-color: #2563eb;
    background: transparent;
  }

  .main {
    margin-left: 0;
    padding: 20px 16px;
  }

  .form-section {
    padding: 16px 18px;
  }
}
</style>
</head>
<body>

<nav class="sidebar">
  <div class="sidebar-title">Sections</div>
  ${sidebarLinks}
</nav>

<main class="main">
  <div class="main-inner">
    <h1 class="form-title">${esc(data.title || 'Form')}</h1>
    ${sectionsHtml}
  </div>
</main>

<script>
(function() {
  var links = document.querySelectorAll('.sidebar-link');
  var headings = document.querySelectorAll('.section-heading');

  // Smooth scroll on click
  links.forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      var target = document.querySelector(link.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  // Scroll-spy via IntersectionObserver
  if ('IntersectionObserver' in window) {
    var current = null;
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          var sectionId = entry.target.closest('.form-section').id;
          if (sectionId !== current) {
            current = sectionId;
            links.forEach(function(l) {
              l.classList.toggle('active', l.dataset.section === sectionId);
            });
          }
        }
      });
    }, { rootMargin: '0px 0px -70% 0px', threshold: 0 });

    headings.forEach(function(h) { observer.observe(h); });
  }
})();
</script>

</body>
</html>`;

fs.writeFileSync(outputPath, html, 'utf8');
console.log(`Generated: ${outputPath}`);
