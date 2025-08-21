CREATE TABLE "user" (
    id UUID PRIMARY KEY,
    summary text,
    preferences jsonb,
    last_change timestamp
);

CREATE TABLE chat (
    id UUID PRIMARY KEY,
    user_id UUID,
    CONSTRAINT FK_ChatUser FOREIGN KEY (user_id) REFERENCES "user"(id),
    created_at timestamp DEFAULT now(),
    chat_chain jsonb,
    summary text,
    is_active BOOLEAN
);

CREATE INDEX idx_chat_user_id ON chat (user_id);
CREATE INDEX idx_chat_id_user_id ON chat (id, user_id);
