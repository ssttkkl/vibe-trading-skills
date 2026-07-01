# Session reply forwarding

When the user asks to forward the **latest / last / most recent** reply from a vibe-trading session to QQ or another channel:

1. Read the full session message list first: `GET /sessions/{session_id}/messages?limit=100`.
2. Select the **newest assistant message by order / created_at**.
3. Do **not** reuse:
   - the assistant reply from the current chat turn,
   - a compacted summary,
   - the first assistant message returned by a polling script.
4. If the user says the forwarded content is wrong, re-check the session stream before sending anything else.
5. Preserve markdown exactly when the user asks for markdown / verbatim relay.

This note exists because the user may append follow-up assistant replies inside the same session, and "last reply" refers to the newest assistant message in the session, not the previous turn in the current conversation.