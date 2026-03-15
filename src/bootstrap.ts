import { spawnSync, spawn as nodeSpawn } from "child_process";
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, unlinkSync, writeFileSync } from "fs";
import os, { homedir } from "os";
import { dirname, join, resolve } from "path";
import YAML from "yaml";
import { fileURLToPath } from "url";
import { DEFAULT_EMBED_MODEL_URI, DEFAULT_GENERATE_MODEL_URI, DEFAULT_MODEL_CACHE_DIR, DEFAULT_RERANK_MODEL_URI } from "./llm.js";

export type BootstrapTarget =
  | "hermes"
  | "openclaw"
  | "pi"
  | "claude-code"
  | "codex"
  | "gemini"
  | "kiro"
  | "vscode";

export type BootstrapTransport = "stdio" | "http";
export type ModelProfileName = "lite" | "standard" | "custom";
export type CheckStatus = "pass" | "warn" | "fail";
export type Readiness = "ready" | "ready_with_degraded_features" | "not_ready";

export type ModelProfile = {
  name: ModelProfileName;
  embedModel: string;
  rerankModel: string;
  generateModel: string;
  rationale: string;
};

export type HostProfile = {
  platform: NodeJS.Platform;
  arch: string;
  totalRamGb: number;
  isAppleSilicon: boolean;
  hasBun: boolean;
  bunVersion: string | null;
  hasNode: boolean;
  nodeVersion: string | null;
  cacheDir: string;
  modelCacheDir: string;
  modelCachePresent: boolean;
  recommendedProfile: ModelProfile;
};

export type DiagnosticCheck = {
  id: string;
  label: string;
  status: CheckStatus;
  message: string;
};

export type TargetConfigResult = {
  target: BootstrapTarget;
  configPath: string | null;
  artifactPath: string;
  autoWritable: boolean;
  wroteConfig: boolean;
  backupPath: string | null;
  valid: boolean;
  format: "json" | "yaml" | "toml";
};

export type BootstrapReport = {
  timestamp: string;
  readiness: Readiness;
  host: HostProfile;
  selectedProfile: ModelProfile;
  preferredToolOrder: string[];
  checks: DiagnosticCheck[];
  watcherTarget: string | null;
  mcp: {
    transport: BootstrapTransport;
    url: string | null;
    pid: number | null;
  };
  targets: TargetConfigResult[];
};

type RuntimeCommand = {
  command?: string;
  args?: string[];
  url?: string;
};

type TargetDefinition = {
  target: BootstrapTarget;
  format: "json" | "yaml" | "toml";
  configPath: string | null;
  artifactPath: string;
  autoWritable: boolean;
  wrapperLabel: string;
};

type BootstrapOptions = {
  cwd: string;
  cacheDir?: string;
  homeDir?: string;
  target: string | undefined;
  profile: string | undefined;
  transport: BootstrapTransport;
  port: number;
  checkOnly: boolean;
  yes: boolean;
  repair: boolean;
  json: boolean;
  cliEntrypoint: string;
  ensureSkillInstalled?: () => Promise<void>;
};

const PREFERRED_TOOL_ORDER = ["fetch_anticipatory_context", "query", "get", "multi_get", "status"];
const DEFAULT_HTTP_PORT = 8181;

export const MODEL_PROFILES: Record<ModelProfileName, ModelProfile> = {
  lite: {
    name: "lite",
    embedModel: "hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf",
    rerankModel: "hf:ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF/qwen3-reranker-0.6b-q8_0.gguf",
    generateModel: "hf:ggml-org/Qwen3-0.6B-GGUF/Qwen3-0.6B-Q8_0.gguf",
    rationale: "Lower-memory profile for constrained laptops and always-on FlowState watchers.",
  },
  standard: {
    name: "standard",
    embedModel: DEFAULT_EMBED_MODEL_URI,
    rerankModel: DEFAULT_RERANK_MODEL_URI,
    generateModel: DEFAULT_GENERATE_MODEL_URI,
    rationale: "Best retrieval quality for coding-agent memory on capable local machines.",
  },
  custom: {
    name: "custom",
    embedModel: process.env.QMD_EMBED_MODEL ?? DEFAULT_EMBED_MODEL_URI,
    rerankModel: process.env.QMD_RERANK_MODEL ?? DEFAULT_RERANK_MODEL_URI,
    generateModel: process.env.QMD_GENERATE_MODEL ?? DEFAULT_GENERATE_MODEL_URI,
    rationale: "Uses explicit environment overrides for advanced local model control.",
  },
};

