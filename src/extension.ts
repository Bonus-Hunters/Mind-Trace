import * as vscode from "vscode";
import * as path from "path";

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand(
    "Mind-Trace.helloWorld",
    () => {
      const panel = vscode.window.createWebviewPanel(
        "mindtrace-ui",
        "Mind-Trace",
        vscode.ViewColumn.One,
        {
          enableScripts: true,
          localResourceRoots: [
            // Allow access to the entire dist folder
            vscode.Uri.file(
              path.join(context.extensionPath, "webview-ui", "dist"),
            ),
          ],
        },
      );

      // 1. Path to your compiled Tailwind CSS
      // Note: Check if your filename is 'index.css' or 'style.css' in dist/assets
      const styleUri = panel.webview.asWebviewUri(
        vscode.Uri.file(
          path.join(
            context.extensionPath,
            "webview-ui",
            "dist",
            "assets",
            "index.css",
          ),
        ),
      );

      // 2. Path to your React JS bundle
      const scriptUri = panel.webview.asWebviewUri(
        vscode.Uri.file(
          path.join(
            context.extensionPath,
            "webview-ui",
            "dist",
            "assets",
            "index.js",
          ),
        ),
      );

      // 3. Set the HTML with the CSS link and CSP
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

export function deactivate() {}
