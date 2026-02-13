import { Uri, Webview } from "vscode";
import * as vscode from "vscode";
import axios from "axios";

export function getUri(
  webview: Webview,
  extensionUri: Uri,
  pathList: string[],
) {
  return webview.asWebviewUri(Uri.joinPath(extensionUri, ...pathList));
}

async function _handleFileSelection(panel: vscode.Webview) {
  const fileUri = await vscode.window.showOpenDialog({
    canSelectMany: false,
    openLabel: "Select Audio",
    filters: {
      "Audio Files": ["wav", "mp3", "ogg", "m4a"],
    },
  });
  if (!fileUri || fileUri.length === 0) return;

  const uri = fileUri[0];
  try {
    // read data from hardisk
    const fileData = await vscode.workspace.fs.readFile(uri);
    const fileName = uri.path.split("/").pop();
    const formData = new FormData();
    const blob = new Blob([fileData], { type: "audio/wav" });
    formData.append("file", blob, fileName);

    const response = await axios.post(
      "http://127.0.0.1:8000/save_meeting_audio",
      formData,
    );

    // send results back to React
    panel.postMessage({
      command: "audioProcessingFinished",
      data: response.data,
    });
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to Upload File: ${error}`);
  }
}

// to delete audio file if it was saved in /Temp
async function _closeAddNoteModal(panel: vscode.Webview, data?: any) {
  if (data && data.audioFile) {
    try {
      const response = await axios.post(
        `http://127.0.0.1:8000/close_modal?filename=${data.audioFile.filename}`,
      );
    } catch (error) {
      vscode.window.showErrorMessage(
        `Failed to close modal properly: ${error}`,
      );
    }
  }
}

export function handleReceivedMessage(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
) {
  panel.onDidReceiveMessage(
    (message: any) => {
      switch (message.command) {
        case "saveNote":
          console.log("Saving note in extension.ts", message);
          switch (message.data.noteType) {
            case "function":
              return;
            case "file":
              return;
            case "feature":
              return;
            case "meeting":
              return;
          }
          return;
        case "selectAudioFile":
          _handleFileSelection(panel);
          return;
        case "closeAddNoteModal":
          _closeAddNoteModal(panel, message.data);
          return;
      }
    },
    undefined,
    context.subscriptions,
  );
}