export function parseBootstrapTargets(rawTarget: string | undefined): BootstrapTarget[] {
  const allTargets: BootstrapTarget[] = [
    "hermes",
    "openclaw",
    "pi",
    "claude-code",
    "codex",
    "gemini",
    "kiro",
    "vscode",
  ];

  if (!rawTarget || rawTarget === "all") {
    return allTargets;
  }

  const seen = new Set<BootstrapTarget>();
  for (const part of rawTarget.split(",").map((value) => value.trim()).filter(Boolean)) {
    if (!allTargets.includes(part as BootstrapTarget)) {
      throw new Error(`Unknown bootstrap target: ${part}`);
    }
    seen.add(part as BootstrapTarget);
  }
  return [...seen];
}

export function getCacheDir(cacheRoot?: string): string {
  return cacheRoot
    ? resolve(cacheRoot, "qmd")
    : resolve(process.env.XDG_CACHE_HOME || resolve(homedir(), ".cache"), "qmd");
}

function commandVersion(command: string): string | null {
  const result = spawnSync(command, ["--version"], { encoding: "utf-8" });
  if (result.status === 0) {
    return (result.stdout || result.stderr || "").trim() || null;
  }
  return null;
}

function bunVersion(): string | null {
  const candidates = [
    "bun",
    resolve(homedir(), ".local", "bun", "bin", "bun"),
    resolve(homedir(), ".bun", "bin", "bun"),
  ];

  for (const candidate of candidates) {
    const version = commandVersion(candidate);
    if (version) {
      return version;
    }
  }

  return null;
}

export function recommendModelProfile(input: {
  totalRamGb: number;
  platform: NodeJS.Platform;
  arch: string;
  custom?: boolean;
}): ModelProfile {
  if (input.custom) {
    return MODEL_PROFILES.custom;
  }
  const isAppleSilicon = input.platform === "darwin" && input.arch === "arm64";
  if (isAppleSilicon && input.totalRamGb >= 16) {
    return MODEL_PROFILES.standard;
  }
  if (input.totalRamGb >= 24) {
    return MODEL_PROFILES.standard;
  }
  return MODEL_PROFILES.lite;
}

export function detectHostProfile(options: { cacheDir?: string } = {}): HostProfile {
  const cacheDir = options.cacheDir ?? getCacheDir();
  const totalRamGb = Math.round((os.totalmem() / (1024 ** 3)) * 10) / 10;
  const platform = os.platform();
  const arch = os.arch();
  const detectedBunVersion = bunVersion();
  const recommendedProfile = recommendModelProfile({
    totalRamGb,
    platform,
    arch,
    custom: Boolean(process.env.QMD_EMBED_MODEL || process.env.QMD_RERANK_MODEL || process.env.QMD_GENERATE_MODEL),
  });

  return {
    platform,
    arch,
    totalRamGb,
    isAppleSilicon: platform === "darwin" && arch === "arm64",
    hasBun: detectedBunVersion !== null,
    bunVersion: detectedBunVersion,
    hasNode: true,
    nodeVersion: process.versions.node,
    cacheDir,
    modelCacheDir: DEFAULT_MODEL_CACHE_DIR,
    modelCachePresent: existsSync(DEFAULT_MODEL_CACHE_DIR),
    recommendedProfile,
  };
}

function ensureParentDir(path: string): void {
  mkdirSync(dirname(path), { recursive: true });
}

function backupPathFor(path: string): string {
  return `${path}.bak`;
}

