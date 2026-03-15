/**
 * Integration tests for the Multi-Agent Idempotency Layer.
 *
 * Uses real temp SQLite databases with sqlite-vec to test cosine-similarity
 * dedup logic end-to-end.
 */

import { describe, test, expect, beforeEach, afterEach } from "vitest";
import { openDatabase, loadSqliteVec } from "../src/db.js";
import type { Database } from "../src/db.js";
import { join } from "node:path";
import { mkdtemp, unlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import {
  checkDuplicateDocument,
  getDedupStats,
  resetDedupStats,
  DEDUP_SIMILARITY_THRESHOLD,
  insertContent,
  insertDocument,
  insertEmbedding,
} from "../src/store.js";

// =============================================================================
// Helpers
// =============================================================================

let testDir: string;
let dbPath: string;
let db: Database;
let vecAvailable = false;

const DIMS = 8; // small dimension for test vectors

function initTestDb(database: Database): void {
  database.exec("PRAGMA journal_mode = WAL");
  database.exec("PRAGMA foreign_keys = ON");

  database.exec(`
    CREATE TABLE IF NOT EXISTS content (
      hash TEXT PRIMARY KEY,
      doc TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
  `);

  database.exec(`
    CREATE TABLE IF NOT EXISTS documents (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      collection TEXT NOT NULL,
      path TEXT NOT NULL,
      title TEXT NOT NULL,
      hash TEXT NOT NULL,
      created_at TEXT NOT NULL,
      modified_at TEXT NOT NULL,
      active INTEGER NOT NULL DEFAULT 1,
      FOREIGN KEY (hash) REFERENCES content(hash) ON DELETE CASCADE,
      UNIQUE(collection, path)
    )
  `);

  database.exec(`CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(hash)`);

  database.exec(`
    CREATE TABLE IF NOT EXISTS content_vectors (
      hash TEXT NOT NULL,
      seq INTEGER NOT NULL DEFAULT 0,
      pos INTEGER NOT NULL DEFAULT 0,
      model TEXT NOT NULL,
      embedded_at TEXT NOT NULL,
      PRIMARY KEY (hash, seq)
    )
  `);

  try {
    loadSqliteVec(database);
    database.exec(
      `CREATE VIRTUAL TABLE IF NOT EXISTS vectors_vec USING vec0(hash_seq TEXT PRIMARY KEY, embedding float[${DIMS}] distance_metric=cosine)`,
    );
    vecAvailable = true;
  } catch {
    vecAvailable = false;
  }
}

/** Normalise a vector to unit length so cosine distance is meaningful. */
function normalise(v: number[]): Float32Array {
  const mag = Math.sqrt(v.reduce((s, x) => s + x * x, 0));
  return new Float32Array(v.map((x) => x / mag));
}

/** Insert a document + embedding helper. */
function seedDoc(
  database: Database,
  hash: string,
  collection: string,
  path: string,
  embedding: Float32Array,
): void {
  insertContent(database, hash, `content for ${hash}`, new Date().toISOString());
  insertDocument(database, collection, path, `Title ${hash}`, hash, new Date().toISOString(), new Date().toISOString());
  insertEmbedding(database, hash, 0, 0, embedding, "test-model", new Date().toISOString());
}

// =============================================================================
// Tests
// =============================================================================

describe("Multi-Agent Idempotency Layer", () => {
  beforeEach(async () => {
    testDir = await mkdtemp(join(tmpdir(), "qmd-idemp-"));
    dbPath = join(testDir, `test-${Date.now()}.sqlite`);
    db = openDatabase(dbPath);
    initTestDb(db);
    resetDedupStats();
  });

  afterEach(async () => {
    db.close();
    try { await unlink(dbPath); } catch { /* ignore */ }
  });

  test("returns not-duplicate when vectors_vec table does not exist", () => {
    // Use a fresh db without vec table
    const plainPath = join(testDir!, "plain.sqlite");
    const plainDb = openDatabase(plainPath);
    plainDb.exec("PRAGMA journal_mode = WAL");
    plainDb.exec(`CREATE TABLE IF NOT EXISTS content (hash TEXT PRIMARY KEY, doc TEXT NOT NULL, created_at TEXT NOT NULL)`);

    const embedding = normalise([1, 0, 0, 0, 0, 0, 0, 0]);
    const result = checkDuplicateDocument(plainDb, embedding, "test-col");

    expect(result.isDuplicate).toBe(false);
    expect(result.existingDocId).toBeUndefined();
    plainDb.close();
  });

  test("returns not-duplicate when no vectors are stored", () => {
    if (!vecAvailable) return; // skip if sqlite-vec unavailable

    const embedding = normalise([1, 0, 0, 0, 0, 0, 0, 0]);
    const result = checkDuplicateDocument(db, embedding, "notes");

    expect(result.isDuplicate).toBe(false);
    expect(result.similarity).toBeUndefined();
  });

  test("detects duplicate when identical embedding is inserted", () => {
    if (!vecAvailable) return;

    const embedding = normalise([1, 0.5, 0.2, 0.1, 0, 0, 0, 0]);
    seedDoc(db, "aabbcc001122", "notes", "doc1.md", embedding);

    const result = checkDuplicateDocument(db, embedding, "notes");

    expect(result.isDuplicate).toBe(true);
    expect(result.existingDocId).toBe("aabbcc");
    expect(result.similarity).toBeGreaterThanOrEqual(0.99);
  });

  test("detects duplicate for very similar (above threshold) embedding", () => {
    if (!vecAvailable) return;

    const original = normalise([1, 0.5, 0.2, 0.1, 0, 0, 0, 0]);
    seedDoc(db, "aabbcc001122", "notes", "doc1.md", original);

    // Slightly perturbed — still very similar
    const similar = normalise([1, 0.5, 0.2, 0.15, 0, 0, 0, 0]);
    const result = checkDuplicateDocument(db, similar, "notes");

    expect(result.isDuplicate).toBe(true);
    expect(result.similarity).toBeGreaterThanOrEqual(DEDUP_SIMILARITY_THRESHOLD);
  });

  test("returns not-duplicate for dissimilar embedding", () => {
    if (!vecAvailable) return;

    const original = normalise([1, 0, 0, 0, 0, 0, 0, 0]);
    seedDoc(db, "aabbcc001122", "notes", "doc1.md", original);

    // Orthogonal vector — cosine similarity ~0
    const different = normalise([0, 0, 0, 0, 0, 0, 0, 1]);
    const result = checkDuplicateDocument(db, different, "notes");

    expect(result.isDuplicate).toBe(false);
  });

  test("does not match documents from a different collection", () => {
    if (!vecAvailable) return;

    const embedding = normalise([1, 0.5, 0.2, 0.1, 0, 0, 0, 0]);
    seedDoc(db, "aabbcc001122", "journals", "doc1.md", embedding);

    // Same embedding, different collection
    const result = checkDuplicateDocument(db, embedding, "notes");

    expect(result.isDuplicate).toBe(false);
  });

  test("respects custom threshold parameter", () => {
    if (!vecAvailable) return;

    const original = normalise([1, 0.5, 0.2, 0.1, 0, 0, 0, 0]);
    seedDoc(db, "aabbcc001122", "notes", "doc1.md", original);

    // Slightly different — similarity around 0.99
    const similar = normalise([1, 0.5, 0.2, 0.15, 0, 0, 0, 0]);

    // With threshold=1.0 (exact match only), should NOT flag as duplicate
    const strict = checkDuplicateDocument(db, similar, "notes", 1.0);
    expect(strict.isDuplicate).toBe(false);

    // With threshold=0.5 (very lenient), should flag
    const lenient = checkDuplicateDocument(db, similar, "notes", 0.5);
    expect(lenient.isDuplicate).toBe(true);
  });

  test("getDedupStats tracks checked and deduped counts", () => {
    if (!vecAvailable) return;

    resetDedupStats();

    const embedding = normalise([1, 0.5, 0.2, 0.1, 0, 0, 0, 0]);
    seedDoc(db, "aabbcc001122", "notes", "doc1.md", embedding);

    // First check: should be a duplicate
    checkDuplicateDocument(db, embedding, "notes");
    // Second check: dissimilar, not a dup
    const different = normalise([0, 0, 0, 0, 0, 0, 0, 1]);
    checkDuplicateDocument(db, different, "notes");

    const stats = getDedupStats();
    expect(stats.checked).toBe(2);
    expect(stats.deduped).toBe(1);
  });

  test("resetDedupStats clears all counters", () => {
    if (!vecAvailable) return;

    const embedding = normalise([1, 0, 0, 0, 0, 0, 0, 0]);
    seedDoc(db, "aabbcc001122", "notes", "doc1.md", embedding);
    checkDuplicateDocument(db, embedding, "notes");

    const before = getDedupStats();
    expect(before.checked).toBeGreaterThan(0);

    resetDedupStats();
    const after = getDedupStats();
    expect(after.checked).toBe(0);
    expect(after.deduped).toBe(0);
    expect(after.inserted).toBe(0);
  });

  test("only matches active documents", () => {
    if (!vecAvailable) return;

    const embedding = normalise([1, 0.5, 0.2, 0.1, 0, 0, 0, 0]);
    seedDoc(db, "aabbcc001122", "notes", "doc1.md", embedding);

    // Deactivate the document
    db.prepare(`UPDATE documents SET active = 0 WHERE hash = ?`).run("aabbcc001122");

    const result = checkDuplicateDocument(db, embedding, "notes");
    expect(result.isDuplicate).toBe(false);
  });
});
