import Image from "next/image";
import { Button } from "./button";

export default function PricingDiv({ price, index }: { price: PricingDetails; index: number }) {
    // Define hover colors based on index
    const colors = [
        "shadow-[0px_4px_60px_rgba(34,197,94,0.5)] hover:shadow-[0px_4px_60px_rgba(34,197,94,0.8)] ", // green
        "shadow-[0px_4px_60px_rgba(59,130,246,0.5)] hover:shadow-[0px_4px_60px_rgba(59,130,246,0.8)]", // blue
        "shadow-[0px_4px_60px_rgba(249,115,22,0.5)] hover:shadow-[0px_4px_60px_rgba(249,115,22,0.8)] ", // orange
        "shadow-[0px_4px_60px_rgba(236,72,153,0.5)] hover:shadow-[0px_4px_60px_rgba(236,72,153,0.8)] ", // pink
    ];

    const colorClass = colors[index % colors.length]; // cycle safely

    return (
        <span
            className={`mt-10 bg-black border border-transparent ${colorClass} font-black 
      flex flex-col items-center justify-between py-6 rounded-[15px] 
      transition-all duration-500 ease-in-out hover:scale-102`}
        >
            <span className="mb-20 flex flex-col h-[80%] justify-between items-center">
                <span className="mb-20 flex flex-col items-center text-white">
                    <h1 className="text-[3vh] font-semibold">{price.type}</h1>
                    <h1 className="text-[6vh] font-semibold">{price.price}</h1>
                </span>

                <span className="px-2 sm:px-4 md:px-6 text-[2vh] font-normal text-white flex h-[100%] flex-col justify-evenly items-start">
                    {price.features.map((feature, i) => (
                        <span className="flex items-start" key={i + price.price}>
                            <Image
                                src="/pricing/tick.png"
                                width={20}
                                height={20}
                                alt="Tick Image"
                                className="w-auto h-auto my-2"
                            />
                            <p className="mx-2 my-2">{feature}</p>
                        </span>
                    ))}
                </span>
            </span>

            <Button
                variant="secondary"
                className="cursor-pointer rounded-full my-2 w-[80%] transition-transform duration-300 ease-in-out hover:scale-105 bg-green-400 hover:bg-green-400"
            >
                Start Free
            </Button>
        </span>
    );
}
