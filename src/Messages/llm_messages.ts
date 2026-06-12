import * as vscode from "vscode";
import axios from "axios";
import { get_folder_curr_name } from "./helpers";

// get ollama local llms
export async function get_local_Ollama_LLMs(panel: vscode.Webview, data?: any) {
  try {
    const response = await axios.get(
      `http://127.0.0.1:8000/llms/get_local_llms`,
    );
    panel.postMessage({
      command: "ollamaModels",
      data: response.data,
    });
    console.log("Local LLMs fetched successfully, response: ", response.data);
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    vscode.window.showErrorMessage(
      `Couldn't Retrieve Local LLMs: ${serverMessage}`,
    );
  }
}

// set seleted llm
export async function change_LLM(panel: vscode.Webview, data?: any) {
  const { llm } = data;
  try {
  } catch (error: any) {
    vscode.window.showErrorMessage(`Couldn't Change LLM: $errorMsg`);
  }
}

// send query msg to llm and get response
export async function send_query_to_llm(panel: vscode.Webview, data: any) {
  try {
    const response = await axios.post(`http://127.0.0.1:8000/llms/send_query`, {
      query: data?.query ?? "",
      projectName: get_folder_curr_name(),
    });
    panel.postMessage({
      command: "llm_response",
      data: response.data,
    });
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    panel.postMessage({
      command: "llm_error",
      data: { error: serverMessage },
    });
    vscode.window.showErrorMessage(`LLM Query Error: ${serverMessage}`);
  }
}
