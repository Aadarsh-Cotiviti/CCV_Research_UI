"use client";
import { useChatContext } from "@/components/chatContextProvider";
import { ChatDisplay } from "@/components/chatDisplay";
import { ChatInputBox, ChatInputDisplay } from "@/components/chatInput";
import { FC, useState } from "react";
import { TextHighlightingProvider } from "@/components/textHighlightingProvider";
import { NotePadWrapper } from "@/components/notesPad";
import { HighlightedText } from "@/db/schemas";

interface Props {
  initNotes: string;
  initHighlightedText: HighlightedText[];
}

export const ChatPage: FC<Props> = ({ initNotes, initHighlightedText }) => {
  const [quotedText, setQuotedText] = useState("");

  const handleQuoteInChat = (text: string) => {
    const formattedQuote = `> ${text.replace(/\n/g, "\n> ")}\n`;
    setQuotedText(formattedQuote);
  };
  return (
    <TextHighlightingProvider
      onQuoteInChat={handleQuoteInChat}
      initHighlightedText={initHighlightedText}
    >
      <NotePadWrapper initNotes={initNotes}>
        <ChatDisplay />
        <ChatInputDisplay quotedText={quotedText} onQuotedTextChange={setQuotedText} />
      </NotePadWrapper>
    </TextHighlightingProvider>
  );
};
