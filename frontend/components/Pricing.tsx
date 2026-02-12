"use client";
import { useState } from "react";
import { Button } from "./ui/button";
import PricingDiv from "./ui/PricingDiv";
import StripePaymentModal from "./StripePaymentModal";
import { PricingPlans } from "@/lib/data";
import { useDashboard } from "@/context/DashboardContex";

const COLOR_THEMES = ["green", "blue", "yellow", "pink"] as const;
function planTypeToName(type: string): string {
  return type.toLowerCase().replace(/\s+/g, "_");
}

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
};

// some tests has beeen commentedd due to conflicts with reccent changes test file can be re-written

export default function Pricing() {
  const { monthly, setMonthly } = useDashboard();
  const [paymentModal, setPaymentModal] = useState<{
    open: boolean;
    planName: string;
    planDisplayName: string;
    amount: string;
    billingCycle: "monthly" | "annual";
    colorTheme: string;
  } | null>(null);

  const handleGetStarted = (price: PricingDetails, index: number, isMonthly: boolean) => {
    if (price.price === "Custom" || !price.stripeLink) return;
    setPaymentModal({
      open: true,
      planName: planTypeToName(price.type),
      planDisplayName: price.type,
      amount: price.price,
      billingCycle: isMonthly ? "monthly" : "annual",
      colorTheme: COLOR_THEMES[index % COLOR_THEMES.length],
    });
  };

  return (
    <section>
      <div className="bg-black w-full pb-20">
        <div className="w-full max-w-6xl mx-auto px-4 flex flex-col items-center gap-8">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              Pricing Plans
            </h2>
            <p className="text-gray-400">
              Choose the plan that works best for you.
            </p>
          </div>

          <div className="relative bg-zinc-900 border border-white/10 p-1 rounded-full flex w-fit mx-auto">
            <div
              className={classNames(
                "absolute z-10 top-1 bottom-1 left-1 bg-black rounded-full transition-transform duration-500 ease-out border border-white/10",
                monthly
                  ? "translate-x-0 w-[calc(50%-4px)]"
                  : "translate-x-[100%] w-[calc(50%-4px)]"
              )}
            />
            <Button
              onClick={() => setMonthly(true)}
              variant="ghost"
              className={classNames(
                "relative z-20 rounded-full w-32 hover:bg-transparent",
                monthly ? "text-white" : "text-gray-400 hover:text-black"
              )}
            >
              Monthly
            </Button>
            <Button
              onClick={() => setMonthly(false)}
              variant="ghost"
              className={classNames(
                "relative z-20 rounded-full w-32 hover:bg-transparent",
                !monthly ? "text-white" : "text-gray-400 hover:text-black"
              )}
            >
              Annual
            </Button>
          </div>

          <div className="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {(monthly ? PricingPlans.monthly : PricingPlans.annual).map(
              (price: PricingDetails, index: number) => (
                <PricingDiv
                  key={price.price}
                  price={price}
                  index={index}
                  monthly={monthly}
                  onGetStarted={handleGetStarted}
                />
              )
            )}
          </div>
        </div>
      </div>
      {paymentModal != null && (
        <StripePaymentModal
          isOpen={paymentModal.open}
          onClose={() => setPaymentModal(null)}
          planName={paymentModal.planName}
          planDisplayName={paymentModal.planDisplayName}
          amount={paymentModal.amount}
          billingCycle={paymentModal.billingCycle}
          colorTheme={paymentModal.colorTheme}
        />
      )}
    </section>
  );
}
