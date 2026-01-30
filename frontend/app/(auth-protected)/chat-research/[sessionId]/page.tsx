import { FC } from "react";
import {
  addMessageToChatSession,
  getClientSession,
  getHighlightsForUser,
  getSessionNotes,
} from "@/lib/db";
import { ChatData } from "@/lib/chat";
import { redirect } from "next/navigation";
import { ChatPage } from "./chatPage";
import { AddServerMessageFunc, ChatProvider } from "@/components/chatContextProvider";
import { getSessionToken } from "@/lib/session";

interface Props {
  params: Promise<{ sessionId: string }>;
}

const Page: FC<Props> = async ({ params }) => {
  const { sessionId } = await params;

  const chatSession = await getClientSession(sessionId);
  const [notesSession, highlights] = await Promise.all([
    getSessionNotes(sessionId),
    getHighlightsForUser(sessionId),
  ]);
  if (!chatSession) {
    redirect("/");
  }
  const primarySection = chatSession.sections[0];
  if (!primarySection) {
    redirect("/");
  }
  const chatdata: ChatData = [
    {
      messages: primarySection.messages,
      sectionId: String(primarySection.id),
    },
  ];

  const addMessage: AddServerMessageFunc = async (message, currentSectionId) => {
    "use server";

    const userJwt = await getSessionToken();
    return addMessageToChatSession(userJwt.uid, sessionId, {
      ...message,
      sectionId: currentSectionId,
    });
  };

  return (
    <ChatProvider initChatData={chatdata} addServerMessage={addMessage}>
      <ChatPage initNotes={notesSession} initHighlightedText={highlights} />
    </ChatProvider>
  );
};

export default Page;
