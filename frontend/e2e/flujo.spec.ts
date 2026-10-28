import { test, expect } from "@playwright/test";
import path from "node:path";

// Flujo principal con video SINTÉTICO sin personas (no es un video de paciente).
const VIDEO = process.env.KINETRA_E2E_VIDEO ?? path.resolve(process.cwd(), "../outputs/sintetico_vacio.mp4");
const EMAIL = "e2e@kinetra.local";
const PASS = process.env.KINETRA_E2E_PASSWORD ?? "";

test("rechaza acceso sin sesión", async ({ request }) => {
  expect((await request.get("/api/patients")).status()).toBe(401);
});

test("login → paciente → subir video → procesamiento → resultados", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Correo").fill(EMAIL);
  await page.getByLabel("Contraseña").fill("incorrecta");
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByRole("alert")).toContainText("Credenciales inválidas");

  await page.getByLabel("Contraseña").fill(PASS);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByRole("heading", { name: "Pacientes" })).toBeVisible();

  const apellido = `Sintetico${Date.now()}`;
  await page.getByLabel("Nombres").fill("Paciente");
  await page.getByLabel("Apellidos").fill(apellido);
  await page.getByRole("button", { name: "Registrar" }).click();
  await expect(page.getByRole("heading", { name: `${apellido}, Paciente` })).toBeVisible();
  await expect(page.getByText("Demostración técnica pendiente de validación profesional")).toBeVisible();

  await page.getByLabel(/Archivo de video/).setInputFiles(VIDEO);
  await page.getByRole("button", { name: "Subir y procesar" }).click();
  await expect(page.getByTestId("job-status").first()).toHaveText(/Completado/, { timeout: 90_000 });

  await page.getByRole("link", { name: "Ver resultados" }).click();
  await expect(page.getByText("Sin pose detectada: 30")).toBeVisible();
  await expect(page.getByText(/válidos 0\.0%/)).toBeVisible();
  await expect(page.getByText("No es un rango de movimiento clínico", { exact: false })).toBeVisible();

  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByRole("button", { name: "Ingresar" })).toBeVisible();
});
