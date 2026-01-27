import path from "node:path";
import { pathToFileURL } from "node:url";
import { drizzle } from "drizzle-orm/libsql";
import * as schemas from "../db/schemas";
import { and, desc, eq, inArray, not, sql } from "drizzle-orm";
import { ResearchSections } from "@/app/(auth-protected)/apc-research/server-actions";
import { ChatNavLinks } from "@/app/api/[[...route]]/_authRoutes";

const dbUrl = pathToFileURL(path.join(process.cwd(), process.env.DB_URL!)).href;
export const db = drizzle(dbUrl, {
  schema: schemas,
  casing: "snake_case",
});

const parseCsv = (value?: string | null) =>
  (value ?? "")
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);

export type UserWithAccess = schemas.User;

export const getClientSession = async (sessionId: string) => {
  return await db.query.sessions.findFirst({
    where: eq(schemas.sessions.id, sessionId),
    with: {
      sections: {
        with: {
          chat: {
            with: {
              messages: {
                with: {
                  feedback: true,
                },
                where: not(eq(schemas.messages.role, "system")),
                orderBy: (messages, { asc }) => [asc(messages.createdAt)],
              },
            },
          },
        },
      },
    },
  });
};

export type ClientSession = Awaited<ReturnType<typeof getClientSession>>;

export type ClientSessionMessages =
  NonNullable<ClientSession>["sections"][number]["chat"]["messages"];

export type ClientSessionMessage = ClientSessionMessages[number];

export const getChatSession = async (uid: string, sessionId: string, limit?: number) => {
  const session = await db.query.sessions.findFirst({
    where: and(eq(schemas.sessions.id, sessionId)),
    with: {
      sections: {
        with: {
          chat: {
            with: {
              messages: {
                columns: {
                  content: true,
                  modelUsed: true,
                  role: true,
                },
                orderBy: (messages, { asc }) => [asc(messages.createdAt)],
                limit,
              },
            },
          },
        },
      },
      user: true,
    },
  });

  if (!session || session.user.id !== uid) return null;
  return session;
};

export const createChatSession = async (
  userId: string,
  messages: Omit<schemas.MessageInsert, "chatId">[],
) => {
  const userMsg = messages.find((msg) => msg.role === "user");
  if (!userMsg) throw new Error("Missing initial user msg");

  return await db.transaction(async (tx) => {
    const maxMsgLength = Math.min(20, userMsg.content.length);
    const topic = userMsg.content.substring(0, maxMsgLength);
    const [session] = await tx
      .insert(schemas.sessions)
      .values({ userId, type: "chat", topic })
      .returning();

    const [chat] = await tx.insert(schemas.chat).values({}).returning();
    const insertMsg: schemas.MessageInsert[] = messages.map((msg) => ({
      chatId: chat.id,
      role: msg.role,
      content: msg.content,
      modelUsed: msg.modelUsed,
    }));
    await tx.insert(schemas.messages).values(insertMsg);
    await tx
      .insert(schemas.sections)
      .values({ sessionId: session.id, chatId: chat.id, title: topic });
    return session;
  });
};

export const addToChatSessionMessage = async (
  uid: string,
  chatSessionId: string,
  newMessage: schemas.MessageInsert,
) => {
  return db.transaction(async (tx) => {
    const session = await tx.query.sessions.findFirst({
      where: () => eq(schemas.sessions.id, chatSessionId),
      with: {
        user: true,
        sections: true,
      },
    });
    if (!session) throw new Error("Chat does not exist");
    if (session.user.id !== uid) throw new Error("Unauthorized");

    const targetSection =
      session.sections.find((section) => section.chatId === newMessage.chatId) ||
      session.sections[0];
    if (!targetSection) throw new Error("No chat section found for session");
    const [msg] = await tx
      .insert(schemas.messages)
      .values({
        chatId: targetSection.chatId,
        content: newMessage.content,
        role: newMessage.role,
        modelUsed: newMessage.modelUsed,
      })
      .returning();
    return msg;
  });
};

