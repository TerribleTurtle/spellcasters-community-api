/**
 * Patch History Type Definitions
 *
 * TypeScript types for the Spellcasters Community API patch history system.
 * These mirror the JSON schemas in schemas/v2/ and are provided for
 * consumer convenience.
 *
 * @module patch-history
 * @see {@link https://terribleturtle.github.io/spellcasters-community-api/api/v2/balance_index.json}
 * @see {@link https://terribleturtle.github.io/spellcasters-community-api/api/v2/changelog.json}
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

/**
 * Balance change classification.
 *
 * - `buff`    — Stats or behaviour improved.
 * - `nerf`    — Stats or behaviour reduced.
 * - `rework`  — Significant mechanical redesign.
 * - `fix`     — Bug fix that altered effective stats.
 * - `new`     — Entity added in this patch.
 */
export type PatchType = "buff" | "nerf" | "rework" | "fix" | "new";

// ---------------------------------------------------------------------------
// balance_index.json
// ---------------------------------------------------------------------------

/**
 * Lookup table for the most recent patch.
 * Maps entity IDs to their balance change type.
 *
 * **Consumer:** Deckbuilder (buff/nerf icons on cards).
 *
 * @example
 * ```ts
 * const res = await fetch(`${BASE}/api/v2/balance_index.json`);
 * const index: BalanceIndex = await res.json();
 * const changeType = index.entities["fire_imp_1"]; // "buff"
 * ```
 */
export interface BalanceIndex {
  /** Semantic version of the patch (e.g. "1.2.0"). */
  patch_version: string;
  /** ISO 8601 date, or empty string if no patch published yet. */
  patch_date: string;
  /** Map of entity_id → PatchType. */
  entities: Record<string, PatchType>;
}

// ---------------------------------------------------------------------------
// changelog.json / changelog_latest.json
// ---------------------------------------------------------------------------

/**
 * A single published patch entry.
 *
 * **Consumer:**
 * - `changelog.json` — Full card page (patch-over-patch comparison).
 * - `changelog_latest.json` — Card popup (quick "what changed" summary).
 */
export interface PatchEntry {
  /** Semantic version (e.g. "1.2.0"). */
  version: string;
  /** ISO 8601 timestamp of when the patch was published. */
  date: string;
  /** Human-readable summary of the patch. */
  description: string;
  /** Map of entity_id → PatchType for entities affected by this patch. */
  entities: Record<string, PatchType>;
}

/**
 * The full changelog is an array of PatchEntry, newest first.
 *
 * @example
 * ```ts
 * const res = await fetch(`${BASE}/api/v2/changelog.json`);
 * const patches: Changelog = await res.json();
 * ```
 */
export type Changelog = PatchEntry[];

/**
 * The latest changelog entry, or null if no patches exist.
 *
 * @example
 * ```ts
 * const res = await fetch(`${BASE}/api/v2/changelog_latest.json`);
 * const latest: ChangelogLatest = await res.json();
 * if (latest) { console.log(latest.version); }
 * ```
 */
export type ChangelogLatest = PatchEntry | null;

// ---------------------------------------------------------------------------
// timeline/{entity_id}.json
// ---------------------------------------------------------------------------

/**
 * A single snapshot of an entity's state at a given patch version.
 *
 * The `snapshot` field contains the full entity object as it existed at
 * that version. The shape varies by entity type (hero, unit, spell, etc.).
 */
export interface TimelineEntry {
  /** Semantic version of the patch this snapshot was taken from. */
  version: string;
  /** ISO 8601 timestamp of when the patch was published. */
  date: string;
  /** Full entity state at this version. */
  snapshot: Record<string, unknown>;
}

/**
 * Per-entity timeline file. Array of snapshots, oldest first.
 *
 * **Consumer:** Full card page (stat comparison across patches).
 *
 * @example
 * ```ts
 * const res = await fetch(`${BASE}/api/v2/timeline/fire_imp_1.json`);
 * const history: EntityTimeline = await res.json();
 * ```
 */
export type EntityTimeline = TimelineEntry[];
