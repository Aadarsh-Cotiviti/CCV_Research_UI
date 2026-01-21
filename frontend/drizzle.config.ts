import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "sqlite",
  schema: "./db/schemas.ts",
  casing: "snake_case",
  dbCredentials: {
    url: process.env.DB_URL ?? "./sqlite.db",
  },
});