export const updateChatMessageContent = async (messageId: string, newContent: string) => {
  return db.transaction(async (tx) => {
    await tx
      .update(schemas.messages)
      .set({ content: newContent })
      .where(eq(schemas.messages.id, messageId));
  });
};

export const submitFeedback = async (
  messageId: string,
  feedbackData: schemas.MessageFeedbackInsert,
) => {
  console.log("Submitting feedback for messageId:", messageId);
  console.log("Feedback data:", feedbackData);
  const feedback = await db.transaction(async (tx) => {
    const msg = await tx.query.messages.findFirst({
      where: () => eq(schemas.messages.id, messageId),
    });
    if (!msg) {
      throw new Error("Message does not exist");
    }
    if (msg.feedbackId !== null) {
      await tx
        .delete(schemas.messageFeedback)
        .where(eq(schemas.messageFeedback.id, msg.feedbackId));
    }
    const [newFeedback] = await tx.insert(schemas.messageFeedback).values(feedbackData).returning();
    await tx
      .update(schemas.messages)
      .set({ feedbackId: newFeedback.id })
      .where(eq(schemas.messages.id, messageId));
    return newFeedback;
  });
  return feedback;
};

export const addToResearchSessionChat = async (
  oktaId: string,
  researchSessionId: string,
  researchSectionId: number,
  newMessage: schemas.MessageInsert,
) => {
  await db.transaction(async (tx) => {
    const researchSession = await tx.query.sessions.findFirst({
      where: () => eq(schemas.sessions.id, researchSessionId),
      with: {
        user: true,
      },
    });
    if (researchSession === undefined || researchSession.type !== "apc")
      throw new Error("Research Session does not exist");
    if (researchSession.user.oktaId !== oktaId) throw new Error("Unauthorized");

    const researchSection = await tx.query.sections.findFirst({
      where: () =>
        and(
          eq(schemas.sections.id, researchSectionId),
          eq(schemas.sections.sessionId, researchSessionId),
        ),
    });
    if (researchSection === undefined) throw new Error("Research Section does not exist");
    await tx.insert(schemas.messages).values({
      chatId: researchSection.chatId,
      content: newMessage.content,
      role: newMessage.role,
      modelUsed: newMessage.modelUsed,
    });
  });
};

const TITLES = [
  "Section 1: Code Description Analysis",
  "Section 2: Guideline Examination",
  "Section 3: Payment Rate Comparison",
  "Section 4: Device Code Analysis",
  "Section 5: NCCI Compliance Check",
  "Section 6: Reference Material Review",
  "Final Assessment",
];

export const createResearchSession = async (
  userId: string,
  topic: string,
  sections: ResearchSections,
  modelUsed: string,
) => {
  const sectionArr = Object.values(sections);
  return await db.transaction(async (tx) => {
    console.log("Creating research session for userId:", userId, "with topic:", topic);
    const [researchSession] = await tx
      .insert(schemas.sessions)
      .values({ userId, topic, type: "apc" })
      .returning();
    console.log("Created research session for userId:", userId, "with topic:", topic);
    const chats = await tx
      .insert(schemas.chat)
      .values(sectionArr.map(() => ({})))
      .returning();
    console.log("Created chats for research session:", chats);
    const sectionChats: schemas.MessageInsert[] = chats.map((chat, i) => {
      const section = sectionArr[i];
      if (section.status === "success") {
        return {
          chatId: chat.id,
          content: typeof section.data === "string" ? section.data : JSON.stringify(section.data),
          role: "assistant",
          modelUsed,
        };
      } else {
        return {
          chatId: chat.id,
          content: `Error generating section: ${section.error || "Unknown error"}`,
          role: "assistant",
          modelUsed,
        };
      }
    });
    console.log("Inserting section chats:", sectionChats);
    const [] = await tx.insert(schemas.messages).values(sectionChats).returning();
    const researchSectionData: schemas.SectionInsert[] = sectionArr.map((section, i) => ({
      sessionId: researchSession.id,
      chatId: chats[i].id,
      title: TITLES[i],
    }));
    console.log("Inserting research sections:", researchSectionData);
    const [] = await tx.insert(schemas.sections).values(researchSectionData).returning();

    return researchSession;
  });
};

