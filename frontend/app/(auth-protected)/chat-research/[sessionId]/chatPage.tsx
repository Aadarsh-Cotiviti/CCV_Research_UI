"use client";
import { useChatContext } from "@/components/chatContextProvider";
import { ChatDisplay } from "@/components/chatDisplay";
import { ChatInputBox } from "@/components/chatInput";
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
        <div className="py-4 border-t-2 px-8">
          <div className="max-w-4xl mx-auto">
            <ChatInputDisplay quotedText={quotedText} onQuotedTextChange={setQuotedText} />
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
