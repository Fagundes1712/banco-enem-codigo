"use strict";
/* Hook PreToolUse (Bash) do Claude Code: barra commit e push na branch principal e roda as checagens antes de commit e push.
   Sai com 2 para bloquear; o texto em stderr volta para o Claude. */
const { execSync } = require("node:child_process");

let entrada = "";
process.stdin.on("data", (d) => (entrada += d));
process.stdin.on("end", () => {
  // só os trechos que começam com git (ou rtk git); texto dentro de heredoc ou string não conta
  const cmd = ((JSON.parse(entrada || "{}").tool_input || {}).command || "")
    .split(/[;&|\n]+/).map((s) => s.trim()).filter((s) => /^(rtk\s+)?git\s/.test(s)).join("\n");
  // o commit vale para a pasta do `cd` ou do `git -C` do próprio comando (outro clone ou worktree), não só para o projeto
  const bruto = (JSON.parse(entrada || "{}").tool_input || {}).command || "";
  const dir = (bruto.match(/^\s*cd\s+("[^"]+"|'[^']+'|\S+)\s*(&&|;)/) || cmd.match(/^(?:rtk\s+)?git\s+-C\s+("[^"]+"|\S+)/m) || [])[1];
  let raiz = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  if (dir) {
    let d = dir.replace(/^["']|["']$/g, "");
    if (process.platform === "win32") d = d.replace(/^\/([a-z])\//i, "$1:/"); // caminho do Git Bash
    raiz = require("node:path").resolve(raiz, d);
  }
  const sh = (c) => execSync(c, { cwd: raiz, stdio: "pipe", encoding: "utf8" }).trim();
  const bloquear = (msg) => (process.stderr.write(msg + "\n"), process.exit(2));

  const sub = (nome) => new RegExp(`^(rtk\\s+)?git\\s+(-C\\s+\\S+\\s+|-\\S+\\s+)*${nome}\\b`, "m").test(cmd);
  const commit = sub("commit");
  const push = sub("push");
  if (!commit && !push) return;

  let branch = "";
  try { branch = sh("git branch --show-current"); } catch { return; }
  // o hook roda antes do comando: uma troca de branch no mesmo comando vale para o commit que vem depois
  for (const m of cmd.matchAll(/^(?:rtk\s+)?git\s+(?:switch|checkout)\s+(?:-\S+\s+)*(\S+)\s*$/gm))
    if (!/\s--\s/.test(m[0])) branch = m[1];
  const principal = /^(main|master)$/;

  const pushes = cmd.split("\n").filter((s) => /^(rtk\s+)?git\s+(-\S+\s+)*push\b/.test(s)).join("\n");
  if (/(--force\b|\s-f\b|\s\+\S+)/.test(pushes) && !/--force-with-lease/.test(pushes))
    bloquear("Push forçado bloqueado. Use --force-with-lease só na sua branch de trabalho.");
  if (pushes.split(/\s+/).some((t) => /^(\S*:)?(refs\/heads\/)?(main|master)$/.test(t)))
    bloquear("Push para main/master bloqueado: abra um PR a partir de uma branch.");
  if (principal.test(branch))
    bloquear(`Você está na ${branch}. Crie uma branch antes: git switch -c <tipo>/<assunto>.`);

  try {
    sh(push ? "npm run verify" : "npm run check");
  } catch (e) {
    bloquear(`${push ? "npm run verify" : "npm run check"} falhou; corrija antes de ${push ? "enviar" : "commitar"}.\n${(e.stdout || "").slice(-2000)}`);
  }
});
