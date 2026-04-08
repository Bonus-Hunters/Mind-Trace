import React, { useEffect } from "react";
import { useState } from "react";
import { StickyNote, Mail, Lock, LogIn, UserRound } from "lucide-react";

interface LoginScreenProps {
  onLogin: (name: string, email: string, password: string) => void;
  name: string;
  setName: any;
  password: string;
  setPassword: any;
  setLoginLoading: any;
  isLoginLoading: boolean;
}

const LoginScreen = ({
  onLogin,
  name,
  setName,
  password,
  setPassword,
  setLoginLoading,
  isLoginLoading,
}: LoginScreenProps) => {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const companyDomain = "@company_domain.com";

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const message = event.data;
      if (message.command === "otp-error") {
        setLoginLoading(false);
      } else if (message.command === "wrong password") {
        setLoginLoading(false);
        setError("Wrong password. Please try again.");
      }
    };
    window.addEventListener("message", handler);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name || name.length === 0) {
      setError("Please enter your name");
      return;
    }

    if (!email || email.length === 0) {
      setError("Please enter your email");
      return;
    }

    if (!email.includes("@")) {
      setError(`Email must have a domain`);
      return;
    }

    if (!password || password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoginLoading(true);
    // Call the onLogin callback which will trigger OTP sending
    onLogin(name, email, password);
  };
  const displayEmail = email.includes("@") ? email : email;

  return (
    <div className="h-screen flex items-center justify-center bg-[#1e1e1e]">
      <div className="w-full max-w-md px-8">
        {/* Logo and Title */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-3 mb-2">
            <StickyNote className="w-8 h-8 text-[#4ec9b0]" />
            <h1 className="text-2xl text-[#ffffff] font-mono">Mind Trace</h1>
          </div>
          <p className="text-xs text-[#6a6a6a] font-mono">
            Easy Enviroment for Developers
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-[#252526] border border-[#3e3e42] rounded-lg p-6 space-y-4">
            {/* Email Field */}
            {/* Name Field */}
            <div>
              <label className="block text-xs text-[#cccccc] mb-2 font-mono">
                Full Name *
              </label>
              <div className="relative">
                <UserRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6a6a6a]" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your full name"
                  className="w-full pl-10 pr-24 py-2.5 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-[#cccccc] mb-2 font-mono">
                Email Address *
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6a6a6a]" />
                <input
                  type="text"
                  value={displayEmail}
                  onChange={(e) => {
                    setEmail(e.target.value);
                  }}
                  placeholder={companyDomain}
                  className="w-full pl-10 pr-24 py-2.5 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-xs text-[#cccccc] mb-2 font-mono">
                Password *
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6a6a6a]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-10 pr-3 py-2.5 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
                />
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="px-3 py-2 bg-[#5a1d1d] border border-[#be1100] rounded">
                <p className="text-xs text-[#f48771] font-mono">{error}</p>
              </div>
            )}

            {/* Login Button */}
            <button
              type="submit"
              disabled={isLoginLoading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-xs bg-[#0e639c] hover:bg-[#1177bb] text-[#ffffff] rounded transition-colors font-mono disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <LogIn className="w-4 h-4" />
              {isLoginLoading ? "Sending OTP..." : "Sign In"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginScreen;
