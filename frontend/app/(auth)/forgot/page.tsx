import AuthSkeleton from "../_components/AuthSkeleton";
import ForgotPassword from "../_components/ForgotPassword";
// import EnterOtp from "../_components/EnterOtp";
// import SetNewPassword from "../_components/SetNewPassword";

export default function LoginPage() {
    return (
        <div>
            <AuthSkeleton AuthType={ForgotPassword} />
        </div>
    );
}

