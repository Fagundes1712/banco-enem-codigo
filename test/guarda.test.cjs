"use strict";
/* Testa o hook .claude/hooks/guarda.cjs num repositório git temporário (não roda as checagens do projeto). */
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync, execSync } = require("node:child_process");

const hook = path.join(__dirname, "../.claude/hooks/guarda.cjs");
const repo = fs.mkdtempSync(path.join(os.tmpdir(), "guarda-"));
execSync("git init -q -b main", { cwd: repo });

let falhas = 0;
// espera: null = passa; regex = bloqueia com essa mensagem
function caso(nome, branch, command, espera) {
  execSync(`git checkout -q -B ${branch}`, { cwd: repo });
  const r = spawnSync(process.execPath, [hook], {
    input: JSON.stringify({ tool_input: { command } }),
    env: { ...process.env, CLAUDE_PROJECT_DIR: repo },
    encoding: "utf8",
  });
  const ok = espera ? r.status === 2 && espera.test(r.stderr) : r.status === 0;
  if (!ok) falhas++;
  console.log(`  ${ok ? "ok  " : "FALHOU"} ${nome} (saída ${r.status})`);
}

caso("comando comum passa", "feat/x", "ls -la", null);
caso("texto citando git push não conta", "main", 'echo "git push --force origin main"', null);
caso("commit na main bloqueia", "main", 'git commit -m "x"', /Você está na main/);
caso("commit na master bloqueia", "master", "git add -A && git commit -am x", /Você está na master/);
caso("push para main bloqueia", "feat/x", "git push origin main", /Push para main/);
caso("push HEAD:main bloqueia", "feat/x", "rtk git push origin HEAD:main", /Push para main/);
caso("push forçado bloqueia", "feat/x", "git push --force origin feat/x", /Push forçado/);
caso("branch com main no nome vai para o verify", "feat/main-menu", "git push -u origin feat/main-menu", /verify falhou/);
caso("commit em branch roda npm run check (falha aqui: sem package.json)", "feat/x", "git commit -m x", /check falhou/);

fs.rmSync(repo, { recursive: true, force: true });
console.log(`== guarda: ${falhas ? falhas + " falha(s)" : "ok"} ==`);
process.exit(falhas ? 1 : 0);