function writeWithBackup(path: string, content: string): string | null {
  ensureParentDir(path);
  let backupPath: string | null = null;
  if (existsSync(path)) {
    backupPath = backupPathFor(path);
    writeFileSync(backupPath, readFileSync(path, "utf-8"), "utf-8");
  }
  writeFileSync(path, content, "utf-8");
  return backupPath;
}

function renderJsonServer(runtime: RuntimeCommand): Record<string, unknown> {
  if (runtime.url) {
    return { url: runtime.url };
  }
  return { command: runtime.command, args: runtime.args ?? [] };
}

function renderCodexToml(runtime: RuntimeCommand): string {
  if (runtime.url) {
    return `[mcp_servers.qmd]\nurl = "${runtime.url}"\n`;
  }
  const args = (runtime.args ?? []).map((value) => `"${value}"`).join(", ");
  return `[mcp_servers.qmd]\ncommand = "${runtime.command}"\nargs = [${args}]\n`;
}

function upsertJsonConfig(existing: string | null, key: "mcpServers" | "servers", runtime: RuntimeCommand): string {
  const parsed = existing ? JSON.parse(existing) as Record<string, any> : {};
  const current = parsed[key] && typeof parsed[key] === "object" ? parsed[key] : {};
  current.qmd = renderJsonServer(runtime);
  parsed[key] = current;
  return `${JSON.stringify(parsed, null, 2)}\n`;
}

function upsertYamlConfig(existing: string | null, runtime: RuntimeCommand): string {
  const parsed = existing ? YAML.parse(existing) as Record<string, any> : {};
  const current = parsed.mcp_servers && typeof parsed.mcp_servers === "object" ? parsed.mcp_servers : {};
  current.qmd = runtime.url
    ? { url: runtime.url }
    : { command: runtime.command, args: runtime.args ?? [] };
  parsed.mcp_servers = current;
  parsed.flowstate_qmd = {
    primary_memory: true,
    preferred_tool_order: PREFERRED_TOOL_ORDER,
  };
  return YAML.stringify(parsed);
}

