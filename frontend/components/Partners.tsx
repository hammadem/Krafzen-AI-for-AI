import Image from "next/image";
import { Carousel, CarouselContent, CarouselItem } from "./ui/carousel";
import Autoplay from "embla-carousel-autoplay";

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

            <div className="relative w-[80%] md:w-[80%] lg:[80%] h-[20vh] hidden sm:block">
                <Image
                    src="/partners/partners.svg"
                    alt="Proof Partners Image"
                    fill
                    className="object-fit"
                    loading="eager"
                />
            </div>

            <div className="sm:hidden block w-full">
                <Carousel
                    opts={{ loop: true }}
                    plugins={[
                        Autoplay({
                            delay: 2000,
                            stopOnInteraction: false,
                            stopOnMouseEnter: false,
                        }),
                    ]}
                    className="w-full"
                >
                    <CarouselContent>
                        <CarouselItem>
                            <div className="h-[10vh] relative w-[80%] mx-auto">
                                <Image
                                    src="/partners/1.svg"
                                    alt="Partner 1"
                                    fill
                                    className="mx-auto object-fit"
                                />
                            </div>

                        </CarouselItem>

                        <CarouselItem>
                            <div className="h-[10vh] relative w-[80%] mx-auto">
                                <Image
                                    src="/partners/2.svg"
                                    alt="Partner 2"
                                    fill
                                    className="mx-auto object-fit"
                                />
                            </div>
                        </CarouselItem>

                        <CarouselItem>
                            <div className="h-[10vh] relative w-[80%] mx-auto">
                                <Image
                                    src="/partners/3.svg"
                                    alt="Partner 3"
                                    fill
                                    className="mx-auto object-fit"

                                />
                            </div>
                        </CarouselItem>

                        <CarouselItem>
                            <div className="h-[10vh] relative w-[80%] mx-auto">
                                <Image
                                    src="/partners/4.svg"
                                    alt="Partner 4"
                                    fill
                                    className="mx-auto object-fit"
                                />
                            </div>

                        </CarouselItem>

                    </CarouselContent>
                </Carousel>
            </div>
        </div >
    );
}