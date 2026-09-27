---
name: Chat model selection
description: Lightweight local model choice and decoding behavior for this chatbot.
---

Use the instruction-tuned SmolLM2 135M model with its chat template and deterministic decoding for this app. The smaller Flan-T5 setup was prone to short generic greetings and incomplete answers under sampling.

**Why:** The chatbot needs useful varied responses on Replit CPU without adding a hosted API dependency or a large model.

**How to apply:** Preserve the chat-template prompt, include recent turns, and prefer deterministic generation when diagnosing repeated or unstable replies.