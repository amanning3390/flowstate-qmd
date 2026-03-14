#!/usr/bin/env python3
import re

# Read the new base64 string
with open('new_skill_base64.txt', 'r') as f:
    new_base64 = f.read().strip()

# Read the embedded skills file
with open('src/embedded-skills.ts', 'r') as f:
    content = f.read()

# Find the SKILL.md entry and replace the base64 string
# Pattern: "SKILL.md": "base64string",
pattern = r'(\"SKILL\.md\": \")([^\"]+)(\",)'
match = re.search(pattern, content)

if match:
    old_base64 = match.group(2)
    print(f"Old base64 length: {len(old_base64)}")
    print(f"New base64 length: {len(new_base64)}")
    
    # Replace the old base64 with the new one
    new_content = content[:match.start(2)] + new_base64 + content[match.end(2):]
    
    # Write back
    with open('src/embedded-skills.ts', 'w') as f:
        f.write(new_content)
    
    print("Updated embedded skill successfully!")
else:
    print("Could not find SKILL.md entry in embedded-skills.ts")
    # Print the first few lines to debug
    print("First 500 chars of file:", content[:500])