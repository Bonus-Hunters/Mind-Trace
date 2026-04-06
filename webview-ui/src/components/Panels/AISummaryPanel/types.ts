export interface Source {
  noteId: string;
  title: string;
  filePath?: string;
  type: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: Source[];
}
