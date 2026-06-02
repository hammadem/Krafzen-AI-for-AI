"use client";

// Upload queue hook for Week 2 Step 2.
//
// Why XHR and not fetch: the spec needs real upload *progress* and
// *cancellation*. fetch() exposes neither for request bodies, so we use
// XMLHttpRequest, which gives `upload.onprogress` and `abort()`.
//
// The actual upload endpoint is the one integration point pending Tazwar/Yehor
// (worker-based flow may replace direct upload). Everything else — the queue,
// concurrency, progress, cancel, retry — is real and endpoint-agnostic.

import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import { getApiBaseUrl } from "@/lib/api/utils";
import { FILE_UPLOAD_URL } from "@/lib/api/api";

export type UploadStatus = "queued" | "uploading" | "success" | "error" | "canceled";

export interface UploadItem {
    id: string;
    file: File;
    progress: number; // 0–100
    status: UploadStatus;
    error?: string;
    /** Server file id once the upload succeeds (if the backend returns it). */
    fileId?: string;
}

const MAX_CONCURRENT = 3;

interface UseFileUploadOptions {
    jobId: string;
    /** Called once per file that finishes uploading, so a file list can refresh. */
    onUploaded?: (raw: unknown) => void;
}

export function useFileUpload({ jobId, onUploaded }: UseFileUploadOptions) {
    const { user } = useAuth();
    const [items, setItems] = useState<UploadItem[]>([]);

    // Latest items for the concurrency pump + live XHRs for cancellation.
    const itemsRef = useRef<UploadItem[]>(items);
    useEffect(() => {
        itemsRef.current = items;
    }, [items]);
    const xhrs = useRef<Map<string, XMLHttpRequest>>(new Map());

    const patch = useCallback((id: string, next: Partial<UploadItem>) => {
        setItems((prev) => prev.map((it) => (it.id === id ? { ...it, ...next } : it)));
    }, []);

    const startItem = useCallback(
        (item: UploadItem) => {
            const token = user?.access_token;
            if (!token) {
                patch(item.id, { status: "error", error: "Not authenticated." });
                return;
            }

            patch(item.id, { status: "uploading", progress: 0, error: undefined });

            const xhr = new XMLHttpRequest();
            xhrs.current.set(item.id, xhr);

            const form = new FormData();
            form.append("file", item.file);
            if (jobId) form.append("job_id", jobId);

            xhr.open("POST", `${getApiBaseUrl()}${FILE_UPLOAD_URL()}`);
            xhr.setRequestHeader("Authorization", `Bearer ${token}`);
            const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
            if (anonKey) xhr.setRequestHeader("apikey", anonKey);
            // Note: do NOT set Content-Type — the browser adds the multipart boundary.

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    patch(item.id, { progress: Math.round((e.loaded / e.total) * 100) });
                }
            };

            xhr.onload = () => {
                xhrs.current.delete(item.id);
                if (xhr.status >= 200 && xhr.status < 300) {
                    let parsed: unknown = null;
                    try {
                        parsed = JSON.parse(xhr.responseText);
                    } catch {
                        /* non-JSON success body is fine */
                    }
                    const fileId =
                        parsed && typeof parsed === "object" && "id" in parsed
                            ? String((parsed as { id?: unknown }).id)
                            : undefined;
                    patch(item.id, { status: "success", progress: 100, fileId });
                    onUploaded?.(parsed);
                } else {
                    patch(item.id, {
                        status: "error",
                        error: `Upload failed (${xhr.status || "network"})`,
                    });
                }
            };

            xhr.onerror = () => {
                xhrs.current.delete(item.id);
                patch(item.id, { status: "error", error: "Network error. Check your connection." });
            };

            xhr.onabort = () => {
                xhrs.current.delete(item.id);
                patch(item.id, { status: "canceled" });
            };

            xhr.send(form);
        },
        [user, jobId, onUploaded, patch]
    );

    // Concurrency pump: keep up to MAX_CONCURRENT uploads running.
    useEffect(() => {
        const list = itemsRef.current;
        const active = list.filter((i) => i.status === "uploading").length;
        if (active >= MAX_CONCURRENT) return;
        const toStart = list.filter((i) => i.status === "queued").slice(0, MAX_CONCURRENT - active);
        toStart.forEach(startItem);
    }, [items, startItem]);

    // Abort everything on unmount.
    useEffect(() => {
        const map = xhrs.current;
        return () => {
            map.forEach((xhr) => xhr.abort());
            map.clear();
        };
    }, []);

    const addFiles = useCallback((files: FileList | File[]) => {
        const incoming = Array.from(files).map<UploadItem>((file) => ({
            id: crypto.randomUUID(),
            file,
            progress: 0,
            status: "queued",
        }));
        if (incoming.length) setItems((prev) => [...prev, ...incoming]);
    }, []);

    const cancel = useCallback((id: string) => {
        const xhr = xhrs.current.get(id);
        if (xhr) {
            xhr.abort(); // triggers onabort → status "canceled"
        } else {
            // queued but not started yet
            setItems((prev) => prev.map((it) => (it.id === id ? { ...it, status: "canceled" } : it)));
        }
    }, []);

    const retry = useCallback((id: string) => {
        // Re-queue; the pump picks it up.
        setItems((prev) =>
            prev.map((it) =>
                it.id === id ? { ...it, status: "queued", progress: 0, error: undefined } : it
            )
        );
    }, []);

    const remove = useCallback(
        (id: string) => {
            xhrs.current.get(id)?.abort();
            setItems((prev) => prev.filter((it) => it.id !== id));
        },
        []
    );

    const clearCompleted = useCallback(() => {
        setItems((prev) => prev.filter((it) => it.status !== "success" && it.status !== "canceled"));
    }, []);

    const hasActive = items.some((i) => i.status === "uploading" || i.status === "queued");

    return { items, addFiles, cancel, retry, remove, clearCompleted, hasActive };
}
