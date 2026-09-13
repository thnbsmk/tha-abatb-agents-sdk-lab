# Publish as standalone GitHub repo

If you want `https://github.com/thnbsmk/exec-server` as a separate repository:

```bash
cd codex/exec-server
git init -b main
git add .
git commit -m "Initial codex exec-server bootstrap"
gh repo create thnbsmk/exec-server --public --source=. --remote=origin --push
```

Or create the empty repo in GitHub UI, then:

```bash
git remote add origin https://github.com/thnbsmk/exec-server.git
git push -u origin main
```

Until then, clone from the monorepo path:

```bash
git clone https://github.com/thnbsmk/tha-abatb-agents-sdk-lab.git
cd tha-abatb-agents-sdk-lab/codex/exec-server
```
