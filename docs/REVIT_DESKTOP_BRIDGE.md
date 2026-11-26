# Revit desktop exchange (RVT → IFC)

This implements the supported exchange path in ADR 002, not native Linux RVT reading or writing. A customer with a licensed installed Revit can use the Autodesk IFC exporter. No paid cloud API, automatic external transfer or fake file extension is involved.

1. Save the authoritative RVT revision locally. In Revit use File > Export > IFC; choose an appropriate IFC4 or IFC2x3 setup and confirm relevant element/quantity export settings. Review the exported model locally.
2. In KRAFZEN Imports, select the correct project/job and **Revit (RVT) desktop bridge**. Select the original RVT and matching exported IFC, each up to 40 MB. Confirm the relationship.
3. Backend authenticates project ownership, denies unverified regional paths, checks the RVT container signature, scans both files and parses the IFC with IfcOpenShell. It stores the actual IFC and records both hashes and the user-declared source relationship. The RVT is not retained.
4. Inspect the saved IFC through BIM Models, geometry, source query, clash and revision workflows. Keep the original RVT and verify fidelity in Revit. Native RVT file contents and exact correspondence are not independently verified.

Official Autodesk IFC export API: https://help.autodesk.com/view/RVT/2025/ENU/?contextId=HID_DEV_GUIDE_IFC_EXPORT

The current free staging scanner is a release dependency. Native RVT conversion on the server requires a genuine authorized conversion runtime and is not delivered by this bridge.
