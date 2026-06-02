"use client";

// Complete Step 2 file panel: uploader (queue/progress/cancel/retry) on top,
// existing files (list/preview/rename/delete) below. Drop into the workspace
// wherever a job's files belong once Tazwar confirms placement:
//   <FilesPanel jobId={job.id} />

import { useState, useCallback } from "react";
import FileUploader from "@/components/FileUploader";
import FileManager from "@/components/FileManager";
import { apiCache } from "@/lib/api/cache";

export default function FilesPanel({ jobId }: { jobId: string }) {
    // Remount key forces FileManager to re-fetch after an upload completes.
    const [refreshKey, setRefreshKey] = useState(0);

    const handleUploaded = useCallback(() => {
        // The list is a cached GET — invalidate it so the new file shows.
        apiCache.delete(`GET:/api/v1/files/?job_id=${jobId}`);
        setRefreshKey((k) => k + 1);
    }, [jobId]);

    return (
        <div className="flex flex-col gap-6">
            <FileUploader jobId={jobId} onUploaded={handleUploaded} />
            <div className="flex flex-col gap-2">
                <h4 className="text-[#8F8F8F] text-xs uppercase tracking-wide">Files</h4>
                <FileManager key={refreshKey} jobId={jobId} />
            </div>
        </div>
    );
}
