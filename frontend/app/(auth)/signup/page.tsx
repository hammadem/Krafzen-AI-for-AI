import AuthSkeleton from "../_components/AuthSkeleton";
import SignUp from "../_components/SignUp";
// import ForgotPassword from "../_components/ForgotPassword";
// import EnterOtp from "../_components/EnterOtp";
// import SetNewPassword from "../_components/SetNewPassword";

export default function LoginPage() {
  return (
    <div>
      <AuthSkeleton AuthType={SignUp}/>
    </div>
  );
}

