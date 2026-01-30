import type { Context } from "hono";
import { Hono } from "hono";
import type { ContentfulStatusCode } from "hono/utils/http-status";
import { fetchCptCodes } from "@/app/(auth-protected)/apc-research/server-actions";
import { FeedbackType, UserRole } from "@/db/schemas";
import { streamSSE } from "hono/streaming";
import { ResponsesModel } from "openai/resources/shared.mjs";
import { AVAILABLE_MODELS, queryllmStream } from "@/lib/llm";
import {
  addMessageToChatSession,
  getUserChatHistory,
  getChatSession,
  updateChatTopic,
  deleteChatSession,
  submitFeedback,
  submitGeneralFeedback,
  updateChatMessageContent,
  updateUserRole,
  getSessionNotes,
  updateSessionNotes,
  getHighlightsForUser,
  createHighlightForUser,
  deleteHighlightForUser,
  updateHighlightNotesForUser,
  getSessionNotesAndHighlights,
  createResearchSession,
  getAllFeedback,
  getAllUsersWithAccess,
  setUserAdminStatus,
  getAdminCount,
} from "@/lib/db";
import { obtainUserData, type UserAuthEnv } from "@/lib/session";

export const app = new Hono<UserAuthEnv>();

type ErrorCode =
  | "bad_request"
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "internal_error";

const jsonError = (c: Context, status: ContentfulStatusCode, message: string, code?: ErrorCode) => {
  return c.json({ error: message, code }, status);
};

const requireAdmin = (c: Context<UserAuthEnv>) => {
  if (!c.var.user.isAdmin) {
    return jsonError(c, 403, "Admin access required", "forbidden");
  }
  return null;
};

app.use(obtainUserData);
app.get("/chat/:sessionId/:sectionId", async (c) => {
  try {
    const sessionId = c.req.param("sessionId");
    const sectionId = c.req.param("sectionId");
    console.log(`Received chat request for sessionId: ${sessionId}, sectionId: ${sectionId}`);
    const chatSession = await getChatSession(c.var.user.id, sessionId);
    if (!chatSession) {
      return jsonError(c, 404, "Chat session not found", "not_found");
    }
    console.log(chatSession.sections);
    const section = chatSession.sections.find((section) => section.id === sectionId);
    if (!section) {
      return jsonError(c, 400, "No sections found for session", "bad_request");
    }

    const ctx = section.messages.map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));
    const lastMsg = section.messages.at(-1);
    console.log("Last message:", lastMsg);
    if (!lastMsg) {
      return jsonError(c, 400, "No messages in chat session", "bad_request");
    }
    if (lastMsg.role !== "user") {
      return jsonError(c, 400, "Last message is not from user", "bad_request");
    }
    const model = lastMsg.modelUsed as ResponsesModel;
    if (!AVAILABLE_MODELS.includes(model)) {
      return jsonError(c, 400, "Model not supported", "bad_request");
    }
    const responseStream = await queryllmStream(ctx, model);
    const reader = responseStream.getReader();
    const decoder = new TextDecoder();

    const newMsg = await addMessageToChatSession(c.var.user.id, sessionId, {
      role: "assistant",
      content: "",
      modelUsed: model,
      sectionId: section.id,
    });
    return streamSSE(c, async (stream) => {
      let finalText = "";
      // Send the message ID as metadata event
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });
        if (!chunkText) continue;
        if (finalText === "") {
          finalText += chunkText;
          newMsg.content = finalText;
          stream.writeSSE({ event: "begin", data: JSON.stringify(newMsg), id: newMsg.id });
        } else {
          finalText += chunkText;
          stream.writeSSE({
            event: "data",
            data: finalText,
            id: newMsg.id,
          });
        }
      }
      stream.writeSSE({ event: "done", data: "[DONE]", id: newMsg.id });

      await updateChatMessageContent(newMsg.id, finalText);
    });
  } catch (error) {
    console.error("Error handling chat request:", error);
    return jsonError(c, 500, "Failed to process chat", "internal_error");
  }
});

export interface ChatNavLinks {
  id: string;
  title: string;
  url: string;
  type: "chat" | "apc";
}

app.get("/chat-history", async (c) => {
  const userId = c.var.user.id;
  const chats = await getUserChatHistory(userId);
  return c.json(chats);
});

app.post("/cpt-codes", async (c) => {
  try {
    const { topic, model } = await c.req.json<{ topic: string; model: ResponsesModel }>();
    return c.json(await fetchCptCodes(topic, model));
  } catch (error) {
    console.error("Error fetching CPT codes:", error);
    return jsonError(c, 500, "Failed to fetch CPT codes", "internal_error");
  }
});

