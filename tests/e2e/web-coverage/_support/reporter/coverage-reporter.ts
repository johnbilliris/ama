/**
 * Custom Playwright reporter for the spec-034 web coverage suite (T033).
 *
 * Emits one CoverageTraceRow per (test × FR) into
 * `tests/e2e/web-coverage/_artifacts/coverage-trace.partial-{shard}.json`.
 * The trace-merge.py CLI (T048) merges these shard files into the canonical
 * coverage-trace.{md,json} artefacts under specs/034-…/.
 *
 * Cycle-1 amendment (T182, Q26): also emits
 * `tests/e2e/web-coverage/_artifacts/cycle-metadata.json` exactly once
 * per run from `onBegin()`. Conforms to
 * `contracts/cycle-metadata.schema.json` and gives the suite-side a
 * symmetric surface for the same cycle boundary the audit-list endpoint
 * reads from `bootstrap_seed_data().current_cycle_start` server-side.
 *
 * Implementation notes (Q26):
 *   • cycle_start_ts is read from
 *     ``packages/domain/src/domain/seed/bootstrap.py`` ``CURRENT_CYCLE_START``
 *     constant via a small regex parse (no python invocation needed at
 *     onBegin — must be sync-friendly and runnable on a clean checkout
 *     even before the API is up).
 *   • cycle_id is generated once via ``crypto.randomUUID()``.
 *   • commit_sha pulls from ``GITHUB_SHA`` first, falls back to
 *     ``git rev-parse HEAD``.
 *   • seed_hash is sha256 of the canonical concat of the four seed JSON
 *     files, sorted by filename. This is byte-stable across runs on the
 *     same seed (SC-010) without needing the API server.
 *   • Validation against the embedded schema is hand-rolled (the task
 *     suggests ajv but adding a runtime dependency is heavier than the
 *     four field checks; deviation documented here for review).
 */
import type {
  Reporter,
  TestCase,
  TestResult,
  FullResult,
  FullConfig,
  Suite,
} from "@playwright/test/reporter";
import { execSync } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { parseTagString } from "./annotations";
import { buildTraceRow, sortRowsDeterministic } from "./trace-row";
import { redact } from "./redact";
import type { CoverageTrace, CoverageTraceRow } from "../types/coverage";

interface ReporterOptions {
  outputDir?: string;
  shardId?: string;
  /** Override repo root for testing — defaults to walking up from __dirname. */
  repoRoot?: string;
}

interface CycleMetadata {
  cycle_start_ts: string;
  cycle_id: string;
  commit_sha: string;
  seed_hash: string;
}

/**
 * Read CURRENT_CYCLE_START from bootstrap.py. The python module is the
 * single source of truth (FR-029 + Q26); we parse the literal rather
 * than invoking python because onBegin must work without a running
 * server and without spawning interpreters.
 */
function readCycleStartTs(repoRoot: string): string {
  const bootstrapPath = resolve(
    repoRoot,
    "packages",
    "domain",
    "src",
    "domain",
    "seed",
    "bootstrap.py",
  );
  const text = readFileSync(bootstrapPath, "utf-8");
  const match = text.match(/CURRENT_CYCLE_START\s*=\s*"([^"]+)"/);
  if (!match) {
    throw new Error(
      `cycle-metadata: could not parse CURRENT_CYCLE_START from ${bootstrapPath}`,
    );
  }
  // Schema requires ISO-8601 with date-time format. The Python literal
  // "2026-02-01T00:00:00+00:00" is already a valid date-time. Schema's
  // ajv "format: date-time" will accept it as-is.
  return match[1];
}

/**
 * SHA-256 (lowercase hex) of the canonical concat of every JSON file
 * under packages/domain/src/domain/seed/, sorted by filename. Stable
 * across runs on the same seed (SC-010 invariant).
 */
function computeSeedHash(repoRoot: string): string {
  const seedDir = resolve(
    repoRoot,
    "packages",
    "domain",
    "src",
    "domain",
    "seed",
  );
  const jsonFiles = readdirSync(seedDir)
    .filter((name) => name.endsWith(".json"))
    .sort();
  const hash = createHash("sha256");
  for (const filename of jsonFiles) {
    hash.update(filename);
    hash.update("\n");
    hash.update(readFileSync(resolve(seedDir, filename)));
    hash.update("\n");
  }
  return hash.digest("hex");
}

/**
 * Resolve commit SHA: env var first (CI), then `git rev-parse HEAD`.
 * Schema enforces ^[0-9a-f]{40}$ — we coerce lowercase + trim.
 */
function resolveCommitSha(repoRoot: string): string {
  const envSha = process.env.GITHUB_SHA?.trim().toLowerCase();
  if (envSha && /^[0-9a-f]{40}$/.test(envSha)) {
    return envSha;
  }
  try {
    const sha = execSync("git rev-parse HEAD", {
      cwd: repoRoot,
      encoding: "utf-8",
    })
      .trim()
      .toLowerCase();
    if (/^[0-9a-f]{40}$/.test(sha)) {
      return sha;
    }
  } catch {
    // Fall through to deterministic placeholder — schema will reject and
    // the reporter will throw, alerting the operator to a detached HEAD
    // or shallow checkout.
  }
  return "0".repeat(40);
}