function upsertTomlConfig(existing: string | null, runtime: RuntimeCommand): string {
  const rendered = renderCodexToml(runtime);
  if (!existing || existing.trim().length === 0) {
    return rendered;
  }

  const sectionPattern = /\[mcp_servers\.qmd\][\s\S]*?(?=\n\[|$)/m;
  if (sectionPattern.test(existing)) {
    return existing.replace(sectionPattern, rendered.trimEnd());
  }
  const separator = existing.endsWith("\n") ? "" : "\n";
  return `${existing}${separator}${rendered}`;
}

function validateWrittenConfig(definition: TargetDefinition, content: string): boolean {
  try {
    if (definition.format === "json") {
      const parsed = JSON.parse(content) as Record<string, any>;
      const key = definition.target === "vscode" ? "servers" : "mcpServers";
      return Boolean(parsed[key]?.qmd);
    }
    if (definition.format === "yaml") {
      const parsed = YAML.parse(content) as Record<string, any>;
      return Boolean(parsed.mcp_servers?.qmd);
    }
    return /\[mcp_servers\.qmd\]/.test(content);
  } catch {
    return false;
  }
}

function getRuntimeCommand(transport: BootstrapTransport, port: number): RuntimeCommand {
  if (transport === "http") {
    return { url: `http://localhost:${port}/mcp` };
  }
  return { command: "qmd", args: ["mcp"] };
}

function buildTargetDefinitions(options: {
  cwd: string;
  homeDir: string;
  cacheDir: string;
  targets: BootstrapTarget[];
}): TargetDefinition[] {
  const targetDir = resolve(options.cacheDir, "targets");
  const definitions: Record<BootstrapTarget, TargetDefinition> = {
    hermes: {
      target: "hermes",
      format: "yaml",
      configPath: resolve(options.homeDir, ".hermes", "config.yaml"),
      artifactPath: resolve(targetDir, "hermes.config.yaml"),
      autoWritable: true,
      wrapperLabel: "Hermes Agent",
    },
    "claude-code": {
      target: "claude-code",
      format: "json",
      configPath: resolve(options.homeDir, ".claude.json"),
      artifactPath: resolve(targetDir, "claude-code.settings.json"),
      autoWritable: true,
      wrapperLabel: "Claude Code",
    },
    codex: {
      target: "codex",
      format: "toml",
      configPath: resolve(options.homeDir, ".codex", "config.toml"),
      artifactPath: resolve(targetDir, "codex.config.toml"),
      autoWritable: true,
      wrapperLabel: "Codex",
    },
    gemini: {
      target: "gemini",
      format: "json",
      configPath: resolve(options.homeDir, ".gemini", "settings.json"),
      artifactPath: resolve(targetDir, "gemini.settings.json"),
      autoWritable: true,
      wrapperLabel: "Gemini CLI",
    },
    kiro: {
      target: "kiro",
      format: "json",
      configPath: resolve(options.cwd, ".kiro", "settings", "mcp.json"),
      artifactPath: resolve(targetDir, "kiro.mcp.json"),
      autoWritable: true,
      wrapperLabel: "Kiro",
    },
    vscode: {
      target: "vscode",
      format: "json",
      configPath: resolve(options.cwd, ".vscode", "mcp.json"),
      artifactPath: resolve(targetDir, "vscode.mcp.json"),
      autoWritable: true,
      wrapperLabel: "VS Code",
    },
    openclaw: {
      target: "openclaw",
      format: "json",
      configPath: null,
      artifactPath: resolve(targetDir, "openclaw.mcp.json"),
      autoWritable: false,
      wrapperLabel: "OpenClaw",
    },
    pi: {
      target: "pi",
      format: "json",
      configPath: null,
      artifactPath: resolve(targetDir, "pi.mcp.json"),
      autoWritable: false,
      wrapperLabel: "pi",
    },
  };

  return options.targets.map((target) => definitions[target]);
}

function renderTargetConfig(definition: TargetDefinition, runtime: RuntimeCommand): string {
  const existing = definition.configPath && existsSync(definition.configPath)
    ? readFileSync(definition.configPath, "utf-8")
    : null;

  if (definition.format === "yaml") {
    return upsertYamlConfig(existing, runtime);
  }
  if (definition.format === "toml") {
    return upsertTomlConfig(existing, runtime);
  }
  const key = definition.target === "vscode" ? "servers" : "mcpServers";
  return upsertJsonConfig(existing, key, runtime);
}

function emitTargetConfigs(definitions: TargetDefinition[], runtime: RuntimeCommand, writeTargets: boolean): TargetConfigResult[] {
  const results: TargetConfigResult[] = [];

  for (const definition of definitions) {
    const content = renderTargetConfig(definition, runtime);
    ensureParentDir(definition.artifactPath);
    writeFileSync(definition.artifactPath, content, "utf-8");

    let wroteConfig = false;
    let backupPath: string | null = null;
    let validationSource = content;

    if (writeTargets && definition.autoWritable && definition.configPath) {
      backupPath = writeWithBackup(definition.configPath, content);
      wroteConfig = true;
      validationSource = readFileSync(definition.configPath, "utf-8");
    }

    results.push({
      target: definition.target,
      configPath: definition.configPath,
      artifactPath: definition.artifactPath,
      autoWritable: definition.autoWritable,
      wroteConfig,
      backupPath,
      valid: validateWrittenConfig(definition, validationSource),
      format: definition.format,
    });
  }

  return results;
}

function detectWatcherTarget(homeDir: string, cwd: string): string | null {
  const candidates = [
    process.env.QMD_FLOW_WATCH,
    resolve(homeDir, ".hermes", "sessions", "current.log"),
    resolve(homeDir, ".codex", "sessions", "current.log"),
    resolve(cwd, ".flowstate", "current.log"),
  ].filter((value): value is string => Boolean(value));

  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      return candidate;
    }
  }
  return null;
}

