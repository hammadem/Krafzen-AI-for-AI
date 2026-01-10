"use client";
import { Check } from "lucide-react";
import { Button } from "../ui/button";
import { useState } from "react";
import StripePaymentModal from "../StripePaymentModal";

export default function PricingDiv({
  price,
  index,
  monthly,
}: {
  price: PricingDetails;
  index: number;
  monthly: boolean;
}) {
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  const handleGetStarted = () => {
    if (price.stripeLink) {
      setShowPaymentModal(true);
    } else {
      // For custom pricing (Enterprise Plus), redirect to support
      window.location.href = "/support";
    }
  };
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

  const colorThemes = ["green", "blue", "yellow", "pink"];
  const colorTheme = colorThemes[index % colorThemes.length];

  return (
    <div
      className={`relative group flex flex-col ${bgClass} backdrop-blur-sm border ${glowClass} rounded-2xl p-6 md:p-8 transition-all duration-500 hover:-translate-y-2`}
    >
      <div className="flex flex-col h-full">
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-white mb-2">{price.type}</h3>
          <div className="flex items-baseline mb-6">
            <span className="text-4xl font-bold text-white">{price.price}</span>
            {price.price !== "Custom" && (
              <span className="text-gray-400 ml-2">/month</span>
            )}
          </div>

          <div className="space-y-3 mb-8">
            {price.features.map((feature, i) => (
              <div key={i} className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
                <span className="text-sm text-gray-300">{feature}</span>
              </div>
            ))}
          </div>
        </div>

        <Button
          variant="secondary"
          onClick={handleGetStarted}
          className="w-full rounded-full h-12 text-black font-bold text-base bg-green-400 hover:bg-green-500 transition-colors shadow-[0_0_15px_rgba(74,222,128,0.2)] hover:shadow-[0_0_25px_rgba(74,222,128,0.4)]"
        >
          {price.stripeLink ? "Get Started" : "Contact Us"}
        </Button>

        {/* Stripe Checkout Modal */}
        {price.stripeLink && (
          <StripePaymentModal
            isOpen={showPaymentModal}
            onClose={() => setShowPaymentModal(false)}
            stripeCheckoutUrl={price.stripeLink}
            planName={price.type}
            amount={price.price}
            colorTheme={colorTheme}
          />
        )}
      </div>
    </div>
  );
}