export const getResearchSections = async (researchSessionId: string) => {
  return await db.query.sections.findMany({
    where: eq(schemas.sections.sessionId, researchSessionId),
    with: {
      chat: {
        with: {
          messages: true,
        },
      },
    },
  });
};

export const getUserData = async (userId: string): Promise<UserWithAccess | null> => {
  const user = await db.query.users.findFirst({
    where: eq(schemas.users.id, userId),
  });
  return user ?? null;
};

export const getUserDataByOkta = async (oktaId: string): Promise<UserWithAccess | null> => {
  const user = await db.query.users.findFirst({
    where: eq(schemas.users.oktaId, oktaId),
  });
  return user ?? null;
};

export const createUser = async (userData: schemas.UserInsert) => {
  const [newUser] = await db.insert(schemas.users).values(userData).returning();
  return newUser;
};

export const updateUserRole = async (oktaId: string, role: schemas.UserRole) => {
  const [updatedUser] = await db
    .update(schemas.users)
    .set({ role })
    .where(eq(schemas.users.oktaId, oktaId))
    .returning();
  return updatedUser;
};
export const setUserAdminStatus = async (userId: string, isAdmin: boolean) => {
  const [updatedUser] = await db
    .update(schemas.users)
    .set({ isAdmin })
    .where(eq(schemas.users.id, userId))
    .returning();
  return updatedUser;
};

export const getAdminCount = async (): Promise<number> => {
  const result = await db
    .select({ count: sql<number>`count(*)` })
    .from(schemas.users)
    .where(eq(schemas.users.isAdmin, true));

  return Number(result[0]?.count ?? 0);
};

export const syncBootstrapAdminRole = async (user: {
  id: string;
  email: string;
}): Promise<UserWithAccess | null> => {
  const bootstrapAdmins = parseCsv(process.env.INITIAL_ADMIN_EMAILS);
  if (bootstrapAdmins.includes(user.email.toLowerCase())) {
    const updated = await setUserAdminStatus(user.id, true);
    return updated ?? null;
  }
  return null;
};

export const getAllUsersWithAccess = async (): Promise<UserWithAccess[]> => {
  return db.query.users.findMany();
};

export const getUserChatHistory = async (userId: string) => {
  const sessions = await db.query.sessions.findMany({
    where: eq(schemas.sessions.userId, userId),
    orderBy: (session, { desc }) => [desc(session.createdAt)],
    limit: 40,
  });

  const chats = sessions.reduce((acc, session) => {
    if (session.type === "chat") {
      acc.push({
        id: session.id,
        type: session.type,
        title: session.topic,
        url: `/chat-research/${session.id}`,
      });
    } else if (session.type === "apc") {
      acc.push({
        id: session.id,
        type: session.type,
        title: session.topic,
        url: `/apc-research/${session.id}`,
      });
    }
    return acc;
  }, [] as ChatNavLinks[]);
  return chats;
};

export const updateChatTopic = async (
  oktaId: string,
  chatId: string,
  newTopic: string,
  chatType: "chat" | "apc",
) => {
  return await db.transaction(async (tx) => {
    const session = await tx.query.sessions.findFirst({
      where: and(eq(schemas.sessions.id, chatId), eq(schemas.sessions.type, chatType)),
      with: {
        user: true,
      },
    });

    if (!session) throw new Error(`${chatType === "chat" ? "Chat" : "Research"} session not found`);
    if (session.user.oktaId !== oktaId) throw new Error("Unauthorized");

    await tx
      .update(schemas.sessions)
      .set({ topic: newTopic })
      .where(eq(schemas.sessions.id, chatId));
  });
};