function createDiagnosticChecks(host: HostProfile, targetResults: TargetConfigResult[]): DiagnosticCheck[] {
  const checks: DiagnosticCheck[] = [];
  const nodeMajor = parseInt((host.nodeVersion ?? "0").split(".")[0] || "0", 10);

  checks.push({
    id: "node",
    label: "Node.js runtime",
    status: nodeMajor >= 22 ? "pass" : "fail",
    message: nodeMajor >= 22
      ? `Node ${host.nodeVersion} satisfies the >=22 requirement.`
      : `Node ${host.nodeVersion} is too old. Install Node 22 or newer.`,
  });

  checks.push({
    id: "bun",
    label: "Bun runtime",
    status: host.hasBun ? "pass" : "warn",
    message: host.hasBun
      ? `Bun ${host.bunVersion} is available for the Bun-first developer workflow.`
      : "Bun is not installed. Install it from https://bun.sh to match the Bun-first project workflow.",
  });

  checks.push({
    id: "model-cache",
    label: "Model cache",
    status: host.modelCachePresent ? "pass" : "warn",
    message: host.modelCachePresent
      ? `Model cache detected at ${host.modelCacheDir}.`
      : `No model cache found at ${host.modelCacheDir}. Run 'qmd pull' before a live demo.`,
  });

  const invalidTargets = targetResults.filter((target) => !target.valid);
  checks.push({
    id: "targets",
    label: "Wrapper configs",
    status: invalidTargets.length === 0 ? "pass" : "fail",
    message: invalidTargets.length === 0
      ? `Generated ${targetResults.length} target configs with the canonical qmd MCP contract.`
      : `Failed to validate config emission for: ${invalidTargets.map((item) => item.target).join(", ")}.`,
  });

  return checks;
}

function readinessFromChecks(checks: DiagnosticCheck[]): Readiness {
  if (checks.some((check) => check.status === "fail")) {
    return "not_ready";
  }
  if (checks.some((check) => check.status === "warn")) {
    return "ready_with_degraded_features";
  }
  return "ready";
}

function formatReportText(report: BootstrapReport): string {
  const lines: string[] = [];
  lines.push(`FlowState-QMD ${report.readiness.replace(/_/g, " ")}`);
  lines.push("");
  lines.push(`Host: ${report.host.platform}/${report.host.arch} with ${report.host.totalRamGb.toFixed(1)} GB RAM`);
  lines.push(`Profile: ${report.selectedProfile.name} — ${report.selectedProfile.rationale}`);
  lines.push(`Tool order: ${report.preferredToolOrder.join(" -> ")}`);
  if (report.watcherTarget) {
    lines.push(`Watcher target: ${report.watcherTarget}`);
  } else {
    lines.push("Watcher target: not detected");
  }
  if (report.mcp.url) {
    lines.push(`MCP daemon: ${report.mcp.url}`);
  }
  lines.push("");
  lines.push("Checks:");
  for (const check of report.checks) {
    const prefix = check.status === "pass" ? "PASS" : check.status === "warn" ? "WARN" : "FAIL";
    lines.push(`- [${prefix}] ${check.label}: ${check.message}`);
  }
  lines.push("");
  lines.push("Targets:");
  for (const target of report.targets) {
    const destination = target.wroteConfig ? target.configPath : target.artifactPath;
    const mode = target.wroteConfig ? "installed" : "artifact";
    lines.push(`- ${target.target}: ${mode} -> ${destination}`);
  }
  return `${lines.join("\n")}\n`;
}

