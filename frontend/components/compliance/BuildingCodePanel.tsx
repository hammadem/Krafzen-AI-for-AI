"use client";

import { useState } from "react";
import { createBuildingCodeAssessment } from "@/lib/api/api";

type User = Parameters<typeof createBuildingCodeAssessment>[0];
type Props = {
    user: User; projectId: string; sourceFile: string;
    context: { state: string; municipality: string; project_address: string; occupancy: string; building_type: string };
    onSaved: (record: unknown) => void;
};

const measurementFields = [
    ["stair_occupant_load", "Stair occupant load served (persons)"],
    ["stair_clear_width_in", "Available stair capacity width (in)"],
    ["other_occupant_load", "Other egress component load (persons)"],
    ["other_clear_width_in", "Other component capacity width (in)"],
    ["emergency_duration_minutes", "Emergency lighting duration (min)"],
    ["initial_average_fc", "Initial average illumination (fc)"],
    ["initial_minimum_fc", "Initial minimum illumination (fc)"],
    ["final_average_fc", "90-minute average illumination (fc)"],
    ["final_minimum_fc", "90-minute minimum illumination (fc)"],
    ["measured_maximum_fc", "Maximum measured illumination (fc)"],
    ["measured_minimum_fc", "Minimum measured illumination (fc)"],
] as const;
const contextFields = [
    ["construction_type", "Construction type"],
    ["building_height_ft", "Building height (ft)"],
    ["building_area_sqft", "Building area (sq ft)"],
    ["adoption_reference", "Adopted code ordinance / amendment reference"],
    ["reviewer_name", "Qualified reviewer name (user asserted)"],
] as const;
const boolFields = [
    ["ibc_applicability_confirmed", "2024 IBC applies to this project"],
    ["nfpa101_applicability_confirmed", "2024 NFPA 101 applies to this project"],
    ["local_amendments_reviewed_no_conflict", "Reviewer checked adoption, amendments and applicable editions; no conflicting amendment governs these checks"],
    ["other_egress_exceptions_excluded", "Reviewer excludes other egress capacity exceptions"],
    ["qualifying_sprinkler_system_confirmed", "Qualifying full-building sprinkler system per selected exception confirmed"],
    ["qualifying_voice_alarm_confirmed", "Qualifying emergency voice/alarm system confirmed"],
    ["emergency_lighting_required_confirmed", "Applicable NFPA emergency lighting requirement confirmed"],
    ["floor_level_egress_photometry_confirmed", "Photometry measured at floor level along the egress path, including the end of the 90-minute period"],
] as const;

export default function BuildingCodePanel({ user, projectId, sourceFile, context, onSaved }: Props) {
    const [values, setValues] = useState<Record<string, string>>({});
    const [flags, setFlags] = useState<Record<string, boolean>>({});
    const [ibc, setIbc] = useState("unknown");
    const [nfpa, setNfpa] = useState("unknown");
    const [basis, setBasis] = useState("unknown_or_other");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const numeric = (key: string) => {
        const raw = values[key]?.trim();
        if (!raw) return null;
        const number = Number(raw);
        if (!Number.isFinite(number) || number < 0) throw new Error("Invalid numeric measurement: " + key);
        return number;
    };
    async function submit() {
        if (!projectId || saving) return;
        setError(""); setSaving(true);
        try {
            const response = await createBuildingCodeAssessment(user, {
                project_id: projectId, source_file_id: sourceFile || null,
                jurisdiction: {
                    ...context, construction_type: values.construction_type || "",
                    building_height_ft: numeric("building_height_ft"),
                    building_area_sqft: numeric("building_area_sqft"),
                    adoption_reference: values.adoption_reference || "",
                    reviewer_name: values.reviewer_name || "",
                    ibc_edition: ibc, nfpa101_edition: nfpa,
                    ibc_applicability_confirmed: !!flags.ibc_applicability_confirmed,
                    nfpa101_applicability_confirmed: !!flags.nfpa101_applicability_confirmed,
                    local_amendments_reviewed_no_conflict: !!flags.local_amendments_reviewed_no_conflict,
                },
                measurements: {
                    ...Object.fromEntries(measurementFields.map(([key]) => [key, numeric(key)])),
                    egress_factor_basis: basis,
                    ...Object.fromEntries(boolFields.slice(3).map(([key]) => [key, !!flags[key]])),
                },
            });
            if (!response.ok) throw new Error(response.error?.message || "Code evidence not saved");
            onSaved(response.data);
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Code assessment failed");
        } finally {
            setSaving(false);
        }
    }
    return (
        <section className="space-y-4 rounded-xl border border-white/10 p-5">
            <h2 className="font-semibold">IBC and NFPA measured rule evidence</h2>
            <p className="text-sm text-amber-200">
                Uses the project jurisdiction and optional evidence file selected above. Without applicable
                edition, reviewer, source evidence and local-amendment confirmation, numerical checks remain
                unknown. Only 2024 IBC egress capacity and 2024 NFPA 101 emergency lighting provisions are
                encoded here. The full category coverage register identifies every unimplemented area.
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
                {contextFields.map(([key, label]) => (
                    <label className="block text-sm" key={key}>{label}
                        <input aria-label={label} value={values[key] || ""}
                            type={key === "building_height_ft" || key === "building_area_sqft" ? "number" : "text"}
                            onChange={e => setValues(old => ({...old, [key]: e.target.value}))}
                            className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2" />
                    </label>
                ))}
                <label className="block text-sm">IBC adopted edition
                    <select value={ibc} onChange={e => setIbc(e.target.value)}
                        className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                        <option value="unknown">Unknown / other edition (not assessed)</option>
                        <option value="2024">2024 IBC</option>
                    </select>
                </label>
                <label className="block text-sm">NFPA 101 adopted edition
                    <select value={nfpa} onChange={e => setNfpa(e.target.value)}
                        className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                        <option value="unknown">Unknown / other edition (not assessed)</option>
                        <option value="2024">2024 NFPA 101</option>
                    </select>
                </label>
                <label className="block text-sm">IBC capacity factor basis
                    <select value={basis} onChange={e => setBasis(e.target.value)}
                        className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                        <option value="unknown_or_other">Unknown / special case</option>
                        <option value="standard_confirmed">Reviewer confirms standard factor</option>
                        <option value="sprinkler_voice_exception_confirmed">Reviewer confirms sprinkler + voice alarm exception</option>
                    </select>
                </label>
            </div>
            {boolFields.map(([key, label]) => (
                <label className="flex items-start gap-2 text-sm" key={key}>
                    <input type="checkbox" checked={!!flags[key]} onChange={e => setFlags(old => ({...old, [key]: e.target.checked}))} />
                    {label}
                </label>
            ))}
            <div className="grid gap-3 sm:grid-cols-2">
                {measurementFields.map(([key, label]) => (
                    <label key={key} className="block text-sm">{label}
                        <input aria-label={label} type="number" min="0" step="any"
                            value={values[key] || ""} onChange={e => setValues(old => ({...old, [key]: e.target.value}))}
                            className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2" />
                    </label>
                ))}
            </div>
            {error && <p role="alert" className="text-red-300 text-sm">{error}</p>}
            <button type="button" disabled={saving || !projectId} onClick={() => void submit()}
                className="rounded-lg bg-sky-300 px-5 py-2 text-slate-950 font-semibold disabled:opacity-40">
                {saving ? "Evaluating and saving…" : "Run IBC/NFPA checks and save evidence"}
            </button>
        </section>
    );
}
