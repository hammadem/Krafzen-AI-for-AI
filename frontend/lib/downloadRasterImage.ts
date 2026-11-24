const RASTER_TYPES: Record<string,string> = {"image/png":"png","image/jpeg":"jpg","image/webp":"webp"};
const MAX_BYTES = 16 * 1024 * 1024;

export function isRasterSource(source: string): boolean {
    if (/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/i.test(source)) return source.length <= Math.ceil(MAX_BYTES * 4 / 3) + 100;
    try {
        const url = new URL(source);
        return url.protocol === "https:" && !url.username && !url.password;
    } catch { return false; }
}

/** Browser-only direct retrieval. No cross-origin server relay or unsafe navigation. */
export async function downloadRasterImage(source: string) {
    if (!isRasterSource(source)) throw new Error("Unsupported image source.");
    const res = await fetch(source, {credentials:"omit",redirect:"error",cache:"no-store",signal:AbortSignal.timeout(30000)});
    if (!res.ok) throw new Error("Image download unavailable. Use the saved file's authenticated download.");
    const declared = Number(res.headers.get("content-length") || 0);
    const mime = (res.headers.get("content-type") || "").split(";")[0].toLowerCase();
    if (!RASTER_TYPES[mime] || declared > MAX_BYTES || !res.body) throw new Error("Unsupported or oversized image.");
    const reader = res.body.getReader();
    const chunks: Uint8Array<ArrayBuffer>[] = [];
    let total = 0;
    try {
        while (true) {
            const {done,value} = await reader.read();
            if (done) break;
            total += value.byteLength;
            if (total > MAX_BYTES) { await reader.cancel(); throw new Error("Image exceeds the supported download size."); }
            chunks.push(new Uint8Array(value));
        }
    } finally { reader.releaseLock(); }
    if (!total) throw new Error("Image is empty.");
    const blob = new Blob(chunks,{type:mime});
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = "design-"+Date.now()+"."+RASTER_TYPES[mime];
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(()=>URL.revokeObjectURL(href),1000);
}
