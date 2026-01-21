import { randomUUID } from "node:crypto";

import { relations, sql } from "drizzle-orm";
import { index, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const userRoleValues = [
  "analyst",
  "sme",
  "data-analyst",
  "clinical-reviewer",
  "audit-lead",
  "it-engineer",
  "other",
] as const;
export type UserRole = (typeof userRoleValues)[number];

const sessionTypeValues = ["chat", "apc"] as const;
export type SessionType = (typeof sessionTypeValues)[number];

export const users = sqliteTable(
  "users",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => randomUUID()),
    oktaId: text("okta_id").notNull().unique(),
    email: text("email").notNull().unique(),
    name: text("name").notNull(),
    role: text("role", { enum: userRoleValues }).default("other"),
    isAdmin: integer("is_admin", { mode: "boolean" }).notNull().default(false),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
      .notNull()
      .default(sql`(strftime('%s','now') * 1000)`),
  },
  (users) => [index("idx_users_okta_id").on(users.oktaId)]
);

export type User = typeof users.$inferSelect;
export type UserInsert = typeof users.$inferInsert;

export const sessions = sqliteTable(
  "sessions",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => randomUUID()),
    userId: text("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    type: text("type", { enum: sessionTypeValues }).notNull().default("chat"),
    topic: text("topic").notNull(),
    notes: text("notes", { mode: "json" }),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
      .notNull()
      .default(sql`(strftime('%s','now') * 1000)`),
  },
  (sessions) => [
    index("idx_sessions_user_id").on(sessions.userId),
    index("idx_sessions_type").on(sessions.type),
  ]
);

export type Session = typeof sessions.$inferSelect;
export type SessionInsert = typeof sessions.$inferInsert;

export const sections = sqliteTable(
  "sections",
  {
    id: integer("id", { mode: "number" }).primaryKey({ autoIncrement: true }),
    sessionId: text("session_id")
      .notNull()
      .references(() => sessions.id, { onDelete: "cascade" }),
    chatId: text("chat_id")
      .notNull()
      .references(() => chat.id, { onDelete: "cascade" }),
    title: text("title").notNull(),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
      .notNull()
      .default(sql`(strftime('%s','now') * 1000)`),
  },
  (sections) => [
    index("idx_sections_session_id").on(sections.sessionId),
    index("idx_sections_chat_id").on(sections.chatId),
  ]
);

export type Section = typeof sections.$inferSelect;
export type SectionInsert = typeof sections.$inferInsert;

export const sessionRelations = relations(sessions, ({ one, many }) => ({
  user: one(users, { fields: [sessions.userId], references: [users.id] }),
  sections: many(sections),
}));

export const sectionRelations = relations(sections, ({ one }) => ({
  session: one(sessions, { fields: [sections.sessionId], references: [sessions.id] }),
  chat: one(chat, { fields: [sections.chatId], references: [chat.id] }),
}));

export const userRelations = relations(users, ({ many }) => ({
  sessions: many(sessions),
  messageFeedback: many(messageFeedback),
  generalFeedback: many(generalFeedback),
  highlightedText: many(highlightedText),
}));

export const chat = sqliteTable("chats", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => randomUUID()),
  createdAt: integer("created_at", { mode: "timestamp_ms" })
    .notNull()
    .default(sql`(strftime('%s','now') * 1000)`),
});

export type Chat = typeof chat.$inferSelect;
export type ChatInsert = typeof chat.$inferInsert;

export const chatRelations = relations(chat, ({ many }) => ({
  messages: many(messages),
}));

const messageRoleValues = ["user", "assistant", "system"] as const;

export interface DocumentData {
  title: string;
  url: string;
  relevance: number;
}

export const messages = sqliteTable(
  "messages",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => randomUUID()),
    chatId: text("chat_id")
      .notNull()
      .references(() => chat.id, { onDelete: "cascade" }),
    role: text("role", { enum: messageRoleValues }).notNull(),
    content: text("content").notNull(),
    modelUsed: text("model_used"),
    documents: text("documents", { mode: "json" }).$type<DocumentData[] | null>(),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
      .notNull()
      .default(sql`(strftime('%s','now') * 1000)`),
    feedbackId: text("feedback_id").references(() => messageFeedback.id, {
      onDelete: "cascade",
    }),
  },
  (messages) => [index("idx_messages_chat_id").on(messages.chatId)]
);

