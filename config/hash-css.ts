#!/usr/bin/env bun

import { createHash } from "crypto";
import { readFileSync, renameSync, existsSync, unlinkSync, readdirSync } from "fs";
import { join } from "path";

const cssPath = join(import.meta.dir, "..", "docs", "statics", "css", "bundle.css");

if (!existsSync(cssPath)) {
  console.error("❌ bundle.css not found");
  process.exit(1);
}

const content = readFileSync(cssPath);
const hash = createHash("sha256").update(content).digest("hex").slice(0, 8);

const cssDir = join(import.meta.dir, "..", "docs", "statics", "css");
for (const file of readdirSync(cssDir)) {
  if (file.startsWith("bundle.") && file !== "bundle.css" && file.endsWith(".css")) {
    unlinkSync(join(cssDir, file));
  }
}

const hashedPath = join(cssDir, `bundle.${hash}.css`);
renameSync(cssPath, hashedPath);
console.log(`✓ Renamed bundle.css → bundle.${hash}.css`);