export const deleteChatSession = async (
  oktaId: string,
  chatId: string,
  chatType: "chat" | "apc",
) => {
  return await db.transaction(async (tx) => {
    const session = await tx.query.sessions.findFirst({
      where: and(eq(schemas.sessions.id, chatId), eq(schemas.sessions.type, chatType)),
      with: {
        user: true,
        sections: {
          columns: {
            id: true,
            chatId: true,
          },
        },
      },
    });

    if (!session) throw new Error(`${chatType === "chat" ? "Chat" : "Research"} session not found`);
    if (session.user.oktaId !== oktaId) throw new Error("Unauthorized");

    const chatIds = session.sections.map((section) => section.chatId);

    if (chatIds.length > 0) {
      await tx.delete(schemas.messages).where(inArray(schemas.messages.chatId, chatIds));
      await tx.delete(schemas.sections).where(eq(schemas.sections.sessionId, chatId));
      await tx.delete(schemas.chat).where(inArray(schemas.chat.id, chatIds));
    } else {
      await tx.delete(schemas.sections).where(eq(schemas.sections.sessionId, chatId));
    }

    await tx.delete(schemas.sessions).where(eq(schemas.sessions.id, chatId));
  });
};

export const submitGeneralFeedback = async (feedbackData: {
  userId: string;
  category?: string;
  subject: string;
  details: string;
}) => {
  const [feedback] = await db
    .insert(schemas.generalFeedback)
    .values({
      userId: feedbackData.userId,
      category: feedbackData.category,
      subject: feedbackData.subject,
      details: feedbackData.details,
    })
    .returning();

  return feedback;
};

export const getSessionNotes = async (sessionId: string) => {
  const sessionResult = await db
    .select({ notes: schemas.sessions.notes })
    .from(schemas.sessions)
    .where(eq(schemas.sessions.id, sessionId))
    .limit(1);

  if (sessionResult.length > 0) {
    const rawNotes = sessionResult[0].notes;
    if (typeof rawNotes === "string") return rawNotes;
    if (rawNotes && typeof rawNotes === "object") {
      const combined = Object.values(rawNotes)
        .map((val) => String(val || "").trim())
        .filter(Boolean)
        .join("\n\n");
      return combined;
    }
    return "";
  }

  return "";
};

export const updateSessionNotes = async (sessionId: string, notes: string) => {
  const sessionResult = await db
    .update(schemas.sessions)
    .set({ notes })
    .where(eq(schemas.sessions.id, sessionId))
    .returning({ id: schemas.sessions.id });

  return sessionResult.length > 0;
};

// Highlight helpers
export const getHighlightsForUser = async (sessionId: string) => {
  return db
    .select()
    .from(schemas.highlightedText)
    .where(eq(schemas.highlightedText.sessionId, sessionId))
    .orderBy(schemas.highlightedText.createdAt);
};

export const createHighlightForUser = async (
  oktaId: string,
  data: {
    sessionId: string;
    messageId: string;
    sectionId?: number | null;
    selectedText: string;
    contextBefore?: string | null;
    contextAfter?: string | null;
    startOffset: number;
    endOffset: number;
    notes?: string | null;
  },
) => {
  const user = await db.query.users.findFirst({ where: eq(schemas.users.oktaId, oktaId) });
  if (!user) throw new Error("User not found");

  const [highlight] = await db
    .insert(schemas.highlightedText)
    .values({
      userId: user.id,
      sessionId: data.sessionId,
      messageId: data.messageId,
      sectionId: data.sectionId ?? null,
      selectedText: data.selectedText,
      contextBefore: data.contextBefore ?? null,
      contextAfter: data.contextAfter ?? null,
      startOffset: data.startOffset,
      endOffset: data.endOffset,
      notes: data.notes ?? null,
    })
    .returning();

  return highlight;
};

