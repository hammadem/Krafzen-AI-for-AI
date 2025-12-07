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
            <div className="relative w-[80%] md:w-[70%] lg:[80%] h-20 sm:h-15 hidden sm:block">
                <Image
                    src="/partners/partner.png"
                    alt="Proof Partners Image"
                    fill
                    className="sm:object-fit object-fit"
                    loading="eager"
                />
            </div>

            <div className="sm:hidden block">
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
                            <Image
                                src="/partners/3.png"
                                alt="Partner 1"
                                width={300}
                                height={300}
                                className="mx-auto"
                            />
                        </CarouselItem>

                        <CarouselItem>
                            <Image
                                src="/partners/2.png"
                                alt="Partner 2"
                                width={300}
                                height={300}
                                className="mx-auto"

                            />
                        </CarouselItem>

                        <CarouselItem>
                            <Image
                                src="/partners/1.png"
                                alt="Partner 3"
                                width={300}
                                height={300}
                                className="mx-auto"

                            />
                        </CarouselItem>

                        <CarouselItem>
                            <Image
                                src="/partners/4.png"
                                alt="Partner 4"
                                width={300}
                                height={300}
                                className="mx-auto"

                            />
                        </CarouselItem>

                    </CarouselContent>
                </Carousel>
            </div>
        </div >
    );
}