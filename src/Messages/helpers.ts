import * as vscode from "vscode";

export function get_folder_curr_name(): string | null {
  const activeEditor = vscode.window.activeTextEditor;
  if (activeEditor) {
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(
      activeEditor.document.uri,
    );
    if (workspaceFolder) {
      return workspaceFolder.name;
    }
  }
  return null;
}
