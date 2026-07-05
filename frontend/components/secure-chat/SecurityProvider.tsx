
"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { generateEncryptionKey, exportKey } from "@/lib/security/crypto";

interface SecurityContextType {
    masterKey: CryptoKey | null;
    isReady: boolean;
}

const SecurityContext = createContext<SecurityContextType | undefined>(undefined);

export function SecurityProvider({ children }: { children: React.ReactNode }) {
    const [masterKey, setMasterKey] = useState<CryptoKey | null>(null);
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        const initSecurity = async () => {
            if (!window.crypto?.subtle) {
                console.warn("Web Crypto encryption is unavailable on this origin; secure-chat encryption is disabled.");
                setIsReady(true);
                return;
            }

            try {
                // In a real "Zero-Leak" app, we might derive this from a user password 
                // or a server-sent ephemeral token, but here we generate a fresh session key.
                // This key is strictly memory-resident for this tab.
                const key = await generateEncryptionKey();
                setMasterKey(key);
                setIsReady(true);
                console.log("Secure Session Initialized: Zero-Leak Protocols Active");
            } catch (e) {
                console.error("Failed to initialize security context", e);
            }
        };

        initSecurity();
    }, []);

    return (
        <SecurityContext.Provider value={{ masterKey, isReady }}>
            {children}
        </SecurityContext.Provider>
    );
}

export function useSecurity() {
    const context = useContext(SecurityContext);
    if (context === undefined) {
        throw new Error("useSecurity must be used within a SecurityProvider");
    }
    return context;
}
