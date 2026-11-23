import FieldEvidencePanel from "@/components/field/FieldEvidencePanel";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { photos, upload, signed } = vi.hoisted(() => ({
    photos: vi.fn(), upload: vi.fn(), signed: vi.fn(),
}));

vi.mock("@/lib/api/api", () => ({
    getFieldPhotos: photos,
    uploadFieldPhoto: upload,
    getFieldPhotoSignedUrl: signed,
}));

const user = { userId: "owner-1", access_token: "token-1" } as User;

describe("Persisted field photo evidence", () => {
    beforeEach(() => {
        photos.mockReset().mockResolvedValue({ ok: true, data: [] });
        upload.mockReset().mockResolvedValue({
            ok: true, data: {
                id: "photo-1", inspection_id: "inspection-1",
                mime_type: "image/jpeg", size_bytes: 2300,
                source_metadata: {
                    malware_scan_completed: true,
                    exif_gps_removed: true,
                    image_width_px: 200, image_height_px: 100,
                }
            }
        });
        signed.mockReset().mockResolvedValue({
            ok: true, data: {
                signed_url: "https://private.example/field/photo?token=valid"
            }
        });
    });

    it("uploads only to the selected inspection and waits for scanned EXIF-free confirmation", async () => {
        render(<FieldEvidencePanel inspectionId="inspection-1" user={user} />);
        fireEvent.click(screen.getByRole("button", { name: "Show / attach site photos" }));
        await waitFor(() => expect(photos).toHaveBeenCalledWith(user, "inspection-1"));
        const file = new File(["image-fixture"], "site.jpg", { type: "image/jpeg" });
        fireEvent.change(screen.getByLabelText("Choose field photograph"), {
            target: { files: [file] }
        });
        await waitFor(() => expect(upload).toHaveBeenCalledWith(user, "inspection-1", file));
        expect(await screen.findByRole("status")).toHaveTextContent(
            /Photo scanned, location metadata removed/
        );
        expect(screen.getByText(/200 × 100 px/)).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Request private photo link" }));
        expect(await screen.findByRole("link", { name: "Open original observation photo" }))
            .toHaveAttribute("href", "https://private.example/field/photo?token=valid");
    });

    it("rejects files larger than 10 MB before network request", async () => {
        render(<FieldEvidencePanel inspectionId="inspection-1" user={user} />);
        fireEvent.click(screen.getByRole("button", { name: "Show / attach site photos" }));
        const file = new File([new Uint8Array(11 * 1024 * 1024)], "massive.png", {
            type: "image/png",
        });
        fireEvent.change(screen.getByLabelText("Choose field photograph"), {
            target: { files: [file] }
        });
        expect(screen.getByRole("alert")).toHaveTextContent(/no larger than 10 MB/);
        expect(upload).not.toHaveBeenCalled();
    });

    it("never claims evidence is saved if backend scan/persistence fails", async () => {
        upload.mockResolvedValueOnce({
            ok: false, error: { message: "Import scanner is not configured" },
        });
        render(<FieldEvidencePanel inspectionId="inspection-1" user={user} />);
        fireEvent.click(screen.getByRole("button", { name: "Show / attach site photos" }));
        fireEvent.change(screen.getByLabelText("Choose field photograph"), {
            target: { files: [new File(["fixture"], "site.jpg")] }
        });
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Import scanner is not configured"
        );
        expect(screen.queryByText(/Photo scanned, location metadata removed/))
            .not.toBeInTheDocument();
    });

    it("does not trust a success response that omits scan and EXIF proof", async () => {
        upload.mockResolvedValueOnce({
            ok: true, data: {
                id: "photo-1",
                source_metadata: { malware_scan_completed: false, exif_gps_removed: false },
            },
        });
        render(<FieldEvidencePanel inspectionId="inspection-1" user={user} />);
        fireEvent.click(screen.getByRole("button", { name: "Show / attach site photos" }));
        fireEvent.change(screen.getByLabelText("Choose field photograph"), {
            target: { files: [new File(["fixture"], "site.jpg")] }
        });
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Server did not verify the scanned, EXIF-free photo record"
        );
    });
});
