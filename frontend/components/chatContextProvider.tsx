"use client";
import { Message, MessageInsert } from "@/db/schemas";
import type { ChatData } from "@/lib/chat";
import { createContext, FC, useContext, useEffect, useState } from "react";
import { SubmitHandler } from "./chatInput";
import { useParams } from "next/navigation";
import { ClientSessionMessage, ClientSessionMessages } from "@/lib/db";

export type AddServerMessageFunc = (
  message: Omit<MessageInsert, "chatId">,
  sectionId: string
) => Promise<Message>;

export interface MessagesContext {
  chatData: ChatData;
  currentSection: string;
  currentMessages: ClientSessionMessages;
  aiResponse: string | null;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  addMessage: (sectionData: string, newMessage: Omit<Message, "documents" | "createdAt">) => void;
  setChatData: (newChatData: ChatData) => void;
  setSelectedSection: (id: string) => void;
  addChunk: (chunk: string, reset?: boolean) => void;
  onChatSubmit: SubmitHandler;
}

const chatContext = createContext<MessagesContext | undefined>(undefined);

interface Props {
  children: React.ReactNode;
  initChatData?: ChatData;
  addServerMessage: AddServerMessageFunc;
}

export const ChatProvider: FC<Props> = ({ children, initChatData = [], addServerMessage }) => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [chatData, setChatData] = useState<MessagesContext["chatData"]>(initChatData);
  const [currentSectionId, setCurrentSectionId] = useState<MessagesContext["currentSection"]>(
    initChatData[0]?.sectionId ?? ""
  );
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [controller, setController] = useState<AbortController>();
  const [loading, setLoading] = useState(false);

  const currentMessages = chatData.find(
    (section) => section.sectionId === currentSectionId
  )?.messages;
  if (!currentMessages) throw new Error("Section does not exist");

  useEffect(() => {
    return () => controller?.abort();
  }, [controller]);

  const addChunk = (chunk: string, reset?: boolean) => {
    if (reset) {
      return setAiResponse(chunk);
    }
    setAiResponse((prev) => {
      if (prev == null) return chunk;
      return prev + chunk;
    });
  };

  const addMessage: MessagesContext["addMessage"] = async (sectionId, newMessage) => {
    setChatData((prevChatData) => {
      const sectionIndex = prevChatData.findIndex((section) => section.sectionId === sectionId);
      if (sectionIndex === -1) throw new Error("Section does not exist");
      const newChatData = [...prevChatData];
      const section = newChatData[sectionIndex];
      // Dedupe based on `id` if present
      if (newMessage.id != null && section.messages.some((m) => m.id === newMessage.id)) {
        return prevChatData;
      }
      const newMessages: ClientSessionMessage[] = [
        ...section.messages,
        {
          content: newMessage.content,
          id: newMessage.id,
          createdAt: new Date(),
          documents: null,
          modelUsed: newMessage.modelUsed,
          role: newMessage.role,
          chatId: section.chatId,
          feedbackId: null,
          feedback: null,
        },
      ];
      newChatData[sectionIndex] = { ...section, messages: newMessages };
      return newChatData;
    });
  };

  const fetchResponse = async (abortCont?: AbortController) => {
    let newController = abortCont;
    if (!newController) {
      newController = new AbortController();
      setController(newController);
    }
    const resp = await fetch("/api/chat", {
      method: "POST",
      signal: newController.signal,
      body: JSON.stringify({ sessionId }),
    });
    const reader = resp.body?.getReader();
    if (!reader) {
      throw new Error("Something went wrong with chat");
    }
    const decoder = new TextDecoder();
    let finalMsg = "";
    let messageId: string | null = null;
    let buffer = "";
    addChunk("", true);

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      buffer += chunk;
      // Process complete SSE messages
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || ""; // Keep incomplete message in buffer

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === "content") {
              finalMsg += data.content;
              addChunk(data.content);
            } else if (data.type === "messageId") {
              messageId = data.messageId;
            }
          } catch (error) {
            console.warn("Failed to parse SSE data:", line, error);
          }
        }
      }
    }

    addMessage(currentSectionId, {
      content: finalMsg,
      role: "assistant",
      id: messageId || crypto.randomUUID(),
      modelUsed: null,
      feedbackId: null,
    });
    addChunk("", true);
  };

  const onChatSubmit: SubmitHandler = async (input, model) => {
    setLoading(true);
    addMessage(currentSectionId, {
      content: input,
      role: "user",
      id: crypto.randomUUID(),
      modelUsed: model,
      feedbackId: null,
    });
    await addServerMessage(
      {
        content: input,
        role: "user",
        modelUsed: model,
      },
      currentSectionId
    );
    await fetchResponse();
    setLoading(false);
  };

  useEffect(() => {
    if (currentMessages.length === 1 && currentMessages[0].role === "user") {
      const controller = new AbortController();
      (async () => {
        setLoading(true);
        await fetchResponse(controller);
        setLoading(false);
      })();
      return () => controller.abort("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setSelectedSection = (sectionId: string) => {
    const newSection = chatData.find((data) => data.sectionId === sectionId);
    if (!newSection) throw new Error("Section does not exist");
    setCurrentSectionId(sectionId);
  };

  const onSetChatData = (newChatData: MessagesContext["chatData"]) => {
    setChatData(newChatData);
    setCurrentSectionId(newChatData[0].sectionId);
  };

  return (
    <chatContext.Provider
      value={{
        chatData,
        currentSection: currentSectionId,
        currentMessages,
        aiResponse,
        loading,
        setLoading,
        addMessage,
        setChatData: onSetChatData,
        setSelectedSection,
        addChunk,
        onChatSubmit,
      }}
    >
      {children}
    </chatContext.Provider>
  );
};

export const useChatContext = () => {
  const chatContextBody = useContext(chatContext);
  if (chatContextBody === undefined) throw new Error("Chat context is missing!");
  return chatContextBody;
};
