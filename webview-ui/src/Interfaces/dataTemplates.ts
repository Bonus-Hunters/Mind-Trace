export interface MeetingData {
  type: string;
  title: string;
  meetingDate: string;
  tags: string | null;
  language: string;
  // audioFileForm: FormData | null;
}

export interface FeatureNoteData {
  type: string;
  title: string;
  description: string;
  tags: string | null;
}

export interface FileNoteData {
  type: string;
  title: string;
  filePath: string;
  description: string;
  tags: string | null;
}

export interface FunctionNoteData {
  type: string;
  title: string;
  description: string;
  filePath: string | null;
  functionName: string | null;
  lineNumber: string | null;
  tags: string | null;
}
