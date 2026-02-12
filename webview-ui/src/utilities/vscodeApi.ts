/**
 * A singleton utility to manage the communication with the VS Code Extension.
 */
class VSCodeWrapper {
  private readonly vscode: any;

  constructor() {
    // Check if the function exists (it only exists inside the VS Code Webview)
    if (typeof acquireVsCodeApi === "function") {
      this.vscode = acquireVsCodeApi();
    } else {
      // This allows you to test in a browser without crashing
      this.vscode = {
        postMessage: (message: any) =>
          console.log("Browser Mock: PostMessage", message),
        getState: () => ({}),
        setState: (state: any) => state,
      };
    }
  }

  public postMessage(command: string, data?: any) {
    this.vscode.postMessage({ command, data });
  }
}

export const vscode = new VSCodeWrapper();
