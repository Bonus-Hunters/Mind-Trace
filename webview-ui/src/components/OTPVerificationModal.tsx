import { useState, useRef, useEffect } from "react";
import { X, Mail, ShieldCheck } from "lucide-react";
import { vscode } from "../utilities/vscodeApi";

interface OTPVerificationModalProps {
  email: string;
  onVerify: (otp: string) => void;
  onClose: () => void;
}

export function OTPVerificationModal({
  email,
  onVerify,
  onClose,
}: OTPVerificationModalProps) {
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // Focus first input on mount
    inputRefs.current[0]?.focus();
  }, []);

  const handleChange = (index: number, value: string) => {
    // Only allow numbers
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    setError("");

    // Move to next input if value entered
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    // Move to previous input on backspace if current is empty
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").trim();

    // Only process if it's 6 digits
    if (/^\d{6}$/.test(pastedData)) {
      const newOtp = pastedData.split("");
      setOtp(newOtp);
      inputRefs.current[5]?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const otpCode = otp.join("");

    if (otpCode.length !== 6) {
      setError("Please enter all 6 digits");
      return;
    }

    setIsLoading(true);
    setError("");
    onVerify(otpCode);
  };

  const handleResend = () => {
    setIsResending(true);
    setOtp(["", "", "", "", "", ""]);
    setError("");
    inputRefs.current[0]?.focus();
    // Send resend OTP request to the extension
    vscode.postMessage("resendOTP", { email: email });
    // Assume resend is successful - in production, wait for backend confirmation
    setTimeout(() => {
      setIsResending(false);
    }, 1000);
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#252526] border border-[#3e3e42] rounded shadow-2xl w-[500px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#3e3e42]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#4ec9b0]" />
            <h2 className="text-sm text-[#ffffff]">Verify Your Email</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#2a2d2e] rounded transition-colors"
          >
            <X className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Info Message */}
          <div className="flex items-start gap-3 px-3 py-2.5 bg-[#1e1e1e] border border-[#3e3e42] rounded">
            <Mail className="w-4 h-4 text-[#4ec9b0] flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs text-[#cccccc] font-mono">
                We've sent a verification code to:
              </p>
              <p className="text-xs text-[#4ec9b0] font-mono font-semibold">
                {email}
              </p>
            </div>
          </div>

          {/* OTP Input */}
          <div>
            <label className="block text-xs text-[#cccccc] mb-3 font-mono">
              Enter 6-Digit Code
            </label>
            <div className="flex gap-2 justify-center">
              {otp.map((digit, index) => (
                <input
                  key={index}
                  ref={(el) => {
                    inputRefs.current[index] = el;
                  }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  onPaste={index === 0 ? handlePaste : undefined}
                  className="w-12 h-12 bg-[#3c3c3c] border border-[#3e3e42] rounded text-center text-lg text-[#ffffff] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
                />
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="px-3 py-2 bg-[#5a1d1d] border border-[#be1100] rounded">
              <p className="text-xs text-[#f48771] font-mono">{error}</p>
            </div>
          )}

          {/* Resend Code */}
          <div className="text-center">
            <button
              type="button"
              disabled={isResending}
              onClick={handleResend}
              className="text-xs text-[#4ec9b0] hover:text-[#6ed4b5] transition-colors font-mono underline disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isResending ? "Resending..." : "Didn't receive the code? Resend"}
            </button>
          </div>

          {/* Verify Button */}
          <button
            type="submit"
            disabled={otp.join("").length !== 6 || isLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-xs bg-[#0e639c] hover:bg-[#1177bb] text-[#ffffff] rounded transition-colors font-mono disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ShieldCheck className="w-4 h-4" />
            {isLoading ? "Verifying..." : "Verify & Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
