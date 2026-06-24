import * as vscode from "vscode";
import axios from "axios";

// OTP storage (in production, use secure backend storage)
export interface OTPData {
  otp: string;
  email: string;
  expiresAt: number;
  attempts: number;
}
export const otpStore: Map<string, OTPData> = new Map();

function generateVerificationId(): string {
  return Math.random().toString(36).substring(2, 15);
}

function isOTPExpired(expiresAt: number): boolean {
  return Date.now() > expiresAt;
}

// Send OTP to user email
export async function _sendOTP(panel: vscode.Webview, data?: any) {
  try {
    const { email, password, name } = data;

    console.log("VSC: sending OTP", email, password);
    // Validate backend credentials first
    const response = await axios.post(`http://127.0.0.1:8000/auth/send_otp`, {
      email: email,
      password: password,
      name: name,
    });

    if (response.status === 200) {
      const verificationId = generateVerificationId();

      const expiresAt = Date.now() + 10 * 60 * 1000; // 10 minutes
      const otp = response.data.otp;
      otpStore.set(verificationId, {
        otp,
        email,
        expiresAt,
        attempts: 0,
      });
      vscode.window.showInformationMessage(`OTP sent: ${otp}`);
      // Send OTP to user email (backend handles this)
      panel.postMessage({
        command: "otp-sent-success",
        data: {
          email,
          verificationId,
          message: `OTP sent to ${email}`,
        },
      });

      vscode.window.showInformationMessage(`OTP sent to ${email}`);
    }
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    panel.postMessage({
      command: "otp-error",
      data: { error: serverMessage },
    });
    vscode.window.showErrorMessage(`Failed to send OTP: ${serverMessage}`);
  }
}

// Verify OTP and add user to database
export async function _verifyOTP(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
  data?: any,
) {
  try {
    const { email, name, password, otp, verificationId } = data;

    // Check if verification ID exists
    const storedOTPData = otpStore.get(verificationId);
    if (!storedOTPData) {
      throw new Error("Invalid verification session");
    }

    // Check if OTP is expired
    if (isOTPExpired(storedOTPData.expiresAt)) {
      otpStore.delete(verificationId);
      throw new Error("OTP has expired. Please request a new one.");
    }

    // Check if OTP matches
    if (storedOTPData.otp !== otp) {
      console.log("VSC: otp = ", otp);
      console.log("VSC: Stored otp = ", storedOTPData.otp);
      storedOTPData.attempts++;
      if (storedOTPData.attempts >= 5) {
        otpStore.delete(verificationId);
        throw new Error("Too many failed attempts. Please request a new OTP.");
      }
      throw new Error("Invalid OTP. Please try again.");
    }

    // OTP verified successfully - add user to database
    const response = await axios.post(
      `http://127.0.0.1:8000/auth/register_user`,
      {
        email: email,
        password: password,
        name: name,
      },
    );

    if (response.status === 200) {
      // Store user authentication info
      await context.globalState.update("userEmail", email);
      // Store a dummy token (in production, use backend token)
      await context.secrets.store("userAuthToken", `token_${Date.now()}`);

      // Clear the OTP data
      otpStore.delete(verificationId);

      // Send success message to React
      panel.postMessage({
        command: "login-success",
        data: { email, message: "Login successful!" },
      });
      vscode.window.showInformationMessage(`Welcome ${name}!`);
    } else if (
      response.status === 500 &&
      response.data.error === "Wrong Password"
    ) {
      panel.postMessage({
        command: "wrong password",
        data: { error: "Wrong password" },
      });
    }
  } catch (error: any) {
    const serverMessage =
      error.response?.data?.error || error.message || "Verification failed";
    panel.postMessage({
      command: "otp-error",
      data: { error: serverMessage },
    });
    vscode.window.showErrorMessage(`Verification Error: ${serverMessage}`);
  }
}

// Resend OTP
export async function _resendOTP(panel: vscode.Webview, data?: any) {
  try {
    const { email } = data;

    // In production, you would generate a new OTP and send it
    // For now, just confirm the resend request
    const response = await axios.post(`http://127.0.0.1:8000/resend_otp`, {
      email,
    });

    if (response.status === 200) {
      vscode.window.showInformationMessage(
        `New OTP sent to ${email}. Check your email.`,
      );
    }
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    panel.postMessage({
      command: "otp-error",
      data: { error: serverMessage },
    });
  vscode.window.showErrorMessage(`Resend failed: ${serverMessage}`);
  }
}

type Authentication_data = {
  isAuthenticated: boolean;
  email: string | undefined;
};
export async function _check_authentication(context: vscode.ExtensionContext) {
  const userEmail = context.globalState.get<string>("userEmail");
  const userToken = await context.secrets.get("userAuthToken");
  const data: Authentication_data = {
    isAuthenticated: !!(userEmail && userToken),
    email: userEmail,
  };
  return data;
}

export async function valid_user(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
) {
  const data = await _check_authentication(context);
  panel.postMessage({
    command: "auth-status",
    data: { isLoggedIn: data.isAuthenticated, email: data.email },
  });
}
