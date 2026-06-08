import * as vscode from "vscode";
import axios from "axios";

export async function handleFileSelection(panel: vscode.Webview) {
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
export async function closeAddNoteModal(panel: vscode.Webview, data?: any) {
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

export async function process_meeting(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
  data?: any,
) {
  try {
    const userEmail = context.globalState.get<string>("userEmail");

    const meeting_data = {
      filename: data.audioFile.filename,
      tags: data.tags,
      title: data.title,
      language: data.language,
      date: data.meetingDate,
      projectName: data.projectName,
      email: userEmail,
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

export async function save_note(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
  data?: any,
) {
  // if data is string -> "" === null values for now [should change later when states are handled]
  const note_data = {
    note_text: data.description,
    project_name: data.projectName,
    type: data.noteCategory,
    tags: data.tags,
    function: data.functionName,
    file_name: data.filePath,
    module: data.moduleName,
    line_number: parseInt(data.lineNumber, 10),
    title: data.title,
  };
  try {
    const email = context.globalState.get<string>("userEmail");
    console.log(`IN::: ${email}`);

    const response = await axios.post(
      `http://127.0.0.1:8000/notes/save_note`,
      note_data,
      {
        headers: { email },
      },
    );
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    vscode.window.showErrorMessage(`Backend Error: ${serverMessage}`);
  }
}