/**
 * Hand-rolled validator for cycle-metadata.schema.json. Mirrors the
 * embedded JSON Schema shape; throws with a precise message on failure
 * so onBegin fails loud rather than silently writing a malformed file.
 */
function validateCycleMetadata(metadata: CycleMetadata): void {
  if (!Number.isFinite(Date.parse(metadata.cycle_start_ts))) {
    throw new Error(
      `cycle-metadata: cycle_start_ts "${metadata.cycle_start_ts}" is not a valid date-time`,
    );
  }
  if (
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      metadata.cycle_id,
    )
  ) {
    throw new Error(`cycle-metadata: cycle_id "${metadata.cycle_id}" is not a UUID`);
  }
  if (!/^[0-9a-f]{40}$/.test(metadata.commit_sha)) {
    throw new Error(
      `cycle-metadata: commit_sha "${metadata.commit_sha}" is not 40-hex; check GITHUB_SHA / shallow clone depth`,
    );
  }
  if (!/^[0-9a-f]{64}$/.test(metadata.seed_hash)) {
    throw new Error(`cycle-metadata: seed_hash "${metadata.seed_hash}" is not 64-hex`);
  }
}

export default class CoverageReporter implements Reporter {
  private rows: CoverageTraceRow[] = [];
  private outputDir: string;
  private shardId: string;
  private repoRoot: string;

  constructor(options: ReporterOptions = {}) {
    this.outputDir = options.outputDir
      ?? resolve(__dirname, "..", "..", "_artifacts");
    this.shardId = options.shardId
      ?? process.env.PLAYWRIGHT_SHARD_INDEX
      ?? process.env.SHARD_ID
      ?? "1";
    // Walk five levels up from
    // tests/e2e/web-coverage/_support/reporter/coverage-reporter.ts
    // → repo root.
    this.repoRoot = options.repoRoot
      ?? resolve(__dirname, "..", "..", "..", "..", "..");
  }

  onBegin(config: FullConfig, _suite: Suite): void {
    mkdirSync(this.outputDir, { recursive: true });

    // Pull the shard index from Playwright's FullConfig — this is the
    // canonical source when the suite was launched with `--shard=N/M`.
    // The constructor's process.env fallbacks remain for local one-shard
    // runs and for tests that instantiate the reporter directly.
    if (config.shard && typeof config.shard.current === "number") {
      this.shardId = String(config.shard.current);
    }

    // Cycle metadata is shard-invariant — only shard 1 writes it so
    // parallel shards don't race on the same path. Other shards still
    // see the file because the merge job (T152) consumes it from disk.
    if (this.shardId !== "1") {
      return;
    }

    const metadata: CycleMetadata = {
      cycle_start_ts: readCycleStartTs(this.repoRoot),
      cycle_id: randomUUID(),
      commit_sha: resolveCommitSha(this.repoRoot),
      seed_hash: computeSeedHash(this.repoRoot),
    };
    validateCycleMetadata(metadata);

    const target = resolve(this.outputDir, "cycle-metadata.json");
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, JSON.stringify(metadata, null, 2) + "\n", "utf-8");
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    const annotationText = [
      ...test.annotations.map((a) => `${a.type}${a.description ? ":" + a.description : ""}`),
      test.title,
    ].join(" ");

    const tags = parseTagString(annotationText);
    if (!tags) {
      return; // Tests outside the coverage taxonomy (smoke etc.) emit nothing.
    }

    const status: CoverageTraceRow["status"] = (() => {
      if (result.status === "passed") return "passed";
      if (result.status === "skipped") return "skipped";
      if (result.status === "interrupted") return "skipped";
      return "failing";
    })();

    const correlationIdAttachment = result.attachments.find((a) => a.name === "correlation-id");
    const correlationId = correlationIdAttachment?.body?.toString("utf-8")?.trim() ?? "";

    const auditAttachment = result.attachments.find((a) => a.name === "audit-evidence-id");
    const auditEvidenceId = auditAttachment?.body?.toString("utf-8")?.trim() ?? null;

    const route = (result.attachments.find((a) => a.name === "route")?.body?.toString("utf-8")?.trim()) ?? "/";
    const aiimsAttachment = result.attachments.find((a) => a.name === "aiims-function");
    const aiimsFunction = (aiimsAttachment?.body?.toString("utf-8")?.trim() ?? "control") as CoverageTraceRow["aiims_function"];

    for (const fr of tags.frs) {
      this.rows.push(
        buildTraceRow({
          tags,
          fr_id: fr,
          test_id: test.id,
          route,
          audit_evidence_id: auditEvidenceId || null,
          correlation_id: correlationId,
          status,
          duration_ms: Math.max(0, Math.round(result.duration ?? 0)),
          aiims_function: aiimsFunction,
        }),
      );
    }
  }

  async onEnd(_result: FullResult): Promise<void> {
    const trace: CoverageTrace = {
      generated_at: new Date().toISOString(),
      spec: "034-webapp-capstone-coverage",
      schema_version: 1,
      rows: sortRowsDeterministic(this.rows),
    };
    const target = resolve(this.outputDir, `coverage-trace.partial-${this.shardId}.json`);
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, JSON.stringify(redact(trace), null, 2) + "\n", "utf-8");
  }

  printsToStdio(): boolean {
    return false;
  }
}
