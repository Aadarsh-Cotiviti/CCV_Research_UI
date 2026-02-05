"use client";
import { Message, MessageInsert } from "@/db/schemas";
import type { ChatData } from "@/lib/chat";
import { createContext, FC, useContext, useEffect, useState } from "react";
import { SubmitHandler } from "./chatInput";
import { useParams } from "next/navigation";
import { ClientSessionMessage, ClientSessionMessages } from "@/lib/db";

export type AddServerMessageFunc = (message: MessageInsert, sessionId: string) => Promise<Message>;

type SectionState = "idle" | "loading" | "responding" | "error";

export interface MessagesContext {
  chatData: ChatData;
  currentSectionId: string;
  currentMessages: ClientSessionMessages;
  state: SectionState;
  setState: (state: SectionState) => void;
  setChatData: (newChatData: ChatData) => void;
  setSelectedSection: (id: string) => void;
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
  const [currentSectionId, setCurrentSectionId] = useState<MessagesContext["currentSectionId"]>(
    initChatData[0]?.sectionId ?? "",
  );
  const [state, setState] = useState<MessagesContext["state"]>("idle");

  const currentSection = chatData.find((section) => section.sectionId === currentSectionId);
  if (!currentSection) throw new Error("Section does not exist");

  const addMessage = async (
    sectionId: string,
    newMessage: Omit<Message, "documents" | "createdAt">,
  ) => {
    setChatData((prevChatData) => {
      const sectionIndex = prevChatData.findIndex((section) => section.sectionId === sectionId);
      if (sectionIndex === -1) throw new Error("Section does not exist");
      const newChatData = [...prevChatData];
      const section = newChatData[sectionIndex];
      if (section.messages instanceof Promise) {
        throw new Error("Messages are still loading");
      }
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
          sectionId: sectionId,
          feedbackId: null,
          feedback: null,
        },
      ];
      newChatData[sectionIndex] = { ...section, messages: newMessages };
      return newChatData;
    });
  };

  const updateChatMessage = (sectionId: string, messageId: string, content: string) => {
    setChatData((prevChatData) => {
      const sectionIndex = prevChatData.findIndex((section) => section.sectionId === sectionId);
      if (sectionIndex === -1) throw new Error("Section does not exist");
      const newChatData = [...prevChatData];
      const section = newChatData[sectionIndex];
      if (section.messages instanceof Promise) {
        throw new Error("Messages are still loading");
      }
      const newMessages = section.messages.map((msg) =>
        msg.id === messageId ? { ...msg, content } : msg,
      );
      newChatData[sectionIndex] = { ...section, messages: newMessages };
      return newChatData;
    });
  };

  const fetchResponse = async () => {
    setState("loading");
    const resp = new EventSource(`/api/chat/${sessionId}/${currentSectionId}`, {
      withCredentials: true,
    });

    resp.addEventListener("begin", (event) => {
      try {
        const msg = JSON.parse(event.data) as ClientSessionMessage;
        setState("responding");
        addMessage(currentSectionId, msg);
      } catch (e) {
        console.warn("Failed to parse begin event:", e);
      }
    });

    resp.addEventListener("data", (event) => {
      try {
        const messageId = (event as MessageEvent).lastEventId;
        const chunkText = event.data;
        updateChatMessage(currentSectionId, messageId, chunkText);
      } catch (e) {
        console.warn("Failed to handle data event:", e);
      }
    });

    resp.addEventListener("done", () => {
      setState("idle");
      resp.close();
    });

    resp.addEventListener("error", (event) => {
      console.error("SSE error:", event);
      setState("error");
      resp.close();
    });
  };

  const onChatSubmit: SubmitHandler = async (input, model) => {
    setState("loading");
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
        sectionId: currentSectionId,
      },
      sessionId,
    );
    await fetchResponse();
  };

  useEffect(() => {
    const messages = currentSection.messages;
    if (messages instanceof Promise) {
      setState("loading");
      const awaitMsg = async () => {
        try {
          const resolvedMessages = await messages;
          setChatData((prevChatData) => {
            const sectionIndex = prevChatData.findIndex(
              (section) => section.sectionId === currentSectionId,
            );
            if (sectionIndex === -1) throw new Error("Section does not exist");
            const newChatData = [...prevChatData];
            newChatData[sectionIndex] = {
              ...newChatData[sectionIndex],
              messages: resolvedMessages,
            };
            return newChatData;
          });
          setState("idle");
        } catch (e) {
          setState("error");
        }
      };
      awaitMsg();
      return;
    }
    if (messages.length === 1 && messages[0].role === "user") {
      (async () => {
        setState("loading");
        await fetchResponse();
        setState("idle");
      })();
    } else {
      setState("idle");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSectionId]);

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
        currentSectionId: currentSectionId,
        currentMessages: currentSection.messages instanceof Promise ? [] : currentSection.messages,
        state,
        setState,
        setChatData: onSetChatData,
        setSelectedSection,
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
