export async function register() {
  if (process.env.NEXT_RUNTIME === "edge") return;

  // Touch the database on startup so the file/connection is initialized once
  await import("./lib/db").then((module) => module.initDatabase());
}
