// @ts-check
/* ProducedBy=BUILDER RulesHash=BUILDER@1.2 Decision=D-0012 */
/**
 * Capsule markdown helpers shared across context tooling.
 */

/**
 * Extract the lines belonging to a markdown heading.
 * @param {string} markdown
 * @param {string} heading
 * @returns {string}
 */
export function extractSection(markdown, heading) {
  const lines = markdown.split(/\r?\n/);
  const matcher = new RegExp(`^(#{1,6})\\s+${escapeRegExp(heading)}\\s*$`, "i");
  let capturing = false;
  let depth = 0;
  const bucket = [];

  for (const line of lines) {
    const headerMatch = line.match(/^(#{1,6})\s+(.*?)\s*$/);
    if (headerMatch) {
      if (matcher.test(line)) {
        capturing = true;
        depth = headerMatch[1].length;
        continue;
      }
      if (capturing && headerMatch[1].length <= depth) break;
    }
    if (capturing) bucket.push(line);
  }

  return bucket.join("\n").trim();
}

/**
 * Convert a markdown list section into discrete bullet strings.
 * @param {string} section
 * @returns {string[]}
 */
export function extractList(section) {
  const lines = section.split(/\r?\n/);
  const items = [];
  let current = "";
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const bullet = line.match(/^([-*]|\d+\.)\s+(.*)$/);
    if (bullet) {
      if (current) items.push(current);
      current = bullet[2].trim();
    } else if (current) {
      current = `${current} ${line}`;
    } else {
      current = line;
    }
  }
  if (current) items.push(current);
  return items;
}

/**
 * Convenience helper for Allowed Context extraction.
 * @param {string} markdown
 * @param {string} heading
 */
export function extractListFromHeading(markdown, heading) {
  const section = extractSection(markdown, heading);
  return section ? extractList(section) : [];
}

/**
 * @param {string} str
 */
function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export default {
  extractSection,
  extractList,
  extractListFromHeading
};
