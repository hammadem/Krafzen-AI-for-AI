"use client";

import { useEffect, useState } from "react";
import { Camera, Image as ImageIcon } from "lucide-react";
import {
    getFieldPhotoSignedUrl, getFieldPhotos, uploadFieldPhoto,
} from "@/lib/api/api";

type PhotoEvidence = {
    id: string; inspection_id: string; mime_type: string; size_bytes: number;
    created_at?: string | null; source_metadata?: {
        malware_scan_completed?: boolean; exif_gps_removed?: boolean;
        image_width_px?: number; image_height_px?: number;
    };
};

export default function FieldEvidencePanel({
    inspectionId, user,
}: {
    inspectionId: string; user: User | null;
}) {
    const [open, setOpen] = useState(false);
    const [photos, setPhotos] = useState<PhotoEvidence[]>([]);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [photoLinks, setPhotoLinks] = useState<Record<string,string>>({});

    useEffect(() => {
        if (!open || !user?.access_token) return;
        let active = true;
        async function load() {
            const response = await getFieldPhotos(user, inspectionId);
            if (!response.ok) throw new Error(response.error?.message || "Cannot load site photos");
            if (active) setPhotos(
                Array.isArray(response.data) ? response.data as unknown as PhotoEvidence[] : []
            );
        }
        void load().catch((cause: unknown) => {
            if (active) setError(cause instanceof Error ? cause.message : "Photos unavailable");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open, inspectionId, user?.access_token]);

    async function attach(file: File | null) {
        if (!file || !user || uploading) return;
        const ext = file.name.split(".").pop()?.toLowerCase();
        if (!ext || !["jpeg", "jpg", "png", "webp"].includes(ext) ||
            !file.size || file.size > 10 * 1024 * 1024) {
            setError("Choose a nonempty JPG, PNG or WebP photo no larger than 10 MB");
            return;
        }
        setUploading(true); setError(null); setNotice(null);
        try {
            const response = await uploadFieldPhoto(user, inspectionId, file);
            if (!response.ok) throw new Error(response.error?.message || "Photo could not be saved");
            const saved = response.data as unknown as PhotoEvidence;
            if (!saved?.id || !saved?.source_metadata?.malware_scan_completed ||
                !saved?.source_metadata?.exif_gps_removed) {
                throw new Error("Server did not verify the scanned, EXIF-free photo record");
            }
            setPhotos(list => [...list, saved]);
            setNotice("Photo scanned, location metadata removed and saved privately.");
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Cannot attach photo");
        } finally {
            setUploading(false);
        }
    }

    async function view(photoId: string) {
        if (!user?.access_token) return;
        setError(null);
        try {
            const response = await getFieldPhotoSignedUrl(user, photoId);
            if (!response.ok) throw new Error(response.error?.message || "Private photo unavailable");
            const info = response.data as unknown as { signed_url?: string };
            const url = new URL(info.signed_url || "");
            if (url.protocol !== "https:") throw new Error("Unsafe signed photo destination");
            setPhotoLinks(old => ({ ...old, [photoId]: url.toString() }));
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Cannot view photo");
        }
    }

    return (
        <div className="border-t border-white/10 pt-3 space-y-2">
            <button type="button" className="flex gap-2 items-center text-xs underline"
                onClick={() => setOpen(value => !value)}>
                <Camera className="h-4 w-4"/>
                {open ? "Hide photo evidence" : "Show / attach site photos"}
            </button>
            {open && (
                <>
                    <label className="block text-xs">
                        Choose field photograph
                        <input type="file" accept=".jpg,.jpeg,.png,.webp"
                            aria-label="Choose field photograph" disabled={uploading}
                            onChange={event => {
                                void attach(event.target.files?.[0] || null);
                                event.currentTarget.value = "";
                            }}
                            className="mt-2 block w-full"/>
                    </label>
                    <p className="text-xs text-slate-400">
                        Requires malware scanning; GPS, EXIF and device details are removed before private storage.
                        Upload does not verify a defect.
                    </p>
                    {uploading && <p role="status" className="text-xs">Scanning and saving photograph…</p>}
                    {notice && <p role="status" className="text-xs text-emerald-300">{notice}</p>}
                    {error && <p role="alert" className="text-xs text-red-300">{error}</p>}
                    {photos.length === 0 &&
                        <p className="text-xs text-slate-400">No saved photo evidence for this inspection.</p>}
                    {photos.map(photo => (
                        <div key={photo.id} className="flex items-center gap-2 flex-wrap text-xs">
                            <ImageIcon className="h-4 w-4"/>
                            <span>{photo.source_metadata?.image_width_px || "?"} × {photo.source_metadata?.image_height_px || "?"} px</span>
                            <button type="button" onClick={() => void view(photo.id)} className="underline">
                                Request private photo link
                            </button>
                            {photoLinks[photo.id] && (
                                <a href={photoLinks[photo.id]} target="_blank" rel="noopener noreferrer"
                                    className="text-emerald-300 underline">Open privacy-sanitized observation photo</a>
                            )}
                        </div>
                    ))}
                </>
            )}
        </div>
    );
}
