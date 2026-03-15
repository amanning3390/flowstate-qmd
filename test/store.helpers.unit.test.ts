/**
 * Store helper-level unit tests (pure logic, no model/runtime dependency).
 *
 * NOTE: Path utilities, handelize, virtual path, and docid tests live in
 * store.test.ts (the canonical location). This file only contains tests
 * that require mock DB objects and don't fit the integration test pattern.
 */

import { describe, test, expect } from "vitest";
import { cleanupOrphanedVectors } from "../src/store";

// =============================================================================
// cleanupOrphanedVectors — mock-based edge case
// =============================================================================

describe("cleanupOrphanedVectors", () => {
  test("returns 0 when vec table exists in schema but sqlite-vec is unavailable", () => {
    const prepare = (sql: string) => {
      if (sql.includes("sqlite_master") && sql.includes("vectors_vec")) {
        return { get: () => ({ name: "vectors_vec" }) };
      }
      if (sql.includes("SELECT 1 FROM vectors_vec LIMIT 0")) {
        return { get: () => { throw new Error("no such module: vec0"); } };
      }
      throw new Error(`Unexpected SQL in test: ${sql}`);
    };

    const db = {
      prepare,
      exec: () => {
        throw new Error("cleanup should not execute vector deletes when sqlite-vec is unavailable");
      },
    } as any;

    expect(cleanupOrphanedVectors(db)).toBe(0);
  });
});