app.put("/chat/:chatId", async (c) => {
  const chatId = c.req.param("chatId");
  const { title, type } = await c.req.json<{ title: string; type: "chat" | "apc" }>();
  const oktaId = c.var.user.oktaId;

  try {
    await updateChatTopic(oktaId, chatId, title, type);
    return c.json({ success: true });
  } catch (error) {
    console.error("Error updating chat topic:", error);
    return jsonError(c, 400, (error as Error).message, "bad_request");
  }
});

app.delete("/chat/:chatId", async (c) => {
  const chatId = c.req.param("chatId");
  const { type } = await c.req.json<{ type: "chat" | "apc" }>();
  const oktaId = c.var.user.oktaId;
  console.log(`Deleting chat session ${chatId} of type ${type} for user ${oktaId}`);
  try {
    await deleteChatSession(oktaId, chatId, type);
    return c.json({ success: true });
  } catch (error) {
    console.log(error);
    return jsonError(c, 400, "Failed to delete chat session", "bad_request");
  }
});

app.post("/create-research", async (c) => {
  try {
    const { targetCpt, contextDetails, model } = await c.req.json<{
      targetCpt: string;
      contextDetails: string;
      model: ResponsesModel;
    }>();
    const session = await createResearchSession(c.var.user.id, targetCpt, model);
    console.log(session, "Created research session");
    return c.json({ id: session.id });
  } catch (error) {
    console.error("Error creating research session:", JSON.stringify(error));
    return jsonError(c, 500, "Failed to create research session", "internal_error");
  }
});

app.post("/feedback", async (c) => {
  const { messageId, type, issueType, details } = await c.req.json<{
    messageId: string;
    type: FeedbackType;
    issueType?: string;
    details: string;
  }>();

  const userId = c.var.user.id;

  try {
    const feedback = await submitFeedback(messageId, {
      type,
      issueType,
      details,
      userId: userId,
    });
    return c.json({ success: true, feedback });
  } catch (error) {
    console.log(error);
    return jsonError(c, 500, "Failed to submit feedback", "internal_error");
  }
});

app.post("/general-feedback", async (c) => {
  const { category, subject, details } = await c.req.json<{
    category?: string;
    subject: string;
    details: string;
  }>();

  const userId = c.var.user.id;

  try {
    const feedback = await submitGeneralFeedback({
      userId,
      category,
      subject,
      details,
    });
    return c.json({ success: true, feedback });
  } catch (error) {
    console.error("Error submitting general feedback:", error);
    return jsonError(c, 500, "Failed to submit feedback", "internal_error");
  }
});

app.patch("/user/role", async (c) => {
  const { role } = await c.req.json<{
    role: UserRole;
  }>();

  const oktaId = c.var.user.oktaId;

  try {
    const updatedUser = await updateUserRole(oktaId, role);
    return c.json({ success: true, user: updatedUser });
  } catch (error) {
    console.error("Error updating user role:", error);
    return jsonError(c, 500, "Failed to update user role", "internal_error");
  }
});

// Notes endpoints
app.get("/notes/:sessionId", async (c) => {
  try {
    const sessionId = c.req.param("sessionId");
    const notes = await getSessionNotes(sessionId);
    return c.json({ notes });
  } catch (error) {
    console.error("Error fetching notes:", error);
    return jsonError(c, 500, "Failed to fetch notes", "internal_error");
  }
});

app.put("/notes/:sessionId", async (c) => {
  try {
    const sessionId = c.req.param("sessionId");
    const { notes } = await c.req.json<{ notes: string }>();

    if (typeof notes !== "string") {
      return jsonError(c, 400, "Invalid notes format", "bad_request");
    }

    const success = await updateSessionNotes(sessionId, notes);
    if (!success) {
      return jsonError(c, 404, "Session not found", "not_found");
    }

    return c.json({ success: true });
  } catch (error) {
    console.error("Error saving notes:", error);
    return jsonError(c, 500, "Failed to save notes", "internal_error");
  }
});

// Highlights endpoints
app.get("/highlights", async (c) => {
  try {
    const url = new URL(c.req.url);
    const sessionId = url.searchParams.get("sessionId");
    if (!sessionId) {
      return jsonError(c, 400, "SessionId is required", "bad_request");
    }
    const highlights = await getHighlightsForUser(sessionId);
    return c.json(highlights);
  } catch (error) {
    console.error("Error fetching highlights:", error);
    if (error instanceof Error && error.message === "User not found") {
      return jsonError(c, 404, "User not found", "not_found");
    }
    return jsonError(c, 500, "Failed to fetch highlights", "internal_error");
  }
});

