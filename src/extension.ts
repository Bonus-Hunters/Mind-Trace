// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
import * as path from "path";
import { Uri, Webview } from "vscode";
import { handleReceivedMessages } from "./messages";

// ── Helpers ──────────────────────────────────────────────────────────────────

function _get_folder_curr_name(): string | null {
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

function getUri(webview: Webview, extensionUri: Uri, pathList: string[]) {
  return webview.asWebviewUri(Uri.joinPath(extensionUri, ...pathList));
}

async function _logout(context: vscode.ExtensionContext) {
  await context.globalState.update("userEmail", undefined);
  await context.secrets.delete("userAuthToken");
}

function _buildHtml(webview: vscode.Webview, extensionUri: Uri): string {
  const scriptUri = getUri(webview, extensionUri, [
    "webview-ui",
    "dist",
    "assets",
    "index.js",
  ]);
  const styleUri = getUri(webview, extensionUri, [
    "webview-ui",
    "dist",
    "assets",
    "index.css",
  ]);

  return /* html */ `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta http-equiv="Content-Security-Policy"
            content="default-src 'none';
                     style-src ${webview.cspSource} 'unsafe-inline';
                     script-src ${webview.cspSource};">
      <link rel="stylesheet" type="text/css" href="${styleUri}">
      <title>Mind-Trace</title>
    </head>
    <body>
      <div id="root"></div>
      <script type="module" src="${scriptUri}"></script>
    </body>
    </html>`;
}

// ── Sidebar WebviewViewProvider ───────────────────────────────────────────────

class MindTraceSidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewId = "my-sidebar-view";

  private _view?: vscode.WebviewView;
  private _pendingQuickNote?: any;

  constructor(
    private readonly _extensionUri: Uri,
    private readonly _context: vscode.ExtensionContext,
  ) {}

  /** Called by VS Code when the sidebar view becomes visible. */
  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    _resolveContext: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken,
  ) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [
        Uri.joinPath(this._extensionUri, "webview-ui", "dist"),
      ],
    };

    webviewView.webview.html = _buildHtml(
      webviewView.webview,
      this._extensionUri,
    );

    handleReceivedMessages(webviewView.webview, this._context, this);
  }

  /** Programmatically show the sidebar panel. */
  public show() {
    if (this._view) {
      this._view.show(true); // true = preserve focus on editor
    }
  }

  /**
   * Reveal the sidebar and open the compact "Add Note" form pre-filled with
   * the given code context (function name, file, line).
   */
  public openAddNote(payload: any) {
    this._pendingQuickNote = payload;
    // Reveal the secondary sidebar (right panel) then focus our view.
    vscode.commands.executeCommand("workbench.action.focusAuxiliaryBar");
    vscode.commands.executeCommand("my-sidebar-view.focus");
    this.flushPendingQuickNote();
  }

  /**
   * Post any pending quick-note context to the webview. Called both right
   * after openAddNote (warm path: webview already mounted) and from the
   * "react_ready" handler (cold path: webview opening for the first time).
   */
  public flushPendingQuickNote() {
    if (this._view && this._pendingQuickNote) {
      this._view.webview.postMessage({
        command: "openQuickNote",
        data: this._pendingQuickNote,
      });
      this._pendingQuickNote = undefined;
    }
  }
}

// ── Extension entry ───────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext) {
  // Register the sidebar WebviewView provider
  const provider = new MindTraceSidebarProvider(context.extensionUri, context);
  const folderName = _get_folder_curr_name();
  vscode.window.showInformationMessage(
    folderName ? `Current folder: ${folderName}` : "No folder open",
  );

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      MindTraceSidebarProvider.viewId,
      provider,
      {
        // Keep the webview alive even when the panel is hidden (like Copilot)
        webviewOptions: { retainContextWhenHidden: true },
      },
    ),
  );

  // "Run Extension" command → reveal the Mind-Trace panel in the secondary sidebar (right side)
  const extension_run_command = vscode.commands.registerCommand(
    "Mind-Trace.runextension",
    () => {
      // Open the secondary sidebar (right panel) then focus our view
      vscode.commands.executeCommand("workbench.action.focusAuxiliaryBar");
      vscode.commands.executeCommand("my-sidebar-view.focus");
    },
  );

  const logout_command = vscode.commands.registerCommand(
    "Mind-Trace.logout",
    () => {
      _logout(context);
    },
  );

  // "Add Note" command → triggered from the editor right-click menu on a selection
  const add_note_command = vscode.commands.registerCommand(
    "Mind-Trace.addNote",
    () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("No active editor to add a note from.");
        return;
      }

      // The form lives in the logged-in webview — require auth first.
      const email = context.globalState.get<string>("userEmail");
      if (!email) {
        vscode.window.showInformationMessage("Log in to Mind-Trace first.");
        return;
      }

      const functionName = editor.document.getText(editor.selection).trim();
      const fileName = path.basename(editor.document.fileName);
      const lineNumber = editor.selection.start.line + 1;

      provider.openAddNote({ functionName, fileName, lineNumber });
    },
  );

  context.subscriptions.push(
    extension_run_command,
    logout_command,
    add_note_command,
  );
}

// This method is called when your extension is deactivated
export function deactivate() {}
