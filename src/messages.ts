import * as vscode from "vscode";
import axios from "axios";
import { get_folder_curr_name } from "./Messages/helpers";
import {
  change_LLM,
  get_local_Ollama_LLMs,
  send_query_to_llm,
} from "./Messages/llm_messages";
import {
  _resendOTP,
  _sendOTP,
  valid_user,
  _verifyOTP,
} from "./Messages/authentication_messages";
import {
  closeAddNoteModal,
  handleFileSelection,
  process_meeting,
  save_note,
} from "./Messages/saving_data_messages";

// send search query to backend and return results
async function _send_search_query(panel: vscode.Webview, data: any) {
  try {
    const response = await axios.post(`http://127.0.0.1:8000/llms/search`, {
      query: data?.query ?? "",
      projectName: get_folder_curr_name(),
    });
    panel.postMessage({
      command: "search_results",
      data: response.data.results,
    });
  } catch (error: any) {
    const serverMessage = error.response?.data?.error || error.message;
    panel.postMessage({
      command: "search_error",
      data: { error: serverMessage },
    });
    vscode.window.showErrorMessage(`Search Error: ${serverMessage}`);
  }
}

export function handleReceivedMessages(
  panel: vscode.Webview,
  context: vscode.ExtensionContext,
) {
  panel.onDidReceiveMessage(
    (message: any) => {
      switch (message.command) {
        case "saveNote":
          switch (message.data.noteType) {
            case "note":
              // TODO: handle saving a note
              save_note(panel, context, message.data);
              return;
            case "meeting":
              process_meeting(panel, context, message.data);
              return;
          }
          return;
        case "selectAudioFile":
          handleFileSelection(panel);
          return;
        case "closeAddNoteModal":
          closeAddNoteModal(panel, message.data);
          return;
        case "react_ready":
          valid_user(panel, context);
          return;
        case "sendOTP":
          _sendOTP(panel, message.data);
          return;
        case "verifyOTP":
          _verifyOTP(panel, context, message.data);
          return;
        case "resendOTP":
          _resendOTP(panel, message.data);
          return;
        case "getOllamaModels":
          get_local_Ollama_LLMs(panel, message.data);
          return;
        case "changeLLM":
          change_LLM(panel, message.data);
          return;
        case "send_query_to_llm":
          send_query_to_llm(panel, message.data);
          return;
        case "close_panel":
          vscode.commands.executeCommand("workbench.action.closeAuxiliaryBar");
          return;
        case "send_search_query":
          _send_search_query(panel, message.data);
          return;
      }
    },
    undefined,
    context.subscriptions,
  );
}
