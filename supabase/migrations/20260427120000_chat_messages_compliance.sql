-- Persist IRC screening snapshot on assistant chat rows (USA jurisdiction flows).
ALTER TABLE public.chat_messages
ADD COLUMN IF NOT EXISTS compliance JSONB DEFAULT NULL;

COMMENT ON COLUMN public.chat_messages.compliance IS 'USA IRC baseline screening JSON attached to assistant messages when computed';
