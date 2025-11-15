import Image from "next/image";
import { Button } from "./ui/button";

export default function ContactCTA() {
    return (
            <div className="relative w-full font-semibold bg-black flex flex-col h-[50vh] py-8 items-center text-white text-[4vh]">
                <span className="flex flex-col h-[100%] items-center w-full justify-evenly">
                    <span className="hidden sm:flex w-full flex-col items-center justify-center">
                        <h1>Ready to design faster?</h1>
                        <h1>Get started today</h1>
                    </span>

                    <span className="w-full flex flex-col items-center justify-center sm:hidden">
                        <h1>Ready to</h1>
                        <h1>design faster?</h1>
                        <h1>Get started</h1>
                        <h1>today</h1>
                    </span>

                    <Button
                        variant="secondary"
                        className="rounded-full z-999 cursor-pointer hover:bg-green-400 bg-green-400"
                    >Book an appointment</Button>
                </span>

                <Image
                    src="/contact/tilt.png"
                    width={600}
                    height={600}
                    alt="Tilted Image"
                    className="absolute right-0 bottom-0 hidden md:block"
                />
        </div>
    );
}