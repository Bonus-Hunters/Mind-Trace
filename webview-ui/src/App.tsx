import "./App.css";
import MainScreen from "./components/Views/MainScreen.tsx";
import LoginScreen from "./components/Views/LoginScreen.tsx";
import { useState } from "react";
import { OTPVerificationModal } from "./components/OTPVerificationModal.tsx";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [pendingEmail, setPendingEmail] = useState("");

  const handleLogin = (email: string, password: string) => {
    // For demo purposes, accept any valid email/password
    console.log("Login attempt:", { email, password });
    setIsLoggedIn(true);
  };
  // for OTP
  //   const handleLogin = (email: string, password: string) => {
  //   // Store email and show OTP modal
  //   console.log('Login attempt:', { email, password });
  //   setPendingEmail(email);
  //   setShowOTPModal(true);
  // };
  const handleOTPVerify = (otp: string) => {
    // For demo purposes, accept any 6-digit OTP
    console.log("OTP verified:", otp);
    setShowOTPModal(false);
    setIsLoggedIn(true);
    setPendingEmail("");
  };

  const handleOTPClose = () => {
    // Close OTP modal and return to login
    setShowOTPModal(false);
    setPendingEmail("");
  };

  if (!isLoggedIn) {
    return (
      <>
        <LoginScreen onLogin={handleLogin} />
        {/* {showOTPModal && pendingEmail && (
          <OTPVerificationModal
            email={pendingEmail}
            onVerify={handleOTPVerify}
            onClose={handleOTPClose}
          />
        )} */}
      </>
    );
  }
  return <MainScreen />;
}

export default App;
