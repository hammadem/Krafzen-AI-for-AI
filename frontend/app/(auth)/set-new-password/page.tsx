import AuthSkeleton from "../_components/AuthSkeleton";
import SetNewPassword from "../_components/SetNewPassword";

export default function SetNewPasswordPage() {
  return (
    <div>
      <AuthSkeleton AuthType={SetNewPassword} />
    </div>
  );
}
