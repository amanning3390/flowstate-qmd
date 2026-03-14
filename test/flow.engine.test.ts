import { beforeEach, afterEach, describe, expect, test, vi } from "vitest";

const mocks = vi.hoisted(() => {
  const watchMock = vi.fn();
  const statSyncMock = vi.fn();
  const existsSyncMock = vi.fn();
  const writeFileSyncMock = vi.fn();
  const mkdirSyncMock = vi.fn();
  const openSyncMock = vi.fn();
  const closeSyncMock = vi.fn();
  const readSyncMock = vi.fn();
  const hybridQueryMock = vi.fn();
  const closeStoreMock = vi.fn();
  const createStoreMock = vi.fn(() => ({ close: closeStoreMock }));
  const watcher = { close: vi.fn() };
  return {
    watchMock,
    statSyncMock,
    existsSyncMock,
    writeFileSyncMock,
    mkdirSyncMock,
    openSyncMock,
    closeSyncMock,
    readSyncMock,
    hybridQueryMock,
    closeStoreMock,
    createStoreMock,
    watcher,
    watchCallback: undefined as ((eventType: string) => void) | undefined,
  };
});

vi.mock("fs", () => ({
  watch: (...args: any[]) => {
    mocks.watchMock(...args);
    mocks.watchCallback = args[1];
    return mocks.watcher;
  },
  statSync: mocks.statSyncMock,
  existsSync: mocks.existsSyncMock,
  writeFileSync: mocks.writeFileSyncMock,
  mkdirSync: mocks.mkdirSyncMock,
  openSync: mocks.openSyncMock,
  closeSync: mocks.closeSyncMock,
  readSync: mocks.readSyncMock,
}));

vi.mock("os", () => ({
  homedir: () => "/home/test",
}));

vi.mock("../src/store.js", () => ({
  createStore: mocks.createStoreMock,
  hybridQuery: mocks.hybridQueryMock,
}));

import { startFlowEngine, updateIntuition } from "../src/flow/engine.js";

describe("flow engine", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    mocks.watchCallback = undefined;
    mocks.existsSyncMock.mockReset();
    mocks.statSyncMock.mockReset();
    mocks.readSyncMock.mockReset();
    mocks.openSyncMock.mockReturnValue(7);
    mocks.hybridQueryMock.mockResolvedValue([]);
    mocks.closeStoreMock.mockReset();
    mocks.createStoreMock.mockImplementation(() => ({ close: mocks.closeStoreMock }));
  });

  afterEach(() => {
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
    const [cachePath, payload] = mocks.writeFileSyncMock.mock.calls[0]!;
    expect(cachePath).toBe("/home/test/.cache/qmd/intuition.json");
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

    mocks.readSyncMock.mockImplementation((fd, buffer, offset, length) => {
      const content = "x".repeat(length - 80) + "This is a sufficiently long agent update that should refresh intuition.";
      buffer.write(content, offset, length, "utf-8");
      return length;
    });

    await startFlowEngine("/tmp/session.log");
    expect(mocks.watchMock).toHaveBeenCalledTimes(1);
    expect(typeof mocks.watchCallback).toBe("function");

    mocks.watchCallback?.("change");
    await vi.advanceTimersByTimeAsync(1500);
    await Promise.resolve();

    expect(mocks.openSyncMock).toHaveBeenCalledWith("/tmp/session.log", "r");
    expect(mocks.readSyncMock).toHaveBeenCalled();
    expect(mocks.hybridQueryMock).toHaveBeenCalledTimes(1);
    expect(mocks.writeFileSyncMock).toHaveBeenCalledTimes(1);
  });

  test("startFlowEngine skips intuition refresh when tail content is too short", async () => {
    mocks.existsSyncMock.mockReturnValue(true);
    mocks.statSyncMock
      .mockReturnValueOnce({ size: 25 })
      .mockReturnValueOnce({ size: 60 });

    mocks.readSyncMock.mockImplementation((fd, buffer, offset, length) => {
      buffer.fill(" ");
      buffer.write("tiny update", offset, Math.min(length, 11), "utf-8");
      return length;
    });

    await startFlowEngine("/tmp/session.log");
    mocks.watchCallback?.("change");
    await vi.advanceTimersByTimeAsync(1500);
    await Promise.resolve();

    expect(mocks.hybridQueryMock).not.toHaveBeenCalled();
    expect(mocks.writeFileSyncMock).not.toHaveBeenCalled();
  });
});
