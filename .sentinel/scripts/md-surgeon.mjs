#!/usr/bin/env node
/* ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0010 */

// Safe, surgical Markdown edits with UTF-8 + code-fence checks.
//
// Quick-start for future agents
// -----------------------------
// 1. Maintain snippets under `.sentinel/snippets/<name>.md` (commit them).
//    These files contain the exact Markdown you want rendered, so you never fight shell quoting.
// 2. Insert/update a block via md-surgeon:
//      node .sentinel/scripts/md-surgeon.mjs \
//          --file=README.md \
//          --marker=SENTINEL:DECISION-LOG \
//          --heading="Decision & Provenance Workflow" \
//          --content=.sentinel/snippets/decision-log.md \
//          --mode=replace
//    • First run with `--heading` creates the block beneath that heading and wraps it with
//      `<!-- SENTINEL:... start/end -->`.
//    • Subsequent runs only need `--marker`, `--content`, and `--mode=replace`; the script finds
//      the markers and swaps that region automatically.
// 3. Prefer snippet files, but stdin works too:
//      type snippet.md | node .sentinel/scripts/md-surgeon.mjs --file=README.md \
//          --marker=SENTINEL:FOO --mode=replace
// 4. Want to append a brand-new block at the end of a doc? Use `--mode=append` (no heading).
//
// Safety rails
// ------------
// • Creates a `.bak` backup before each write.
// • Aborts if code fences (```/~~~) are unbalanced in either the snippet or the final doc.
// • Errors if you try to `--mode=insert` when markers already exist.
//
// TL;DR: write/update snippets once, run md-surgeon, and never hand-edit inside the marker block.



import { readFile, writeFile, copyFile } from "node:fs/promises";
import { basename } from "node:path";

const args = Object.fromEntries(process.argv.slice(2).map(a=>{
  const m = a.match(/^--([^=]+)=(.*)$/); return m ? [m[1], m[2]] : [a.replace(/^--/,""), true];
}));

const required = (k) => { if(!args[k]) fail(`missing --${k}`); return args[k]; };
const file = required("file");
const marker = required("marker");               // e.g., SENTINEL:DECISION-LOG
const contentPath = args["content"];             // optional: path to snippet
const heading = args["heading"];                 // optional: insert after this H2/H3
const mode = args["mode"] || "replace";          // replace | insert | append
const backup = args["backup"] ?? true;

const START = `<!-- ${marker}:start -->`;
const END   = `<!-- ${marker}:end -->`;

function fail(msg, code=1){ console.error(`md-surgeon: ${msg}`); process.exit(code); }
function normLF(s){ return s.replace(/\r\n/g, "\n"); }

async function loadContent(){
  if (contentPath) return normLF(await readFile(contentPath, "utf8"));
  // read from stdin (no shell quoting pain)
  return await new Promise((resolve)=>{
    let buf=""; process.stdin.setEncoding("utf8");
    process.stdin.on("data", c=>buf+=c); process.stdin.on("end", ()=>resolve(normLF(buf)));
  });
}

function hasBalancedFences(md){
  // naive but effective: ensure each fence type opens/closes evenly
  const ticks = (md.match(/^```/gm) || []).length;
  const tildes = (md.match(/^~~~/gm) || []).length;
  return (ticks % 2 === 0) && (tildes % 2 === 0);
}

function insertAfterHeading(doc, headingText, block){
  const hRegex = new RegExp(`^#{2,6}\\s+${escapeRegex(headingText)}\\s*$`, "m");
  const m = doc.match(hRegex);
  if(!m) return null;
  const idx = m.index + m[0].length;
  const before = doc.slice(0, idx);
  const after  = doc.slice(idx);
  const leadNl = /\n$/.test(before) ? "" : "\n";
  return `${before}${leadNl}\n\n${block}\n\n${after}`;
}

function escapeRegex(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }

(async () => {
  let doc = normLF(await readFile(file, {encoding: "utf8"}));
  const snippet = await loadContent();

  if (!hasBalancedFences(snippet)) fail("snippet has unbalanced code fences");

  const startIdx = doc.indexOf(START);
  const endIdx   = doc.indexOf(END);

  if (backup) await copyFile(file, `${file}.bak`);

  if (startIdx !== -1 && endIdx !== -1 && endIdx > startIdx) {
    if (mode === "insert") fail("markers exist; use --mode=replace for existing region");
    // replace region
    const head = doc.slice(0, startIdx);
    const tail = doc.slice(endIdx + END.length);
    doc = `${head}${START}\n${snippet.trim()}\n${END}${tail}`;
  } else if (heading) {
    // insert new marked block after a heading
    const block = `${START}\n${snippet.trim()}\n${END}`;
    const updated = insertAfterHeading(doc, heading, block);
    if (!updated) fail(`heading "${heading}" not found`);
    doc = updated;
  } else if (mode === "append") {
    // append at end
    const sep = /\n$/.test(doc) ? "" : "\n";
    doc = `${doc}${sep}\n\n${START}\n${snippet.trim()}\n${END}\n`;
  } else {
    fail("no existing markers; provide --heading to place the block or --mode=append");
  }

  if (!hasBalancedFences(doc)) {
    fail("resulting document has unbalanced code fences; write aborted");
  }
  const hasNonAscii = [...doc].some((char) => char.charCodeAt(0) > 0x7f);
  if (hasNonAscii && doc.includes("\uFFFD")) {
    fail("replacement character detected; encoding issue");
  }

  await writeFile(file, doc, { encoding: "utf8" });
  console.log(`md-surgeon: ok -> ${basename(file)} [marker=${marker}]`);
})().catch(e=>fail(e?.message||String(e)));

