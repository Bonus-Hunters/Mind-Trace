import "./App.css";
import MainScreen from "./components/Views/MainScreen.tsx";
import LoginScreen from "./components/Views/LoginScreen.tsx";
import { useState, useEffect } from "react";
import { OTPVerificationModal } from "./components/OTPVerificationModal.tsx";
import { vscode } from "./utilities/vscodeApi.ts";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [pendingEmail, setPendingEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [otpVerificationId, setOtpVerificationId] = useState<string | null>(
    null,
  );
  const [isLoginLoading, setLoginLoading] = useState(false);

  useEffect(() => {
    // 1. Tell the extension we are ready to receive data
    vscode.postMessage("react_ready");

    // 2. Listen for messages from the extension
    const handler = (event: MessageEvent) => {
      const message = event.data;
      if (message.command === "auth-status") {
        setIsLoggedIn(message.data.isLoggedIn);
        if (message.data.email) setPendingEmail(message.data.email);
      } else if (message.command === "otp-sent-success") {
        // OTP was sent successfully, show verification modal
        setPendingEmail(message.data.email);
        setOtpVerificationId(message.data.verificationId);
        setShowOTPModal(true);
      } else if (message.command === "otp-error") {
      } else if (message.command === "login-success") {
        // User successfully logged in
        setShowOTPModal(false);
        setIsLoggedIn(true);
        setPendingEmail("");
        setOtpVerificationId(null);
      } else if (message.command === "otp-error") {
        console.error("OTP Error:", message.data.error);
      }
    };
    console.log("REACT: isLoggedIn= ", isLoggedIn);
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, []);

  const handleLogin = (name: string, email: string, password: string) => {
    // Send login request with OTP to the extension
    console.log("REACT: Login attempt:", { email, password });
    vscode.postMessage("sendOTP", {
      email: email,
      password: password,
      name: name,
    });
  };

  const handleOTPVerify = (otp: string) => {
    // Send OTP verification to the extension
    console.log("OTP verification attempt:", otp);
    vscode.postMessage("verifyOTP", {
      email: pendingEmail,
      name: name,
      password: password,
      otp: otp,
      verificationId: otpVerificationId,
    });
  };

  const handleOTPClose = () => {
    // Close OTP modal and return to login
    setLoginLoading(false);
    setShowOTPModal(false);
    setPendingEmail("");
    setOtpVerificationId(null);
  };

  if (!isLoggedIn) {
    return (
      <>
        <LoginScreen
          name={name}
          setName={setName}
          password={password}
          setPassword={setPassword}
          onLogin={handleLogin}
          setLoginLoading={setLoginLoading}
          isLoginLoading={isLoginLoading}
        />
        {showOTPModal && pendingEmail && (
          <OTPVerificationModal
            email={pendingEmail}
            onVerify={handleOTPVerify}
            onClose={handleOTPClose}
          />
        )}
      </>
    );
  }
  return <MainScreen />;
}

export default App;
