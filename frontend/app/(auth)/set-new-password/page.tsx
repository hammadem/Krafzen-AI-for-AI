import { Suspense } from "react";
import AuthSkeleton from "../_components/AuthSkeleton";
import SetNewPassword from "../_components/SetNewPassword";

export default function SetNewPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-white">Loading...</div>}>
      <AuthSkeleton AuthType={SetNewPassword} />
    </Suspense>
  );
}
