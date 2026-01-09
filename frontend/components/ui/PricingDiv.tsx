"use client";
import { Check } from "lucide-react";
import Link from "next/link";
import { Button } from "../ui/button";

export default function PricingDiv({
  price,
  index,
  monthly,
}: {
  price: PricingDetails;
  index: number;
  monthly: boolean;
}) {
  const glowEffects = [
    "group-hover:shadow-[0_0_40px_-10px_rgba(34,197,94,0.6)] border-zinc-800 hover:border-green-500/50",
    "group-hover:shadow-[0_0_40px_-10px_rgba(59,130,246,0.6)] border-zinc-800 hover:border-blue-500/50",
    "group-hover:shadow-[0_0_40px_-10px_rgba(234,179,8,0.6)] border-zinc-800 hover:border-yellow-500/50",
    "group-hover:shadow-[0_0_40px_-10px_rgba(236,72,153,0.6)] border-zinc-800 hover:border-pink-500/50",
  ];

  const bgColors = [
    "bg-green-500/5 hover:bg-green-500/10",
    "bg-blue-500/5 hover:bg-blue-500/10",
    "bg-yellow-500/5 hover:bg-yellow-500/10",
    "bg-pink-500/5 hover:bg-pink-500/10",
  ];

  const glowClass = glowEffects[index % glowEffects.length];
  const bgClass = bgColors[index % bgColors.length];

  return (
    <div
      className={`relative group flex flex-col ${bgClass} backdrop-blur-sm border ${glowClass} rounded-2xl p-6 md:p-8 transition-all duration-500 hover:-translate-y-2`}
    >
      <div className="absolute inset-x-4 top-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent" />

      <div className="mb-6 space-y-2">
        <h3 className="text-xl font-medium text-gray-300">
          {price.type}
        </h3>

        <div className="flex items-end gap-2 whitespace-nowrap min-h-[56px]">
          <span className="text-4xl md:text-5xl font-bold text-white tracking-tight">
            {price.price}
          </span>

          {!price.price.includes("Custom") && (
            <span className="text-gray-500 text-sm mb-1">
              {monthly ? "/month" : "/year"}
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 space-y-4 mb-8">
        {price.features.map((feature, i) => (
          <div key={i} className="flex items-start gap-3">
            <Check
              size={18}
              strokeWidth={2}
              className="mt-1 text-white rounded-full border border-white/20 p-0.5"
            />
            <span className="text-sm text-gray-400 font-light leading-relaxed">
              {feature}
            </span>
          </div>
        ))}
      </div>

      <Button
        variant="secondary"
        asChild
        className="w-full rounded-full h-12 text-black font-bold text-base bg-green-400 hover:bg-green-500 transition-colors shadow-[0_0_15px_rgba(74,222,128,0.2)] hover:shadow-[0_0_25px_rgba(74,222,128,0.4)]"
      >
        {price.stripeLink ? (
          <a href={price.stripeLink} target="_blank" rel="noopener noreferrer">
            Get Started
          </a>
        ) : (
          <Link href="/support">Contact Us</Link>
        )}
      </Button>
    </div>
  );
}
