import { getApiBaseUrl } from "@/lib/api/utils";

export type AccessStatus = { subscription?: {plan_name?:string;status?:string}; balance?: {can_access_workspace?:boolean} };

export function destinationFromAccess(data: AccessStatus): "/workspace" | "/pricing" {
    return data?.balance?.can_access_workspace === true ? "/workspace" : "/pricing";
}

export async function getPostLoginDestination(token: string): Promise<"/workspace" | "/pricing"> {
    if (!token) throw new Error("Missing verified session");
    const response = await fetch(`${getApiBaseUrl()}/api/v1/payments/subscription-status`, {
        headers: { Authorization: `Bearer ${token}` }, cache: "no-store",
        signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) throw new Error("Unable to verify account access");
    const status = await response.json() as AccessStatus;
    if (typeof status?.balance?.can_access_workspace !== "boolean") {
        throw new Error("Account access response incomplete");
    }
    return destinationFromAccess(status);
}
