import { beforeEach, describe, expect, it } from "vitest";
import { useChatStore } from "@/components/secure-chat/store";

describe("secure chat store", () => {
    beforeEach(() => {
        useChatStore.getState().clearAllSessions();
    });

    it("adds a message without relying on crypto.randomUUID", () => {
        const sessionId = useChatStore.getState().createSession("LAN test");

        useChatStore.getState().addMessage(sessionId, {
            role: "user",
            content: "Create a home office",
        });

        const [message] = useChatStore.getState().sessions[sessionId].messages;
        expect(message.id).toMatch(/^[0-9a-f]{32}$/);
        expect(message.content).toBe("Create a home office");
    });
});
