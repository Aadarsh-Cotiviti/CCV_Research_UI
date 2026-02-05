"use client";

import { ChatDisplay, SectionTabDisplay } from "@/components/chatDisplay";
import { ChatInputDisplay } from "@/components/chatInput";
import { NotePadWrapper } from "@/components/notesPad";
import { TextHighlightingProvider } from "@/components/textHighlightingProvider";
import { HighlightedText } from "@/db/schemas";
import { FC, useState } from "react";
import { sectionRenderers } from "../components/sectionRenders";

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
        <SectionTabDisplay initialPageRender={sectionRenderers}>
          <ChatDisplay />
        </SectionTabDisplay>
        <ChatInputDisplay quotedText={quotedText} onQuotedTextChange={setQuotedText} />
      </NotePadWrapper>
    </TextHighlightingProvider>
  );
};
