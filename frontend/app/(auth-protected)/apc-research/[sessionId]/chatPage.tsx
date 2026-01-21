"use client";

import { useChatContext } from "@/components/chatContextProvider";
import { ChatDisplay, SectionTabDisplay } from "@/components/chatDisplay";
import { ChatInputBox } from "@/components/chatInput";
import { NotePadWrapper } from "@/components/notesPad";
import { TextHighlightingProvider } from "@/components/textHighlightingProvider";
import { HighlightedText } from "@/db/schemas";
import { FC, useState } from "react";

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
        <div className="flex-1 flex flex-col overflow-y-hidden">
          <SectionTabDisplay>
            <ChatDisplay />
          </SectionTabDisplay>
          <div className="py-4 border-t-2 px-8">
            <div className="max-w-5xl mx-auto">
              <ChatInputDisplay quotedText={quotedText} onQuotedTextChange={setQuotedText} />
            </div>
          </div>
        </div>
      </NotePadWrapper>
    </TextHighlightingProvider>
  );
};

const ChatInputDisplay = ({
  quotedText,
  onQuotedTextChange,
}: {
  quotedText: string;
  onQuotedTextChange: (text: string) => void;
}) => {
  const { onChatSubmit } = useChatContext();

  return (
    <ChatInputBox
      onSubmit={onChatSubmit}
      useIconButton
      placeholder="Ask another question"
      initialValue={quotedText}
      onValueChange={onQuotedTextChange}
    />
  );
};
