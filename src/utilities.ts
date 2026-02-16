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
    const response = await axios.post(
      `http://127.0.0.1:8000/save_meeting_audio`,
      {
        filePath: uri.fsPath,
      },
    );
    // send results back to React
    panel.postMessage({
      command: "audioProcessingFinished",
      data: response.data,
    });
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    vscode.window.showErrorMessage(`Backend Error: ${serverMessage}`);
  }
}

// to delete audio file if it was saved in /Temp
async function _closeAddNoteModal(panel: vscode.Webview, data?: any) {
  if (data && data.audioFile) {
    try {
      const response = await axios.post(`http://127.0.0.1:8000/close_modal`, {
        filePath: data.audioFile["filename"],
      });
      vscode.window.showInformationMessage(`${response.data.message}`);
    } catch (error) {
      vscode.window.showErrorMessage(
        `Failed to close modal properly: ${error}`,
      );
    }
  }
}

async function _process_meeting(panel: vscode.Webview, data?: any) {
  try {
    const meeting_data = {
      filename: data.audioFile.filename,
      tags: data.tags,
      title: data.title,
      language: data.language,
      date: data.meetingDate,
      projectName: data.projectName,
    };
    const response = await axios.post(
      `http://127.0.0.1:8000/process_meeting`,
      meeting_data,
    );
    vscode.window.showInformationMessage(`${response.data.message}`);
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    vscode.window.showErrorMessage(`Backend Error: ${serverMessage}`);
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
          switch (message.data.noteType) {
            case "function":
              return;
            case "file":
              return;
            case "feature":
              return;
            case "meeting":
              _process_meeting(panel, message.data);
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
