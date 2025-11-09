import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    include: ["tests/sentinels/**/*.test.{ts,tsx,js,mjs}", "tests/sentinels/**/*.spec.{ts,tsx,js,mjs}"],
    globals: true,
    environment: "node",
    setupFiles: []
  },
  resolve: {
    alias: {
      "@fixtures": path.resolve("./contracts/fixtures")
    }
  }
});
