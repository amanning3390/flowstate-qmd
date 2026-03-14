#!/usr/bin/env node
import { Command } from "commander";
import { startFlowEngine } from "../flow/engine.js";
import { resolve } from "path";
import { existsSync } from "fs";

const program = new Command();

program
  .name("qmd")
  .description("FlowState-QMD: Anticipatory Memory for AI Agents")
  .version("1.0.0");

program
  .command("flow")
  .description("Start the FlowEngine to monitor agent sessions contextually")
  .argument("<targetFile>", "Log file or session transcript to monitor")
  .option("--lite", "Run in ultra-lite mode using ~0.8B models for low VRAM consumption")
  .action(async (targetFile: string, options: { lite?: boolean }) => {
    const fullPath = resolve(targetFile);
    if (!existsSync(fullPath)) {
      console.error(`Target file not found: ${fullPath}`);
      process.exit(1);
    }
    
    try {
      const isLite = options.lite || false;
      await startFlowEngine(fullPath, isLite);
    } catch (err) {
      console.error(err);
      process.exit(1);
    }
  });

program.parse(process.argv);
