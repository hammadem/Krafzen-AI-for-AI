import {isRasterSource} from "@/lib/downloadRasterImage";
describe("safe browser image downloads",()=>{
    it("allows bounded raster data and HTTPS only",()=>{
        expect(isRasterSource("data:image/png;base64,aGVsbG8=")).toBe(true);
        expect(isRasterSource("https://example.com/image.png")).toBe(true);
        expect(isRasterSource("javascript:alert(1)")).toBe(false);
        expect(isRasterSource("data:image/svg+xml;base64,AAAA")).toBe(false);
        expect(isRasterSource("http://localhost:8000/private")).toBe(false);
        expect(isRasterSource("https://user:password@example.com/image.png")).toBe(false);
    });
});