export type Message = Omit<typeof messages.$inferSelect, "chatId">;
export type MessageInsert = typeof messages.$inferInsert;

export const messageRelations = relations(messages, ({ one, many }) => ({
  chat: one(chat, { fields: [messages.chatId], references: [chat.id] }),
  feedback: one(messageFeedback, {
    fields: [messages.feedbackId],
    references: [messageFeedback.id],
  }),
  highlightedText: many(highlightedText),
}));

const feedbackTypeValues = ["positive", "negative"] as const;
export type FeedbackType = (typeof feedbackTypeValues)[number];
export const messageFeedback = sqliteTable(
  "message_feedback",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => randomUUID()),
    userId: text("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    type: text("type", { enum: feedbackTypeValues }).notNull(),
    issueType: text("issue_type"),
    details: text("details"),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
      .notNull()
      .default(sql`(strftime('%s','now') * 1000)`),
  },
  (feedback) => [index("idx_feedbacks_user_id").on(feedback.userId)]
);

export type MessageFeedback = typeof messageFeedback.$inferSelect;
export type MessageFeedbackInsert = typeof messageFeedback.$inferInsert;

export const messageFeedbackRelations = relations(messageFeedback, ({ one }) => ({
  user: one(users, { fields: [messageFeedback.userId], references: [users.id] }),
  message: one(messages, { fields: [messageFeedback.id], references: [messages.feedbackId] }),
}));

// Highlighted text from chat messages
export const highlightedText = sqliteTable(
  "highlighted_text",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => randomUUID()),
    userId: text("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    sessionId: text("session_id")
      .notNull()
      .references(() => sessions.id, { onDelete: "cascade" }),
    messageId: text("message_id")
      .notNull()
      .references(() => messages.id, { onDelete: "cascade" }),
    sectionId: integer("section_id", { mode: "number" }).references(() => sections.id),
    selectedText: text("selected_text").notNull(),
    contextBefore: text("context_before"),
    contextAfter: text("context_after"),
    startOffset: integer("start_offset", { mode: "number" }).notNull(),
    endOffset: integer("end_offset", { mode: "number" }).notNull(),
    notes: text("notes"),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
      .notNull()
      .default(sql`(strftime('%s','now') * 1000)`),
  },
  (highlightedText) => [
    index("idx_highlighted_text_user_id").on(highlightedText.userId),
    index("idx_highlighted_text_session_id").on(highlightedText.sessionId),
    index("idx_highlighted_text_message_id").on(highlightedText.messageId),
  ]
);

export type HighlightedText = typeof highlightedText.$inferSelect;
export type HighlightedTextInsert = typeof highlightedText.$inferInsert;

export const highlightedTextRelations = relations(highlightedText, ({ one }) => ({
  user: one(users, { fields: [highlightedText.userId], references: [users.id] }),
  message: one(messages, { fields: [highlightedText.messageId], references: [messages.id] }),
}));

// General app feedback table
export const generalFeedback = sqliteTable(
  "general_feedback",
  {
    id: text("id")
      .primaryKey()
      .$defaultFn(() => randomUUID()),
    userId: text("user_id")
      .notNull()
      .references(() => users.id, { onDelete: "cascade" }),
    category: text("category"),
    subject: text("subject").notNull(),
    details: text("details").notNull(),
    createdAt: integer("created_at", { mode: "timestamp_ms" })
      .notNull()
      .default(sql`(strftime('%s','now') * 1000)`),
  },
  (feedback) => [index("idx_general_feedback_user_id").on(feedback.userId)]
);

export type GeneralFeedback = typeof generalFeedback.$inferSelect;
export type GeneralFeedbackInsert = typeof generalFeedback.$inferInsert;

export const generalFeedbackRelations = relations(generalFeedback, ({ one }) => ({
  user: one(users, { fields: [generalFeedback.userId], references: [users.id] }),
}));