app.post("/highlights", async (c) => {
  try {
    const body = await c.req.json();
    const {
      sessionId,
      messageId,
      sectionId,
      selectedText,
      contextBefore,
      contextAfter,
      startOffset,
      endOffset,
      notes,
    } = body;

    if (
      !sessionId ||
      !messageId ||
      !selectedText ||
      startOffset === undefined ||
      endOffset === undefined
    ) {
      return jsonError(c, 400, "Missing required fields", "bad_request");
    }
    const highlight = await createHighlightForUser(c.var.user.oktaId, {
      sessionId,
      messageId,
      sectionId: sectionId ? Number(sectionId) : undefined,
      selectedText,
      contextBefore,
      contextAfter,
      startOffset,
      endOffset,
      notes,
    });

    return c.json(highlight);
  } catch (error) {
    console.error("Error creating highlight:", error);
    if (error instanceof Error && error.message === "User not found") {
      return jsonError(c, 404, "User not found", "not_found");
    }
    return jsonError(c, 500, "Failed to create highlight", "internal_error");
  }
});

app.delete("/highlights/:id", async (c) => {
  try {
    const highlightId = c.req.param("id");
    await deleteHighlightForUser(c.var.user.oktaId, highlightId);
    return c.json({ success: true });
  } catch (error) {
    console.error("Error deleting highlight:", error);
    if (error instanceof Error && error.message === "User not found") {
      return jsonError(c, 404, "User not found", "not_found");
    }
    return jsonError(c, 500, "Failed to delete highlight", "internal_error");
  }
});

app.patch("/highlights/:id", async (c) => {
  try {
    const highlightId = c.req.param("id");
    const body = await c.req.json();
    const { notes } = body;
    const updatedHighlight = await updateHighlightNotesForUser(
      c.var.user.oktaId,
      highlightId,
      notes,
    );
    return c.json(updatedHighlight);
  } catch (error) {
    console.error("Error updating highlight:", error);
    if (error instanceof Error && error.message === "User not found") {
      return jsonError(c, 404, "User not found", "not_found");
    }
    return jsonError(c, 500, "Failed to update highlight", "internal_error");
  }
});

// Admin endpoints
app.get("/admin/feedback", async (c) => {
  const guard = requireAdmin(c);
  if (guard) return guard;

  const data = await getAllFeedback();
  return c.json(data);
});

app.get("/admin/users", async (c) => {
  const guard = requireAdmin(c);
  if (guard) return guard;

  const users = await getAllUsersWithAccess();
  return c.json(users);
});

app.patch("/admin/users/:userId/roles", async (c) => {
  const guard = requireAdmin(c);
  if (guard) return guard;

  const userId = c.req.param("userId");
  const body = await c.req.json<{ isAdmin?: boolean }>();
  const isAdmin = body.isAdmin;
  if (typeof isAdmin !== "boolean") {
    return jsonError(c, 400, "isAdmin flag required", "bad_request");
  }

  try {
    if (!isAdmin) {
      const adminCount = await getAdminCount();
      if (adminCount <= 1) {
        return jsonError(c, 400, "Cannot remove the last admin user", "bad_request");
      }
    }

    const updatedUser = await setUserAdminStatus(userId, isAdmin);
    return c.json({ isAdmin: updatedUser?.isAdmin ?? false });
  } catch (error) {
    console.error("Error updating user roles:", error);
    return jsonError(c, 500, "Failed to update admin status", "internal_error");
  }
});

// Combined session data: notes + highlights in one request
app.get("/session/:sessionId/notes-highlights", async (c) => {
  try {
    const sessionId = c.req.param("sessionId");
    const data = await getSessionNotesAndHighlights(c.var.user.oktaId, sessionId);
    return c.json(data);
  } catch (error) {
    console.error("Error fetching session data:", error);
    if (error instanceof Error) {
      if (error.message === "User not found") {
        return jsonError(c, 404, "User not found", "not_found");
      }
      if (error.message === "Unauthorized") {
        return jsonError(c, 403, "Unauthorized", "forbidden");
      }
      if (error.message === "Session not found") {
        return jsonError(c, 404, "Session not found", "not_found");
      }
    }
    return jsonError(c, 500, "Failed to fetch session data", "internal_error");
  }
});
