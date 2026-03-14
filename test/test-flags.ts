export const RUN_LLM_INTEGRATION = process.env.QMD_RUN_LLM_TESTS === "1";

export function describeIfLlmIntegration() {
  return RUN_LLM_INTEGRATION ? "run" : "skip";
}
