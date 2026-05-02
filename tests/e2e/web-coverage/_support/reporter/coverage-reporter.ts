/**
 * Custom Playwright reporter for the spec-034 web coverage suite (T033).
 *
 * Emits one CoverageTraceRow per (test × FR) into
 * `tests/e2e/web-coverage/_artifacts/coverage-trace.partial-{shard}.json`.
 * The trace-merge.py CLI (T048) merges these shard files into the canonical
 * coverage-trace.{md,json} artefacts under specs/034-…/.
 */
import type {
  Reporter,
  TestCase,
  TestResult,
  FullResult,
  FullConfig,
  Suite,
} from "@playwright/test/reporter";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { parseTagString } from "./annotations";
import { buildTraceRow, sortRowsDeterministic } from "./trace-row";
import { redact } from "./redact";
import type { CoverageTrace, CoverageTraceRow } from "../types/coverage";

interface ReporterOptions {
  outputDir?: string;
  shardId?: string;
}

export default class CoverageReporter implements Reporter {
  private rows: CoverageTraceRow[] = [];
  private outputDir: string;
  private shardId: string;

  constructor(options: ReporterOptions = {}) {
    this.outputDir = options.outputDir
      ?? resolve(__dirname, "..", "..", "_artifacts");
    this.shardId = options.shardId
      ?? process.env.PLAYWRIGHT_SHARD_INDEX
      ?? process.env.SHARD_ID
      ?? "1";
  }

  onBegin(_config: FullConfig, _suite: Suite): void {
    mkdirSync(this.outputDir, { recursive: true });
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
