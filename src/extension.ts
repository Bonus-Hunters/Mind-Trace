// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from "vscode";
// This method is called
import * as path from "path";
import { getUri, handleReceivedMessage } from "./utilities";

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand(
    "Mind-Trace.helloWorld",
    () => {
      // 1. Create the panel
      const panel = vscode.window.createWebviewPanel(
        "mindtrace-ui",
        "Mind-Trace",
        vscode.ViewColumn.One,
        {
          enableScripts: true, // Required for React
          localResourceRoots: [
            vscode.Uri.file(
              path.join(context.extensionPath, "webview-ui/dist"),
            ),
          ],
        },
      );
      handleReceivedMessage(panel.webview, context);
      // 2. Generate the path to your React JS file
      const scriptUri = getUri(panel.webview, context.extensionUri, [
        "webview-ui",
        "dist",
        "assets",
        "index.js",
      ]);
      const styleUri = getUri(panel.webview, context.extensionUri, [
        "webview-ui",
        "dist",
        "assets",
        "index.css",
      ]);

      // 3. Set the HTML
      panel.webview.html = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${panel.webview.cspSource}; script-src ${panel.webview.cspSource};">
                <link rel="stylesheet" type="text/css" href="${styleUri}">
                <title>Mindtrace</title>
            </head>
            <body>
                <div id="root"></div>
                <script type="module" src="${scriptUri}"></script>
            </body>
            </html>
        `;
    },
  );

  context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
