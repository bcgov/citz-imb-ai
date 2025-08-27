CREATE TABLE "user" (
    id UUID PRIMARY KEY,
    summary text,
    preferences jsonb,
    last_change timestamp
);

CREATE TABLE chat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    CONSTRAINT FK_ChatUser FOREIGN KEY (user_id) REFERENCES "user"(id),
    created_at timestamp DEFAULT now(),
    updated_at timestamp,
    chat_chain jsonb,
    summary text, 
    title text
);

CREATE INDEX idx_chat_user_id ON chat (user_id);
