import { AddServerMessageFunc, ChatProvider } from "@/components/chatContextProvider";
import { FC } from "react";
import {
  addToChatSessionMessage,
  getClientSession,
  getHighlightsForUser,
  getSessionNotes,
} from "@/lib/db";
import { ChatData } from "@/lib/chat";
import { ChatPage } from "./chatPage";
import { redirect } from "next/navigation";
import { verifySessionCookie } from "@/lib/session";

interface Props {
  params: Promise<{ sessionId: string }>;
}

const Page: FC<Props> = async ({ params }) => {
  const { sessionId } = await params;
  const sessionData = await getClientSession(sessionId);
  if (!sessionData) {
    redirect("/");
  }
  const [notesSession, highlights] = await Promise.all([
    getSessionNotes(sessionId),
    getHighlightsForUser(sessionId),
  ]);
  const addServerMessage: AddServerMessageFunc = async (message, sectionId) => {
    "use server";
    const userJwt = await verifySessionCookie();
    return addToChatSessionMessage(userJwt.uid, sessionId, {
      ...message,
      chatId: sectionId,
    });
  };
  const initData: ChatData = sessionData.sections.map((section) => ({
    messages: section.chat.messages,
    chatId: section.chatId,
    sectionId: String(section.id),
    title: section.title,
  }));

  return (
    <ChatProvider initChatData={initData} addServerMessage={addServerMessage}>
      <ChatPage initNotes={notesSession} initHighlightedText={highlights} />
    </ChatProvider>
  );
};

export default Page;
