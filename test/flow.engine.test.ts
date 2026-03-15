import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import {
  readIntuitionCache,
  setFlowEngineRuntimeForTests,
  startFlowEngine,
  updateIntuition,
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
    expect(mocks.writeFileSyncMock).toHaveBeenCalledTimes(1);
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
    expect(mocks.writeFileSyncMock).toHaveBeenCalledTimes(1);
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
});
