# DWG runtime options

KRAFZEN supports native external CLI conversion without changing file extensions.

- Default: GNU LibreDWG, GPLv3-or-later. Install reviewed native `dwg2dxf` and `dxf2dwg` binaries on the same host, set `DWG_CONVERTER_TYPE=LIBREDWG`, and optionally set `DWG_LIBREDWG_DWG2DXF` / `DWG_LIBREDWG_DXF2DWG` to their paths. Export explicitly targets R2000 (AC1015). Newer or unsupported entities may lose fidelity; review roundtrips, layers, units, dimensions and annotations. No binaries are redistributed by this change.
- Existing ODA runtime: only select `DWG_CONVERTER_TYPE=ODA` and `DWG_ODA_USE_AUTHORIZED=true` after confirming applicable commercial/SaaS rights and approved runtime package. The free ODA application is not an unconditional commercial license. Audit existing bundled binaries and redistribution rights.
- Imported DWG still requires current malware signatures and scanner; converted DXF is rescanned and parsed. Neither converter accepts arbitrary remote URLs.

Native runtime must be installed and tested using real drawings before marking hosted conversion operational. Executable discovery is not evidence of conversion fidelity. Keep user originals locally.

Sources: https://www.gnu.org/software/libredwg/manual/html_node/Encoding.html ; https://www.gnu.org/software/libredwg/manual/html_node/Programs.html ; https://www.opendesign.com/faq/question/what-are-oda-viewer-and-oda-file-converter
