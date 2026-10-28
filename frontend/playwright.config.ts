import { defineConfig } from "@playwright/test";

// Requiere backend (sirviendo frontend/dist) y worker activos contra la BD de PRUEBA.
// Ver scripts/e2e.ps1.
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  use: { baseURL: process.env.KINETRA_E2E_URL ?? "http://127.0.0.1:8000", locale: "es-BO", timezoneId: "America/La_Paz" },
  reporter: [["list"]],
});
