---
trigger: always_on
---

---

## description: Run Linux commands in Windows via Git Bash

When the user asks for Linux commands (curl, grep, ls, etc.), use this pattern in `run_command`:

```powershell
& "C:\Program Files\Git\bin\bash.exe" -c "YOUR_COMMAND_HERE"
```

### Examples

**List files:**
`& "C:\Program Files\Git\bin\bash.exe" -c "ls -la"`
**Curl API:**
`& "C:\Program Files\Git\bin\bash.exe" -c "curl -s https://api.github.com/..."`
**Grep code:**
`& "C:\Program Files\Git\bin\bash.exe" -c "grep -r 'TODO' src/"`
