import { describe, expect, test } from "vitest";
import { detectHostProfile, MODEL_PROFILES, parseBootstrapTargets, recommendModelProfile } from "../src/bootstrap.js";

describe("bootstrap helpers", () => {
  test("parseBootstrapTargets expands all and preserves known targets", () => {
    expect(parseBootstrapTargets("all")).toContain("hermes");
    expect(parseBootstrapTargets("gemini,kiro,vscode")).toEqual(["gemini", "kiro", "vscode"]);
  });

  test("recommendModelProfile prefers standard on capable Apple Silicon hosts", () => {
    const profile = recommendModelProfile({
      totalRamGb: 24,
      platform: "darwin",
      arch: "arm64",
    });
    expect(profile).toEqual(MODEL_PROFILES.standard);
  });

  test("recommendModelProfile falls back to lite on constrained hosts", () => {
    const profile = recommendModelProfile({
      totalRamGb: 8,
      platform: "linux",
      arch: "x64",
    });
    expect(profile).toEqual(MODEL_PROFILES.lite);
  });

  test("detectHostProfile reports a recommended profile and cache paths", () => {
    const profile = detectHostProfile();
    expect(profile.recommendedProfile).toBeTruthy();
    expect(profile.cacheDir).toContain("qmd");
    expect(profile.modelCacheDir).toContain("qmd");
  });
});
