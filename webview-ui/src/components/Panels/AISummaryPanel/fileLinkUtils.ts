/**
 * Detection + tokenization helpers for turning filenames mentioned in an
 * assistant reply into clickable links.
 *
 * A filename is matched by its basename (name + extension). Any leading path
 * segments in the text (e.g. `src/utils/foo.py`) are ignored for matching —
 * only the last segment (`foo.py`) is captured, consistent with the
 * "same name and extension" rule used when resolving duplicates.
 */

// Broad set of common source / programming file extensions.
export const SUPPORTED_EXTENSIONS = [
  "py",
  "ts",
  "tsx",
  "js",
  "jsx",
  "cpp",
  "c",
  "cc",
  "h",
  "hpp",
  "cs",
  "java",
  "go",
  "rs",
  "rb",
  "php",
  "swift",
  "kt",
  "kts",
  "scala",
  "m",
  "mm",
  "sql",
  "sh",
  "bash",
  "css",
  "scss",
  "less",
  "html",
  "vue",
  "dart",
  "lua",
  "r",
  "jl",
  "ex",
  "exs",
  "json",
  "yaml",
  "yml",
  "xml",
  "md",
] as const;

// Matches a basename token ending in a supported extension. The character
// class before the dot excludes path separators so only the final segment of a
// path is captured. Extensions are ordered longest-first so e.g. `.tsx` wins
// over `.ts`.
const EXTENSION_ALTERNATION = [...SUPPORTED_EXTENSIONS]
  .sort((a, b) => b.length - a.length)
  .join("|");

export const FILE_NAME_REGEX = new RegExp(
  `[\\w.-]*[\\w-]\\.(?:${EXTENSION_ALTERNATION})(?![\\w])`,
  "gi",
);

export interface ResolvedFile {
  path: string;
  relativePath: string;
}

export type ResolvedFileMap = Record<string, ResolvedFile[]>;

export type ContentToken =
  | { type: "text"; value: string }
  | { type: "file"; name: string; matches: ResolvedFile[] };

/** Return the de-duplicated list of filename basenames mentioned in `content`. */
export function extractFileNames(content: string): string[] {
  if (!content) return [];
  const names = new Set<string>();
  for (const match of content.matchAll(FILE_NAME_REGEX)) {
    names.add(match[0]);
  }
  return [...names];
}

/**
 * Split `content` into an ordered list of plain-text runs and file tokens.
 * Each file token carries the workspace matches resolved for that name (empty
 * array when unresolved or not found).
 */
export function tokenizeContent(
  content: string,
  resolved: ResolvedFileMap = {},
): ContentToken[] {
  if (!content) return [];

  const tokens: ContentToken[] = [];
  let lastIndex = 0;
  // matchAll gives a fresh iterator; the regex is global so indices advance.
  for (const match of content.matchAll(FILE_NAME_REGEX)) {
    const name = match[0];
    const start = match.index ?? 0;

    if (start > lastIndex) {
      tokens.push({ type: "text", value: content.slice(lastIndex, start) });
    }

    tokens.push({ type: "file", name, matches: resolved[name] ?? [] });
    lastIndex = start + name.length;
  }

  if (lastIndex < content.length) {
    tokens.push({ type: "text", value: content.slice(lastIndex) });
  }

  return tokens;
}