export const deleteHighlightForUser = async (oktaId: string, highlightId: string) => {
  const user = await db.query.users.findFirst({ where: eq(schemas.users.oktaId, oktaId) });
  if (!user) throw new Error("User not found");

  await db
    .delete(schemas.highlightedText)
    .where(
      and(eq(schemas.highlightedText.id, highlightId), eq(schemas.highlightedText.userId, user.id)),
    );
};

export const updateHighlightNotesForUser = async (
  oktaId: string,
  highlightId: string,
  notes?: string | null,
) => {
  const user = await db.query.users.findFirst({ where: eq(schemas.users.oktaId, oktaId) });
  if (!user) throw new Error("User not found");

  const [updatedHighlight] = await db
    .update(schemas.highlightedText)
    .set({ notes: notes ?? null })
    .where(
      and(eq(schemas.highlightedText.id, highlightId), eq(schemas.highlightedText.userId, user.id)),
    )
    .returning();

  return updatedHighlight;
};

// Combined notes + highlights for a session (chat or research)
export const getSessionNotesAndHighlights = async (oktaId: string, sessionId: string) => {
  const user = await db.query.users.findFirst({ where: eq(schemas.users.oktaId, oktaId) });
  if (!user) throw new Error("User not found");

  const session = await db.query.sessions.findFirst({
    where: eq(schemas.sessions.id, sessionId),
    with: {
      user: true,
    },
  });

  if (!session) throw new Error("Session not found");
  if (session.user.id !== user.id) throw new Error("Unauthorized");

  const highlights = await getHighlightsForUser(sessionId);

  return {
    notes: (() => {
      if (typeof session.notes === "string") return session.notes;
      if (session.notes && typeof session.notes === "object") {
        const combined = Object.values(session.notes)
          .map((val) => String(val || "").trim())
          .filter(Boolean)
          .join("\n\n");
        return combined;
      }
      return "";
    })(),
    highlights,
  };
};

export const getAllFeedback = async () => {
  const messageFeedback = await db
    .select({
      id: schemas.messageFeedback.id,
      userId: schemas.messageFeedback.userId,
      userEmail: schemas.users.email,
      userName: schemas.users.name,
      type: schemas.messageFeedback.type,
      issueType: schemas.messageFeedback.issueType,
      details: schemas.messageFeedback.details,
      createdAt: schemas.messageFeedback.createdAt,
      messageId: schemas.messages.id,
      messageContent: schemas.messages.content,
      messageRole: schemas.messages.role,
      messageModel: schemas.messages.modelUsed,
      sessionId: schemas.sessions.id,
      sessionType: schemas.sessions.type,
    })
    .from(schemas.messageFeedback)
    .leftJoin(schemas.users, eq(schemas.messageFeedback.userId, schemas.users.id))
    .leftJoin(schemas.messages, eq(schemas.messages.feedbackId, schemas.messageFeedback.id))
    .leftJoin(schemas.sections, eq(schemas.sections.chatId, schemas.messages.chatId))
    .leftJoin(schemas.sessions, eq(schemas.sessions.id, schemas.sections.sessionId))
    .orderBy(desc(schemas.messageFeedback.createdAt));

  const generalFeedback = await db
    .select({
      id: schemas.generalFeedback.id,
      userId: schemas.generalFeedback.userId,
      userEmail: schemas.users.email,
      userName: schemas.users.name,
      category: schemas.generalFeedback.category,
      subject: schemas.generalFeedback.subject,
      details: schemas.generalFeedback.details,
      createdAt: schemas.generalFeedback.createdAt,
    })
    .from(schemas.generalFeedback)
    .leftJoin(schemas.users, eq(schemas.generalFeedback.userId, schemas.users.id))
    .orderBy(desc(schemas.generalFeedback.createdAt));

  return { messageFeedback, generalFeedback };
};
