import { useEffect, useState } from "react";
import { Mic, Upload, Loader2, ShieldCheck } from "lucide-react";
import { vscode } from "../../utilities/vscodeApi";

interface VoiceEnrollmentScreenProps {
  onComplete: () => void;
}

/**
 * First-time onboarding shown to a newly registered user right after OTP
 * verification. The user must upload a voice recording of themselves
 * (WAV/MP3, at least 10 seconds) before the extension opens. The native file
 * dialog and backend validation are handled by the extension host via the
 * "enrollVoice" message.
 */
const VoiceEnrollmentScreen = ({ onComplete }: VoiceEnrollmentScreenProps) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const message = event.data;
      if (message.command === "voiceEnrollmentFinished") {
        setIsProcessing(false);
        setError("");
        onComplete();
      } else if (message.command === "voiceEnrollmentError") {
        setIsProcessing(false);
        setError(message.data?.error ?? "Something went wrong. Please try again.");
      }
    };
    window.addEventListener("message", handler);
    return () => window.removeEventListener("message", handler);
  }, [onComplete]);

  const handleUpload = () => {
    setError("");
    setIsProcessing(true);
    vscode.postMessage("enrollVoice");
  };

  return (
    <div className="h-screen flex items-center justify-center bg-[#1e1e1e]">
      <div className="w-full max-w-md px-8">
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Mic className="w-8 h-8 text-[#4ec9b0]" />
            <h1 className="text-2xl text-[#ffffff] font-mono">
              Set Up Your Voice
            </h1>
          </div>
          <p className="text-xs text-[#6a6a6a] font-mono text-center">
            One last step to finish setting up your profile
          </p>
        </div>

        <div className="bg-[#252526] border border-[#3e3e42] rounded-lg p-6 space-y-4">
          {/* Instructions */}
          <div className="flex items-start gap-3 px-3 py-2.5 bg-[#1e1e1e] border border-[#3e3e42] rounded">
            <ShieldCheck className="w-4 h-4 text-[#4ec9b0] flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs text-[#cccccc] font-mono">
                Upload a voice recording of yourself so Mind Trace can recognize
                you in meetings.
              </p>
              <p className="text-xs text-[#6a6a6a] font-mono">
                Formats: WAV or MP3 · at least 10 seconds.
              </p>
            </div>
          </div>

          {/* Upload button */}
          <button
            type="button"
            onClick={handleUpload}
            disabled={isProcessing}
            className="flex items-center justify-center gap-2 w-full px-3 py-3 bg-[#0e639c] hover:bg-[#1177bb] text-[#ffffff] rounded text-xs transition-colors font-mono disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing your voice sample…
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Browse Voice Sample
              </>
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="px-3 py-2 bg-[#5a1d1d] border border-[#be1100] rounded">
              <p className="text-xs text-[#f48771] font-mono">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceEnrollmentScreen;
