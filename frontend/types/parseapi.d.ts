type File_Type = "dxf" | "dwg" | "revit" | "step";

type GPT_PARSE_REQ = {
    text: string,
    file_type?: File_Type,
    additional_context?: string
}

type GPT_PARSE_TRANSCRIPTION_REQ = {
    transcription_text: string,
    file_type?: File_Type
    additional_context: string
}


type ParsedInstruction = {
    command: string
    parameters: Record<string, _any>,
    confidence: number
}

type GPT_PARSED_INSRUCTION_SUCCESS = {
    status: string,
    instructions: ParsedInstruction[],
    file_type: File_Type
    raw_gpt_response: string
    timestamp: string
}