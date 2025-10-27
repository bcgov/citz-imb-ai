# MemGPT Comparison

One relevant paper that addresses a concern with handling growing context in a limited context window is the one on [MemGPT](https://arxiv.org/pdf/2310.08560).

While our use case in this example is more specific, it's worth comparing their approach to what we experimented with here.

## Full Chat History Approach

Our system maintains the complete chat history for each conversation, storing all user messages and assistant responses in their original form. Tool calls are not stored, but the current tool call is added to the model context.

Some benefits of this approach is that we can display this full chat history to users through the frontend of the application. It also means the model can reference what was said word for word. If there's a need for audit trails, this is necessary. For us, it's also easier to debug.

The downside is that as the chat history grows, more of the limited context window is being filled by the history. If you have a small model with a small context window, you might hit the cap very quickly. It also means you're paying more for each request, as input tokens are part of that cost calculation. There's also the system implications of more storage needed and larger payloads when sending data.

## MemGPT Approach

MemGPT uses a memory management system that summarizes older parts of conversations and discards the original messages to save context space. It maintains a "core memory" with key facts about the user and recent conversation history.

This has a major benefit of maintaining a maximum context size. As the chat continues, the summary of this chat is continuously updated to reflect the update before being supplied as context. This is a very scalable approach, especially when you know the chat will continue for an extended time or contain large exchanges. It ends up being cheaper to submit this chat history as context (fewer tokens) and faster (less context to process).

There are some drawbacks to this approach as well. The details of the conversation will be lost during summary. In some cases, the summaries may even contain incorrect interpretations of the chat. This can make it difficult to know what was actually said between the user and the assistant roles.

There's also an added cost to this approach. Rather than updating a summary occasionally, the summary must be updated after every exchange to ensure this new information is captured in context for the next prompt. A rapid chat between user and assistant could result in many additional calls to the AI model. Even a prompt every minute, not unlikely in a chat bot scenario, could mean performing 60 additional summaries every hour for just one user. If you're familiar with token costs, you might already know that the *output* tokens are more expensive than the *input* tokens, so we can deal with the costs of a bigger input context easier than the costs of more frequent generations.

## Why Full History is Sufficient Here

Our existing use case is for the BC Laws chat bot. Users internal to government query the system in plain language, and they receive a generated response based on context from a set of vector-indexed law data.

When dealing with questions of law, precision and accuracy are important. Users need to be able to reference specific passage of acts and regulations, not just a summarized version of them, so losing detail would be a detriment to our audience.

In our early RAG implementation, we were using a smaller Mixtral-7B model. This model considers 32,000 tokens for input. This context window was sometimes a problem if a chat continued, especially because we would continue to send historic context pulled from the database with each request. It was very possible to reach the limit.

By comparison, the current agentic workflow chat is using the Azure OpenAI service. Assuming you use the GPT-4o model, your input token maximum is now 128,000, or four times Mixtral's. On top of this, we are not sending past database contexts with each request, only the most recent one. The exchange between the user and assistant is miniscule in size compared to even one of these database contexts. A chat would have to continue for a very lengthy amount of time before we approached this new maximum, and our users' past chats don't suggest that conversations continue beyond a few exchanges.

The demand on the BC Laws application is very low at the moment, so the scheduled summaries of chats is sufficient for the current use. If it's decided that a more reactive user summary is needed, we can simply increase the interval of the scheduled summary task.
