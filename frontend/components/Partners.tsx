import Image from "next/image";

export default function Partners() {
    return (
        <div className="z-9999 bg-black flex flex-col sm:flex-row w-full items-center justify-evenly sm:justify-around">
            <span
                className="sm:h-40 h-10"
            ></span>

            <p className="text-white text-[3vh]">Trusted by</p>
            <span
                className="sm:h-0 h-10"
            ></span>
            <div className="relative w-[80%] md:w-[70%] lg:[80%] h-20 sm:h-15">
                <Image
                    src="/partners/partner.png"
                    alt="Proof Partners Image"
                    fill
                    className="sm:object-fit object-fit"
                    loading="eager"
                />
            </div>
        </div>
    );
}