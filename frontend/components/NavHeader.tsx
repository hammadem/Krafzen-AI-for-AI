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

            <div className="w-full h-30 z-9999" style={style}>

                <div className="w-[50%] flex flex-col items-center justify-center">
                    <h1 className="text-white text-[6vh] font-semibold mt-3">{currentNav}</h1>

                    <span className="flex items-center justify-center">
                        <Link className="text-white cursor-pointer font-semibold" href="/" aria-label="Home Link">Home</Link>
                        <Image
                            src="/navheader/Vector.png"
                            height={5}
                            width={5}
                            alt="Vector Image Navheader"
                            className="mx-3"
                        />
                        <p className="text-white font-semibold">{currentNav}</p>
                    </span>
                </div>

            </div>
        </>
    )
}