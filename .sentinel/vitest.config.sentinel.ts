import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/sentinels/**/*.test.{ts,tsx,js,mjs}"],
    globals: true,
    environment: "node",
    setupFiles: []
  },
  resolve: {
    alias: {
      "@fixtures": "./contracts/fixtures"
    }
  }
});
