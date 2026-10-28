"use strict";
// End-to-end no Chromium contra o site servido por HTTP, como no GitHub Pages.
const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "e2e",
  testMatch: "*.spec.cjs",
  workers: 1, // a cobertura junta tudo num relatório só
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  globalSetup: "./e2e/setup.cjs",
  globalTeardown: "./e2e/teardown.cjs",
  use: {
    baseURL: "http://127.0.0.1:8766/",
    serviceWorkers: "block", // sem cache do shell: a cobertura vê o código desta branch
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "celular", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: "python3 -m http.server 8766 --bind 127.0.0.1",
    url: "http://127.0.0.1:8766/",
    reuseExistingServer: !process.env.CI,
  },
});
