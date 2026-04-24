"use client";

import { useState } from "react";
import {
  createAnnotation,
  updateAnnotation,
  deleteAnnotation,
  type PlaybackEvent,
} from "@/lib/api/simulation-playback";

interface Props {
  tenantId: string;
  currentSimTime: number;
  annotations: PlaybackEvent[];
  currentUserOid: string;
  onCreated?: (ann: PlaybackEvent) => void;
  onUpdated?: (ann: PlaybackEvent) => void;
  onDeleted?: (annotationId: string) => void;
  onSeek?: (simTime: number) => void;
}

export function PlaybackAnnotationPanel({
  tenantId,
  currentSimTime,
  annotations,
  currentUserOid,
  onCreated,
  onUpdated,
  onDeleted,
  onSeek,
}: Props) {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    const text = draft.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    try {
      const ann = await createAnnotation(tenantId, currentSimTime, text);
      onCreated?.(ann);
      setDraft("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const startEdit = (ann: PlaybackEvent) => {
    setEditingId(ann.id);
    setEditDraft(String(ann.payload?.text ?? ""));
  };

  const saveEdit = async (ann: PlaybackEvent) => {
    const text = editDraft.trim();
    if (!text) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await updateAnnotation(tenantId, ann.id, text);
      onUpdated?.(updated);
      setEditingId(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (ann: PlaybackEvent) => {
    if (!window.confirm("Delete this annotation?")) return;
    setBusy(true);
    setError(null);
    try {
      await deleteAnnotation(tenantId, ann.id);
      onDeleted?.(ann.id);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="playback-annotation-panel">
      <header>
        <h3>Annotations ({annotations.length})</h3>
        <p className="playback-annotation-hint">
          Add review notes pinned to timeline positions.
        </p>
      </header>

      <div className="playback-annotation-compose">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={`Add annotation at ${formatTime(currentSimTime)}…`}
          rows={2}
          maxLength={2000}
        />
        <button
          type="button"
          onClick={submit}
          disabled={busy || !draft.trim()}
          className="playback-annotation-submit"
        >
          Pin at {formatTime(currentSimTime)}
        </button>
      </div>

      {error && (
        <p role="alert" className="playback-annotation-error">
          {error}
        </p>
      )}

      <ul className="playback-annotation-list">
        {annotations
          .slice()
          .sort((a, b) => a.sim_time_offset - b.sim_time_offset)
          .map((ann) => {
            const author = String(ann.payload?.author_oid ?? "unknown");
            const text = String(ann.payload?.text ?? "");
            const updatedAt = ann.payload?.updated_at;
            const editable = author === currentUserOid;
            return (
              <li key={ann.id}>
                <div className="playback-annotation-head">
                  <button
                    type="button"
                    className="playback-annotation-ts"
                    onClick={() => onSeek?.(ann.sim_time_offset)}
                    title="Seek to this point"
                  >
                    {formatTime(ann.sim_time_offset)}
                  </button>
                  <span className="playback-annotation-author">{author}</span>
                </div>
                {editingId === ann.id ? (
                  <>
                    <textarea
                      value={editDraft}
                      onChange={(e) => setEditDraft(e.target.value)}
                      rows={2}
                      maxLength={2000}
                    />
                    <div className="playback-annotation-actions">
                      <button onClick={() => saveEdit(ann)} disabled={busy}>Save</button>
                      <button onClick={() => setEditingId(null)}>Cancel</button>
                    </div>
                  </>
                ) : (
                  <>
                    <p className="playback-annotation-body">{text}</p>
                    {updatedAt && (
                      <p className="playback-annotation-meta">edited</p>
                    )}
                    {editable && (
                      <div className="playback-annotation-actions">
                        <button onClick={() => startEdit(ann)} disabled={busy}>Edit</button>
                        <button onClick={() => remove(ann)} disabled={busy}>Delete</button>
                      </div>
                    )}
                  </>
                )}
              </li>
            );
          })}
      </ul>
    </aside>
  );
}

function formatTime(total: number) {
  const t = Math.max(0, Math.floor(total));
  const h = String(Math.floor(t / 3600)).padStart(2, "0");
  const m = String(Math.floor((t % 3600) / 60)).padStart(2, "0");
  const s = String(t % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}
