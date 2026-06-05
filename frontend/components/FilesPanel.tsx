"use client";

// Step 2 file panel — list/preview/rename/delete for a job's files.
// Note: there is no user-facing upload; Yehor's worker uploads to storage and
// POSTs the metadata, so the frontend only reads/manages existing files.
// Drop in wherever a job's files belong:  <FilesPanel jobId={job.id} />

import FileManager from "@/components/FileManager";

export default function FilesPanel({ jobId }: { jobId: string }) {
    return (
        <div className="flex flex-col gap-2">
            <h4 className="text-[#8F8F8F] text-xs uppercase tracking-wide">Files</h4>
            <FileManager jobId={jobId} />
        </div>
    );
}
