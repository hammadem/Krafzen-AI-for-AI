import { JSX, useEffect, useRef } from "react"
import Autoplay from "embla-carousel-autoplay"
import { Carousel } from "@/components/ui/carousel"

export default function RotateCarousel({ children }: { children: JSX.Element }) {
    const carouselRef = useRef<HTMLDivElement | null>(null)

    const autoplay = useRef(
        Autoplay({
            delay: 0,
            stopOnInteraction: false,
            stopOnMouseEnter: false,
        })
    )

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    autoplay.current.play()
                } else {
                    autoplay.current.stop()
                }
            },
            { threshold: 0.5 } // 50% visible
        )

        if (carouselRef.current) {
            observer.observe(carouselRef.current)
        }

        return () => observer.disconnect()
    }, [])

    return (
        <div ref={carouselRef}>
            <Carousel
                opts={{ loop: true, duration: 3000 }}
                plugins={[autoplay.current]}
                className="w-full"
            >
                {children}
            </Carousel>
        </div>
    )
}
