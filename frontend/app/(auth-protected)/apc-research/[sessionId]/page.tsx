import { AddServerMessageFunc, ChatProvider } from "@/components/chatContextProvider";
import { FC } from "react";
import {
  addMessageToChatSession,
  getClientSession,
  getHighlightsForUser,
  getSessionNotes,
} from "@/lib/db";
import { ChatData } from "@/lib/chat";
import { ChatPage } from "./chatPage";
import { redirect } from "next/navigation";
import { getSessionToken } from "@/lib/session";
import { runSection } from "@/lib/backendClient";

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
  const addServerMessage: AddServerMessageFunc = async (message, sessionId) => {
    "use server";
    const userJwt = await getSessionToken();
    return addMessageToChatSession(userJwt.uid, sessionId, message);
  };

  const initData: ChatData = sessionData.sections.map((section, i) => {
    const fetchSection = async () => {
      const resp = await runSection(i, {
        cpt: sessionData.metadata.cpt,
        model: sessionData.metadata.initialModel,
        use_cache: true,
        context: "",
      });
      if (resp.error) {
        throw new Error(`Error fetching section data: ${resp.error}`);
      }
      const messages = await addMessageToChatSession(sessionData.userId, sessionId, {
        content: JSON.stringify(resp.data),
        role: "assistant",
        sectionId: section.id,
      });
      return [messages];
    };
    return {
      messages: section.messages.length > 0 ? section.messages : fetchSection(),
      sectionId: section.id,
      title: section.title,
    };
  });

  return (
    <ChatProvider initChatData={initData} addServerMessage={addServerMessage}>
      <ChatPage initNotes={notesSession} initHighlightedText={highlights} />
    </ChatProvider>
  );
};

export default Page;
