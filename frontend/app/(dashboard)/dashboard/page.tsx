"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Dashboard() {
    const router = useRouter();

    useEffect(() => {
        router.push("/dashboard/id");

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return null;
}
