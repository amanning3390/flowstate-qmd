import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import {
  readIntuitionCache,
  setFlowEngineRuntimeForTests,
  startFlowEngine,
  updateIntuition,
  getFlowTelemetry,
  resetFlowTelemetry,
  loadTelemetry,
} from "../src/flow/engine.js";

const mocks = {
  watchMock: vi.fn(),
  statSyncMock: vi.fn(),
  existsSyncMock: vi.fn(),
  writeFileSyncMock: vi.fn(),
  readFileSyncMock: vi.fn(),
  renameSyncMock: vi.fn(),
  mkdirSyncMock: vi.fn(),
  openSyncMock: vi.fn(),
  closeSyncMock: vi.fn(),
  readSyncMock: vi.fn(),
  hybridQueryMock: vi.fn(),
  closeStoreMock: vi.fn(),
  createStoreMock: vi.fn(),
  watcher: { close: vi.fn() },
  watchCallback: undefined as ((eventType: string) => void) | undefined,
};

describe("flow engine", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    mocks.watchCallback = undefined;
    mocks.openSyncMock.mockReturnValue(7);
    mocks.hybridQueryMock.mockResolvedValue([]);
    mocks.createStoreMock.mockImplementation(() => ({ close: mocks.closeStoreMock }));
    mocks.watchMock.mockImplementation((_targetFile, callback) => {
      mocks.watchCallback = callback;
      return mocks.watcher;
    });

    setFlowEngineRuntimeForTests({
      watch: mocks.watchMock as any,
      statSync: mocks.statSyncMock as any,
      existsSync: mocks.existsSyncMock as any,
      writeFileSync: mocks.writeFileSyncMock as any,
      readFileSync: mocks.readFileSyncMock as any,
      renameSync: mocks.renameSyncMock as any,
      mkdirSync: mocks.mkdirSyncMock as any,
      openSync: mocks.openSyncMock as any,
      closeSync: mocks.closeSyncMock as any,
      readSync: mocks.readSyncMock as any,
      homedir: () => "/home/test",
      createStore: mocks.createStoreMock as any,
      hybridQuery: mocks.hybridQueryMock as any,
    });
  });

  afterEach(() => {
    setFlowEngineRuntimeForTests(null);
    vi.useRealTimers();
  });

  test("updateIntuition writes intuition cache and closes the store", async () => {
    mocks.existsSyncMock.mockReturnValue(false);
    mocks.hybridQueryMock.mockResolvedValue([
      { filepath: "qmd://docs/a.md", score: 0.9, title: "A" },
    ]);

    await updateIntuition("hello world context");

    expect(mocks.mkdirSyncMock).toHaveBeenCalledWith("/home/test/.cache/qmd", { recursive: true });
    // writeFileSync is called twice: once for intuition cache .tmp, once for telemetry.json
    expect(mocks.writeFileSyncMock).toHaveBeenCalledTimes(2);
    expect(mocks.renameSyncMock).toHaveBeenCalledWith(
      "/home/test/.cache/qmd/intuition.json.tmp",
      "/home/test/.cache/qmd/intuition.json"
    );
    const [cachePath, payload] = mocks.writeFileSyncMock.mock.calls[0]!;
    expect(cachePath).toBe("/home/test/.cache/qmd/intuition.json.tmp");
    expect(String(payload)).toContain("hello world context");
    expect(String(payload)).toContain("qmd://docs/a.md");
    expect(mocks.closeStoreMock).toHaveBeenCalledTimes(1);
  });

  test("startFlowEngine throws when target file is missing", async () => {
    mocks.existsSyncMock.mockReturnValue(false);

    await expect(startFlowEngine("/tmp/missing.log")).rejects.toThrow(
      "[FLOW] Target file not found: /tmp/missing.log"
    );
  });

  test("startFlowEngine debounces file growth and refreshes intuition from file tail", async () => {
    mocks.existsSyncMock.mockReturnValue(true);
    mocks.statSyncMock
      .mockReturnValueOnce({ size: 100 })
      .mockReturnValueOnce({ size: 260 });

    mocks.readSyncMock.mockImplementation((_fd, buffer, offset, length) => {
      const content = "x".repeat(length - 80) + "This is a sufficiently long agent update that should refresh intuition.";
      buffer.write(content, offset, length, "utf-8");
      return length;
    });

    await startFlowEngine("/tmp/session.log");
    expect(mocks.watchMock).toHaveBeenCalledTimes(1);
    expect(typeof mocks.watchCallback).toBe("function");

    mocks.watchCallback?.("change");
    vi.advanceTimersByTime(1500);
    await Promise.resolve();

    expect(mocks.openSyncMock).toHaveBeenCalledWith("/tmp/session.log", "r");
    expect(mocks.readSyncMock).toHaveBeenCalled();
    expect(mocks.hybridQueryMock).toHaveBeenCalledTimes(1);
    // writeFileSync is called twice: once for intuition cache .tmp, once for telemetry.json
    expect(mocks.writeFileSyncMock).toHaveBeenCalledTimes(2);
    expect(mocks.renameSyncMock).toHaveBeenCalledTimes(1);
  });

  test("startFlowEngine skips intuition refresh when tail content is too short", async () => {
    mocks.existsSyncMock.mockReturnValue(true);
    mocks.statSyncMock
      .mockReturnValueOnce({ size: 25 })
      .mockReturnValueOnce({ size: 60 });

    mocks.readSyncMock.mockImplementation((_fd, buffer, offset, length) => {
      buffer.fill(" ");
      buffer.write("tiny update", offset, Math.min(length, 11), "utf-8");
      return length;
    });

    await startFlowEngine("/tmp/session.log");
    mocks.watchCallback?.("change");
    vi.advanceTimersByTime(1500);
    await Promise.resolve();

    expect(mocks.hybridQueryMock).not.toHaveBeenCalled();
    expect(mocks.writeFileSyncMock).not.toHaveBeenCalled();
  });

  test("readIntuitionCache returns parsed cache entries when present", () => {
    const cached = {
      timestamp: 1741972800000,
      query: "auth rollback",
      memories: [
        { file: "qmd://docs/adr/auth-rollback.md", score: 0.91, title: "Auth rollback ADR" },
      ],
    };
    mocks.existsSyncMock.mockReturnValue(true);
    mocks.readFileSyncMock.mockReturnValue(JSON.stringify(cached));

    expect(readIntuitionCache()).toEqual(cached);
    expect(mocks.readFileSyncMock).toHaveBeenCalledWith("/home/test/.cache/qmd/intuition.json", "utf-8");
  });

  test("readIntuitionCache returns null when cache is invalid", () => {
    mocks.existsSyncMock.mockReturnValue(true);
    mocks.readFileSyncMock.mockReturnValue("{not json");

    expect(readIntuitionCache()).toBeNull();
  });

  // ===========================================================================
  // Telemetry tracking
  // ===========================================================================

  test("readIntuitionCache increments cacheHits on successful read", () => {
    resetFlowTelemetry();
    const cached = {
      timestamp: Date.now(),
      query: "test query",
      memories: [],
    };
    mocks.existsSyncMock.mockReturnValue(true);
    mocks.readFileSyncMock.mockReturnValue(JSON.stringify(cached));

    readIntuitionCache();
    readIntuitionCache();

    const t = getFlowTelemetry();
    expect(t.cacheHits).toBe(2);
    expect(t.cacheMisses).toBe(0);
    expect(t.lastHitAt).toBeTypeOf("number");
  });

  test("readIntuitionCache increments cacheMisses when file is missing", () => {
    resetFlowTelemetry();
    mocks.existsSyncMock.mockReturnValue(false);

    readIntuitionCache();

    const t = getFlowTelemetry();
    expect(t.cacheHits).toBe(0);
    expect(t.cacheMisses).toBe(1);
    expect(t.lastMissAt).toBeTypeOf("number");
  });

  test("readIntuitionCache increments cacheMisses on parse failure", () => {
    resetFlowTelemetry();
    mocks.existsSyncMock.mockReturnValue(true);
    mocks.readFileSyncMock.mockReturnValue("not-json");

    readIntuitionCache();

    const t = getFlowTelemetry();
    expect(t.cacheHits).toBe(0);
    expect(t.cacheMisses).toBe(1);
  });

  test("resetFlowTelemetry zeroes all counters", () => {
    // Accumulate some hits
    mocks.existsSyncMock.mockReturnValue(true);
    mocks.readFileSyncMock.mockReturnValue(JSON.stringify({
      timestamp: Date.now(), query: "q", memories: [],
    }));
    readIntuitionCache();

    resetFlowTelemetry();
    const t = getFlowTelemetry();
    expect(t.cacheHits).toBe(0);
    expect(t.cacheMisses).toBe(0);
    expect(t.lastHitAt).toBeNull();
    expect(t.lastMissAt).toBeNull();
    expect(t.totalRefreshes).toBe(0);
    expect(t.avgRefreshMs).toBe(0);
  });

  test("updateIntuition records refresh duration in telemetry", async () => {
    resetFlowTelemetry();
    mocks.existsSyncMock.mockReturnValue(false);
    mocks.hybridQueryMock.mockResolvedValue([]);

    await updateIntuition("context for refresh test");

    const t = getFlowTelemetry();
    expect(t.totalRefreshes).toBe(1);
    expect(t.avgRefreshMs).toBeGreaterThanOrEqual(0);
  });

  test("updateIntuition persists telemetry to disk", async () => {
    resetFlowTelemetry();
    mocks.existsSyncMock.mockReturnValue(false);
    mocks.hybridQueryMock.mockResolvedValue([]);

    await updateIntuition("persist telemetry test");

    // writeFileSync is called twice: once for intuition cache (.tmp), once for telemetry
    const telemetryCalls = mocks.writeFileSyncMock.mock.calls.filter(
      (call: [string, string]) => String(call[0]).includes("telemetry.json"),
    );
    expect(telemetryCalls.length).toBe(1);

    const written = JSON.parse(String(telemetryCalls[0]![1]));
    expect(written.totalRefreshes).toBe(1);
  });

  test("updateIntuition accumulates avgRefreshMs over multiple calls", async () => {
    resetFlowTelemetry();
    mocks.existsSyncMock.mockReturnValue(false);
    mocks.hybridQueryMock.mockResolvedValue([]);

    await updateIntuition("call 1");
    await updateIntuition("call 2");

    const t = getFlowTelemetry();
    expect(t.totalRefreshes).toBe(2);
    expect(t.avgRefreshMs).toBeGreaterThanOrEqual(0);
  });

  test("loadTelemetry reads persisted telemetry from disk", () => {
    const persisted = {
      cacheHits: 42,
      cacheMisses: 7,
      lastHitAt: 1710000000000,
      lastMissAt: 1710000001000,
      totalRefreshes: 10,
      avgRefreshMs: 55.5,
    };
    mocks.existsSyncMock.mockImplementation((p: string) =>
      String(p).includes("telemetry.json"),
    );
    mocks.readFileSyncMock.mockReturnValue(JSON.stringify(persisted));

    const loaded = loadTelemetry();
    expect(loaded.cacheHits).toBe(42);
    expect(loaded.cacheMisses).toBe(7);
    expect(loaded.totalRefreshes).toBe(10);
    expect(loaded.avgRefreshMs).toBe(55.5);
  });

  test("loadTelemetry returns defaults when file is missing", () => {
    resetFlowTelemetry();
    mocks.existsSyncMock.mockReturnValue(false);

    const loaded = loadTelemetry();
    expect(loaded.cacheHits).toBe(0);
    expect(loaded.cacheMisses).toBe(0);
    expect(loaded.totalRefreshes).toBe(0);
  });

  test("updateIntuition passes liteMode to hybridQuery", async () => {
    mocks.existsSyncMock.mockReturnValue(false);
    mocks.hybridQueryMock.mockResolvedValue([]);

    await updateIntuition("lite mode test", true);

    expect(mocks.hybridQueryMock).toHaveBeenCalledWith(
      expect.anything(),
      "lite mode test",
      expect.objectContaining({ liteMode: true }),
    );
  });
});