function writeBootstrapArtifacts(report: BootstrapReport, cacheDir: string): void {
  mkdirSync(cacheDir, { recursive: true });
  writeFileSync(resolve(cacheDir, "bootstrap-report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf-8");
  writeFileSync(
    resolve(cacheDir, "agent-config.json"),
    `${JSON.stringify({
      qmd: {
        primaryMemory: true,
        preferredToolOrder: report.preferredToolOrder,
        transport: report.mcp.transport,
        url: report.mcp.url,
      },
    }, null, 2)}\n`,
    "utf-8",
  );

  const scriptPath = resolve(cacheDir, "start-flowstate.sh");
  writeFileSync(
    scriptPath,
    `#!/bin/bash
set -euo pipefail
qmd mcp --http --daemon --port ${report.mcp.url ? report.mcp.url.split(":")[2]?.split("/")[0] ?? DEFAULT_HTTP_PORT : DEFAULT_HTTP_PORT}
echo "FlowState-QMD ready. Prefer fetch_anticipatory_context, then query, then get/multi_get."
`,
    "utf-8",
  );
}

function ensureHttpDaemon(cliEntrypoint: string, cacheDir: string, port: number): { url: string; pid: number } {
  const pidPath = resolve(cacheDir, "mcp.pid");
  if (existsSync(pidPath)) {
    const existingPid = parseInt(readFileSync(pidPath, "utf-8").trim(), 10);
    try {
      process.kill(existingPid, 0);
      return { url: `http://localhost:${port}/mcp`, pid: existingPid };
    } catch {
      unlinkSync(pidPath);
    }
  }

  mkdirSync(cacheDir, { recursive: true });
  const logPath = resolve(cacheDir, "mcp.log");
  const logFd = openSync(logPath, "w");
  const spawnArgs = cliEntrypoint.endsWith(".ts")
    ? ["--import", join(dirname(cliEntrypoint), "..", "..", "node_modules", "tsx", "dist", "esm", "index.mjs"), cliEntrypoint, "mcp", "--http", "--port", String(port)]
    : [cliEntrypoint, "mcp", "--http", "--port", String(port)];
  const child = nodeSpawn(process.execPath, spawnArgs, {
    stdio: ["ignore", logFd, logFd],
    detached: true,
  });
  child.unref();
  closeSync(logFd);

  writeFileSync(pidPath, String(child.pid), "utf-8");
  return { url: `http://localhost:${port}/mcp`, pid: child.pid ?? 0 };
}

export async function runBootstrap(options: BootstrapOptions): Promise<BootstrapReport> {
  const homeDir = options.homeDir ?? homedir();
  const cacheDir = options.cacheDir ?? getCacheDir();
  const targets = parseBootstrapTargets(options.target);
  const host = detectHostProfile({ cacheDir });
  const selectedProfile = options.profile === "lite"
    ? MODEL_PROFILES.lite
    : options.profile === "custom"
      ? MODEL_PROFILES.custom
      : host.recommendedProfile;
  const targetDefinitions = buildTargetDefinitions({
    cwd: options.cwd,
    homeDir,
    cacheDir,
    targets,
  });

  if (!options.checkOnly && options.ensureSkillInstalled) {
    await options.ensureSkillInstalled();
  }

  const runtime = getRuntimeCommand(options.transport, options.port || DEFAULT_HTTP_PORT);
  const targetResults = emitTargetConfigs(targetDefinitions, runtime, !options.checkOnly);
  const watcherTarget = detectWatcherTarget(homeDir, options.cwd);

  let daemonUrl: string | null = null;
  let daemonPid: number | null = null;
  if (!options.checkOnly && options.transport === "http") {
    const daemon = ensureHttpDaemon(options.cliEntrypoint, cacheDir, options.port || DEFAULT_HTTP_PORT);
    daemonUrl = daemon.url;
    daemonPid = daemon.pid;
  } else if (options.transport === "http") {
    daemonUrl = `http://localhost:${options.port || DEFAULT_HTTP_PORT}/mcp`;
  }

  const checks = createDiagnosticChecks(host, targetResults);
  const report: BootstrapReport = {
    timestamp: new Date().toISOString(),
    readiness: readinessFromChecks(checks),
    host,
    selectedProfile,
    preferredToolOrder: PREFERRED_TOOL_ORDER,
    checks,
    watcherTarget,
    mcp: {
      transport: options.transport,
      url: daemonUrl,
      pid: daemonPid,
    },
    targets: targetResults,
  };

  writeBootstrapArtifacts(report, cacheDir);
  return report;
}

export function printBootstrapReport(report: BootstrapReport, asJson: boolean): void {
  if (asJson) {
    process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
    return;
  }
  process.stdout.write(formatReportText(report));
}
