import * as vscode from "vscode";
import axios from "axios";
import { get_folder_curr_name } from "./helpers";

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

// fetch the list of project names for the current user's company
export async function get_projects(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
) {
  try {
    const email = context.globalState.get<string>("userEmail");
    const response = await axios.get(`http://127.0.0.1:8000/projects`, {
      headers: { email },
    });
    panel.postMessage({
      command: "projects_data",
      data: response.data,
    });
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    panel.postMessage({
      command: "projects_error",
      data: { error: serverMessage },
    });
    vscode.window.showErrorMessage(`Failed to load projects: ${serverMessage}`);
  }
}

// fetch the cached list of meetings (with chunks) for the current user
export async function get_meetings(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
) {
  try {
    const email = context.globalState.get<string>("userEmail");
    const response = await axios.get(`http://127.0.0.1:8000/meetings`, {
      headers: { email },
    });
      console.log(response.data)
    panel.postMessage({
      command: "meetings_data",
      data: response.data,
    });
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    panel.postMessage({
      command: "meetings_error",
      data: { error: serverMessage },
    });
    vscode.window.showErrorMessage(`Failed to load meetings: ${serverMessage}`);
  }
}

// create a new project for the current user's company
export async function save_project(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
  data?: any,
) {
  try {
    const email = context.globalState.get<string>("userEmail");
    const project_data = {
      email,
      projectName: data.projectName,
      creationDate: data.creationDate,
    };
    const response = await axios.post(
      `http://127.0.0.1:8000/create_project`,
      project_data,
    );
    vscode.window.showInformationMessage(`${response.data.message}`);
    // let the webview know so it can refresh project dropdowns
    panel.postMessage({ command: "project_created", data: response.data });
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    vscode.window.showErrorMessage(`Backend Error: ${serverMessage}`);
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

// Save a quick code annotation captured from the editor right-click menu.
export async function save_quick_note(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
  data?: any,
) {
  const note_data = {
    note_text: data.noteContent,
    project_name: get_folder_curr_name(),
    type: "code-annotation",
    tags: data.metadata, // comma-separated, optional
    function: data.functionName,
    file_name: data.fileName,
    line_number: data.lineNumber,
  };
  try {
    const email = context.globalState.get<string>("userEmail");
    await axios.post(`http://127.0.0.1:8000/notes/save_note`, note_data, {
      headers: { email },
    });
    vscode.window.showInformationMessage("Note saved");
    panel.postMessage({ command: "quickNoteSaved" });
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    vscode.window.showErrorMessage(`Backend Error: ${serverMessage}`);
    panel.postMessage({
      command: "quickNoteError",
      data: { error: serverMessage },
    });
  }
}
