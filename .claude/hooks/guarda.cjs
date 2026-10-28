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
  const raiz = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const sh = (c) => execSync(c, { cwd: raiz, stdio: "pipe", encoding: "utf8" }).trim();
  const bloquear = (msg) => (process.stderr.write(msg + "\n"), process.exit(2));

  const sub = (nome) => new RegExp(`^(rtk\\s+)?git\\s+(-C\\s+\\S+\\s+|-\\S+\\s+)*${nome}\\b`, "m").test(cmd);
  const commit = sub("commit");
  const push = sub("push");
  if (!commit && !push) return;

  let branch = "";
  try { branch = sh("git branch --show-current"); } catch { return; }
  const principal = /^(main|master)$/;

  if (push && /(--force\b|\s-f\b|\+\S+)/.test(cmd) && !/--force-with-lease/.test(cmd))
    bloquear("Push forçado bloqueado. Use --force-with-lease só na sua branch de trabalho.");
  if (push && cmd.split(/\s+/).some((t) => /^(\S*:)?(refs\/heads\/)?(main|master)$/.test(t)))
    bloquear("Push para main/master bloqueado: abra um PR a partir de uma branch.");
  if (principal.test(branch))
    bloquear(`Você está na ${branch}. Crie uma branch antes: git switch -c <tipo>/<assunto>.`);

  try {
    sh(push ? "npm run verify" : "npm run check");
  } catch (e) {
    bloquear(`${push ? "npm run verify" : "npm run check"} falhou; corrija antes de ${push ? "enviar" : "commitar"}.\n${(e.stdout || "").slice(-2000)}`);
  }
});
