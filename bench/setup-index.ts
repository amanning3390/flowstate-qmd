import { createStore, hashContent, extractTitle, syncConfigToDb } from "../src/store.js";
import { readFileSync, readdirSync, statSync } from "fs";
import { join, relative } from "path";

function findMarkdownFiles(dir: string): string[] {
  const results: string[] = [];
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === ".git") continue;
    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      results.push(...findMarkdownFiles(full));
    } else if (entry.endsWith(".md")) {
      results.push(full);
    }
  }
  return results;
}

async function main() {
  const dbPath = process.env.INDEX_PATH!;
  const store = createStore(dbPath);
  const repoRoot = join(import.meta.dirname!, "..");

  // Create a proper CollectionConfig
  const config = {
    collections: {
      repo: {
        path: repoRoot,
        pattern: "**/*.md",
      }
    }
  };
  syncConfigToDb(store.db, config);

  const mdFiles = findMarkdownFiles(repoRoot);
  const now = new Date().toISOString();
  let count = 0;

  for (const file of mdFiles) {
    const relPath = relative(repoRoot, file);
    const content = readFileSync(file, "utf-8");
    const hash = await hashContent(content);
    const title = extractTitle(content, relPath) || relPath;

    try {
      store.insertContent(hash, content, now);
      store.insertDocument("repo", relPath, title, hash, now, now);
      count++;
    } catch (e: any) {
      if (!e.message?.includes("UNIQUE")) {
        console.error(`Skip ${relPath}: ${e.message}`);
      }
    }
  }

  console.log(`Indexed ${count} of ${mdFiles.length} markdown files`);
  const status = store.getStatus();
  console.log(JSON.stringify(status, null, 2));
  store.close();
}

main();
