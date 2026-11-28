# AEC small language model experiment

Base: HuggingFaceTB/SmolLM2-135M-Instruct, Apache 2.0; checkpoint ee72e5415c002e8fc0566a191a07c0b2b708875a. Source: https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct . No remote model code or pickle weights loaded. Use the existing CC BY 4.0 buildingSMART IFC fixture corpus and retained per-source attribution. No customer content or copyrighted standards.

The bounded CPU LoRA experiment uses only reference extraction with the facts supplied in the prompt. It measures exact answers on held-out model families before and after adapter fitting. It records real loss values, source manifest and actual safetensors adapter. It is not fine-tuning a comprehensive design or engineering LLM, nor independent practitioner evaluation. The model is not enabled on Render: the 512 MiB backend is not a suitable inference host. No paid GPU requested. CI artifacts expire after 7 days.

Run only within an authorized compute allowance; no cloud compute purchase is authorized. Deploy only after additional licensed data, independent project-based evaluation, resource assessment, security review and professional acceptance. Never use generated numeric claims instead of parsed geometry or deterministic compliance rules.
