import Image from "next/image";
import Link from "next/link";

const style: React.CSSProperties = {
    backgroundImage: "url('/navheader/nav-image2.png')",
    backgroundRepeat: "no-repeat",
    backgroundSize: "cover",
    backgroundPosition: "center",
    borderTop: "1px solid white",
    borderBottom: "1px solid white",
};

export default function NavHeader({ currentNav }: { currentNav: string; }) {
    return (
        <>

            <div className="w-full h-[18vh] sm:h-[22vh] z-9999 flex items-center w-full" style={style}>

                <div className="flex flex-col mx-6 w-[80%] mx-auto">

                    <div className="flex flex-col items-start justify-center">
                        <h1 className="text-white text-[6vh] font-semibold">{currentNav}</h1>

                        <span className="flex items-center justify-start">
                            <Link className="text-white cursor-pointer font-semibold" href="/" aria-label="Home Link">Home</Link>
                            <Image
                                src="/navheader/Vector.png"
                                height={5}
                                width={5}
                                alt="Vector Image Navheader"
                                className="mx-3 translate-y-[2px]"
                            />
                            <p className="text-white font-semibold">{currentNav}</p>
                        </span>
                    </div>
                </div>

            </div>
        </>
    )
}