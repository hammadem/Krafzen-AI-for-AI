import { act, renderHook, waitFor } from "@testing-library/react";
import { useFetchProjects } from "@/hooks/useFetchProjects";

const state = vi.hoisted(() => ({
    user: {userId: "a", access_token: "token-a"} as User | null,
    getAllProjects: vi.fn(),
}));
vi.mock("@/context/AuthContext", () => ({ useAuth: () => ({user: state.user}) }));
vi.mock("@/lib/api/api", () => ({ getAllProjects: state.getAllProjects }));

beforeEach(() => {
    state.user = {userId: "a", access_token: "token-a"} as User;
    state.getAllProjects.mockReset();
});

describe("project catalog isolation", () => {
    it("never shows the previous account's projects while the next request is pending", async () => {
        state.getAllProjects.mockResolvedValueOnce({ok: true, data: [{id: "private-a"}]});
        let finish: (value: unknown) => void = () => {};
        state.getAllProjects.mockImplementationOnce(() => new Promise(resolve => {finish = resolve;}));
        const {result, rerender} = renderHook(() => useFetchProjects());
        await waitFor(() => expect(result.current.projects[0]?.id).toBe("private-a"));
        state.user = {userId: "b", access_token: "token-b"} as User;
        rerender();
        expect(result.current.projects).toEqual([]);
        expect(result.current.status).toBe("inprogress");
        await waitFor(() => expect(state.getAllProjects).toHaveBeenCalledTimes(2));
        await act(async () => finish({ok: true, data: [{id: "private-b"}]}));
        await waitFor(() => expect(result.current.projects[0]?.id).toBe("private-b"));
    });
    it("reports a thrown API failure instead of remaining in loading state", async () => {
        state.getAllProjects.mockRejectedValueOnce(new Error("Network failure"));
        const {result} = renderHook(() => useFetchProjects());
        await waitFor(() => expect(result.current.status).toBe("error"));
        expect(result.current.projects).toEqual([]);
        expect(result.current.apiError?.message).toMatch(/retry/i);
    });
});
