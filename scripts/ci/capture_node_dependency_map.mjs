import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

const [inputPath, outputPath, workspaceRoot] = process.argv.slice(2);
if (!inputPath || !outputPath || !workspaceRoot) {
  throw new Error("Usage: capture_node_dependency_map.mjs <pnpm-list.json> <output.tsv|-> <workspace-root>");
}

const projects = JSON.parse(readFileSync(inputPath, "utf8"));
if (!Array.isArray(projects) || projects.length === 0) {
  throw new Error("The installed workspace graph must contain at least one importer");
}

const root = workspaceRoot.replaceAll("\\", "/");
const rows = new Set();
const sections = ["dependencies", "devDependencies", "optionalDependencies"];

function relativeLocation(location) {
  return path.posix.relative(root, location.replaceAll("\\", "/")) || ".";
}

function visit(dependencies, importer, parent) {
  for (const [name, dependency] of Object.entries(dependencies ?? {})) {
    if (typeof dependency.version !== "string" || typeof dependency.path !== "string") {
      throw new Error(`Incomplete installed package identity: ${importer}:${name}`);
    }
    const location = relativeLocation(dependency.path);
    const resolved = dependency.resolved ?? "-";
    if (resolved !== "-") {
      const url = new URL(resolved);
      const allowedHost = url.hostname === "packagefeedproxy.microsoft.io" ||
        url.hostname === "ms-feed-25.pkgs.visualstudio.com";
      if (url.protocol !== "https:" || !allowedHost || url.search || url.username || url.password) {
        throw new Error(`Unapproved or credential-bearing package resolution: ${importer}:${name}`);
      }
    }
    rows.add([importer, parent, name, dependency.version, location, resolved].join("\t"));
    for (const section of sections) visit(dependency[section], importer, location);
  }
}

for (const project of projects) {
  if (typeof project.name !== "string" || typeof project.path !== "string") {
    throw new Error("Incomplete workspace importer identity");
  }
  const importer = relativeLocation(project.path);
  rows.add([importer, "importer", project.name, project.version ?? "-", "-", "-"].join("\t"));
  for (const section of sections) visit(project[section], importer, `${importer}:${section}`);
}

const output = [...rows].sort().join("\n") + "\n";
if (outputPath === "-") process.stdout.write(output);
else writeFileSync(outputPath, output);
console.error(`Installed dependency-map rows: ${rows.size}`);
