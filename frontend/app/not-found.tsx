import Link from "next/link";

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center h-screen bg-[#0a0a0a] text-white">
            <h1 className="text-6xl font-bold">404</h1>
            <p className="mt-3 text-gray-400">We can&apos;t find what you&apos;re looking for.</p>

            <Link
                aria-label="Link to homepage"
                href="/"
                className="mt-5 px-5 py-2 bg-white text-black rounded-lg hover:bg-gray-200 transition"
            >
                Go Home
            </Link>
        </div>
    );
}
