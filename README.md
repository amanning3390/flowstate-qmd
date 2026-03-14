# FLOWSTATE-QMD
### NIRVANA FOR AGENTS • HERMES HACKATHON 2026

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered by Hermes](https://img.shields.io/badge/Powered%20by-Hermes%20Agent-blueviolet)](https://github.com/NousResearch/hermes-agent)
[![Base: QMD](https://img.shields.io/badge/Base-tobi%2Fqmd-blue)](https://github.com/tobi/qmd)

```text
  _______  _        _______           _______ _________ _______ _________ _______ 
 (  ____ \( \      (  ___  )|\     /|(  ____ \__   __/(  ___  )\__   __/(  ____ \
 | (    \/| (      | (   ) || )   ( || (    \/   ) (   | (   ) |   ) (   | (    \/
 | (__    | |      | |   | || | _ | || (_____    | |   | (___) |   | |   | (__    
 |  __)   | |      | |   | || |( )| |(_____  )   | |   |  ___  |   | |   |  __)   
 | (      | |      | |   | || || || |      ) |   | |   | (   ) |   | |   | (      
 | )      | (____/\| (___) || () () |/\____) |   | |   | )   ( |   | |   | (____/\
 |/       (_______/(_______)(_______)\_______)   )_(   |/     \|   )_(   (_______/
                                                                                  
  _______  _______  ______                                                        
 (  ___  )(       )(  __  \                                                       
 | (   ) || () () || (  \  )                                                      
 | |   | || || || || |   ) |                                                      
 | |   | || |(_)| || |   | |                                                      
 | |   | || |   | || |   ) |                                                      
 | (___) || )   ( || (__/  )                                                      
 (_______)|/     \|(______/                                                       
```

## THE VISION
**Why ask when your agent already knows?**

Traditional RAG and memory tools force agents into a "Stutter Loop":
1. Agent receives a prompt.
2. Agent realizes it's missing context.
3. Agent calls a search tool.
4. Agent waits for retrieval.
5. Agent process context.
6. Agent finally answers.

**FLOWSTATE-QMD** kills the stutter. It creates a "Sixth Sense" for agents by pre-fetching relevant memories into an **Intuition Cache** before the agent even begins its turn.

## FEATURES
- **Anticipatory Retrieval:** Background observation of your session pre-loads context.
- **SOTA Local Models:** Swapped default embeddings for `Qwen3-Embedding-4B` and `Qwen3-Reranker-4B`.
- **Zero-Tool "Intuition":** Information appears in the system prompt—no search tool latency.
- **Sub-50ms Latency:** Optimized via `node-llama-cpp` and GGUF for instant across-the-board memory.
- **Multi-Agent Idempotency:** One global, non-redundant memory pool for Hermes, Claude Code, and all sub-agents.

## HOW IT WORKS
1. **The Horizon Monitor:** A background process tails your active session log.
2. **The Latent Vectorizer:** Every few seconds, the last 1000 tokens are vectorized using Qwen3-4B.
3. **The Intuition Injection:** Relevant snippets from the QMD SQLite-Vec store are injected into `~/.cache/qmd/intuition.json`.
4. **The Hermes Skill:** The `flowstate-qmd` skill instructs the agent to check the cache at turn-start.

## INSTALLATION
```bash
# Clone the upgrade
git clone https://github.com/[YOUR-USERNAME]/flowstate-qmd.git
cd flowstate-qmd

# Install dependencies
bun install

# Initialize your intuition
qmd init
qmd pull # Downloads Qwen3-4B models
```

## CREDITS
Huge respect to **@tobi** for the original [QMD project](https://github.com/tobi/qmd), which provided the rock-solid SQLite-Vec foundation we built this on. 

Built with 💜 for the **Hermes Hackathon 2026**.
