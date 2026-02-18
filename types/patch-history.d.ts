/**
 * Patch History Type Definitions
 *
 * TypeScript types for the Spellcasters Community API patch history system.
 * These mirror the JSON schemas in schemas/v2/.
 *
 * Endpoints:
 *   - changelog_index.json      → ChangelogIndex
 *   - changelog_page_N.json     → ChangelogPage
 *   - changelog_latest.json     → ChangelogLatest
 *   - timeline/{entity_id}.json → EntityTimeline
 *
 * @module patch-history
 */

// ---------------------------------------------------------------------------
// Changelog
// ---------------------------------------------------------------------------

/** Type of change made to an entity. */
export type ChangeType = "add" | "edit" | "delete";

/** Patch classification. */
export type PatchCategory = "Patch" | "Hotfix" | "Content";

/** A single entity change within a patch. */
export interface ChangeEntry {
  /** Entity filename (e.g. "knight.json"). */
  target_id: string;
  /** Human-readable entity name. */
  name: string;
  /** Which field/aspect was changed. */
  field: string;
  /** Type of change. */
  change_type?: ChangeType;
  /** Entity category (e.g. "units", "heroes"). */
  category?: string;
  /** Field-level diffs (deep-diff format). */
  diffs?: unknown[];
}

/** A single patch entry with all its changes. */
export interface PatchEntry {
  /** Unique patch identifier. */
  id: string;
  /** Semantic version (e.g. "1.2.0"). */
  version: string;
  /** Patch classification. */
  type: PatchCategory;
  /** Human-readable title. */
  title: string;
  /** ISO 8601 timestamp. */
  date: string;
  /** Optional tags. */
  tags?: string[];
  /** All entity changes in this patch. */
  changes: ChangeEntry[];
}

/** A single changelog page — array of patches. */
export type ChangelogPage = PatchEntry[];

/** The latest patch entry, or null if none exist. */
export type ChangelogLatest = PatchEntry | null;

/** Pagination manifest for the changelog. */
export interface ChangelogIndex {
  /** Total number of patches across all pages. */
  total_patches: number;
  /** Maximum patches per page. */
  page_size: number;
  /** Number of page files. */
  total_pages: number;
  /** Ordered list of page filenames. */
  pages: string[];
}

// ---------------------------------------------------------------------------
// Entity Timeline (GET /api/v2/timeline/{entity_id}.json)
// ---------------------------------------------------------------------------

/** A snapshot of an entity's stats at a specific patch version. */
export interface TimelineEntry {
  /** Semantic version. */
  version: string;
  /** ISO 8601 timestamp. */
  date: string;
  /** Full entity state at this version. */
  snapshot: Record<string, unknown>;
}

/** Per-entity timeline — array of snapshots, oldest first. */
export type EntityTimeline = TimelineEntry[];
