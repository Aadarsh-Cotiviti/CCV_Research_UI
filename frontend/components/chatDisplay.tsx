"use client";

import { useChatContext } from "./chatContextProvider";
import { useParams } from "next/navigation";
import { DocumentLink } from "./documentLink";
import { FileIcon } from "lucide-react";
import { ChatFeedback } from "./chatFeedback";
import { FC, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { markdownComponents } from "./MarkdownComponents";
import { ClientSessionMessage } from "@/lib/db";
import { useTextHighlightingContext } from "./textHighlightingProvider";
import { TextSelectionMenu } from "./textSelectionMenu";
import { TextSelection } from "@/hooks/useTextHighlighting";
export const ChatDisplay = () => {
  const { currentMessages, aiResponse, loading } = useChatContext();
  const {
    isSelectionMenuOpen,
    currentSelection,
    menuPosition,
    quoteInChat,
    saveHighlight,
    clearSelection,
  } = useTextHighlightingContext();
  const lastUserMessageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll the last user message to the top of the view
    const lastMsg = currentMessages.at(-1);
    if (lastMsg?.role === "user" && lastUserMessageRef.current) {
      lastUserMessageRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
        inline: "nearest",
      });
    }
  }, [currentMessages]);

  const handleAddToNotes = async (selection: TextSelection, notes?: string) => {
    await saveHighlight(selection, notes);
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="mx-auto flex flex-col overflow-y-auto items-start max-w-5xl">
        {currentMessages.map((message, index) => {
          const isLastUserMessage = message.role === "user" && index === currentMessages.length - 1;

          return message.role === "user" ? (
            <div key={message.id} ref={isLastUserMessage ? lastUserMessageRef : null}>
              <UserMessage data={message} />
            </div>
          ) : (
            <AssistantMessage key={message.id} data={message} />
          );
        })}
        {loading && aiResponse === "" && (
          <div className="flex gap-2 mt-4">
            <div className="animate-bounce size-4 bg-accent rounded-full"></div>
            <div className="animate-bounce delay-[150ms] size-4 bg-accent rounded-full"></div>
            <div className="animate-bounce delay-[300ms] size-4 bg-accent rounded-full"></div>
          </div>
        )}
        {aiResponse && (
          <AssistantMessage
            data={{
              content: aiResponse,
              createdAt: new Date(),
              documents: null,
              id: crypto.randomUUID(),
              modelUsed: "",
              role: "assistant",
              chatId: "",
              feedback: null,
              feedbackId: null,
            }}
          />
        )}
      </div>
      <div className="pb-[100svh]" />

      <TextSelectionMenu
        isOpen={isSelectionMenuOpen}
        position={menuPosition}
        selection={currentSelection}
        onQuote={quoteInChat}
        onAddToNotes={handleAddToNotes}
        onClose={clearSelection}
      />
    </div>
  );
};

const Icon = ({ children }: { children: React.ReactNode }) => {
  return (
    <span className="flex items-center justify-center rounded-full size-10 shrink-0 bg-background">
      {children}
    </span>
  );
};

const AssistantMessage = ({ data }: { data: ClientSessionMessage }) => {
  const { handleTextSelection } = useTextHighlightingContext();
  const { sessionId } = useParams<{ sessionId: string }>();
  const { currentSection } = useChatContext();
  const documents = data.documents;

  const handleMouseUp = (event: React.MouseEvent) => {
    if (!sessionId) return;
    const sectionNumeric = Number(currentSection);
    const sectionId = Number.isFinite(sectionNumeric) ? sectionNumeric : undefined;
    handleTextSelection(event, data.content, data.id, sessionId, sectionId);
  };

  return (
    <div className="flex gap-2 mt-4 w-full">
      <div className="flex flex-col w-full">
        <div
          className="px-0 rounded-sm select-text cursor-text"
          onMouseUp={handleMouseUp}
          data-message-id={data.id}
        >
          <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {data.content}
          </Markdown>
        </div>
        <ChatFeedback feedback={data.feedback} messageId={data.id} />
        {documents && (
          <div>
            <span className="mb-2 flex gap-2 items-center text-sm text-muted-foreground">
              <FileIcon className="size-4" /> 2 sources
            </span>
            <div className="flex gap-2">
              {documents.map((doc) => (
                <DocumentLink key={doc.title} data={doc} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const UserMessage = ({ data }: { data: ClientSessionMessage }) => {
  return (
    <div className="flex gap-2 items-center bg-muted rounded p-2 px-4 mt-4">
      <Icon>You</Icon>
      <div className="flex flex-col">
        <p className="whitespace-pre-wrap">{data.content}</p>
        <span className="text-xs text-muted-foreground">
          {new Date(data.createdAt).toLocaleTimeString(undefined, {
            hour: "numeric",
            minute: "numeric",
          })}
        </span>
      </div>
    </div>
  );
};

interface SectionSelectorProps {
  children: React.ReactNode;
}

export const SectionTabDisplay: FC<SectionSelectorProps> = ({ children }) => {
  const { currentSection: selectedSection, setSelectedSection, chatData } = useChatContext();

  return (
    <div className="flex flex-1 flex-col max-w-5xl mx-auto px-6 [&>div:nth-child(2)]:p-0 overflow-y-auto">
      <div className="w-full gap-2 grid grid-cols-7 py-4">
        {chatData.map((data) => (
          <div
            key={data.sectionId}
            className={cn("px-4 py-4 text-center text-xs cursor-pointer hover:bg-muted", {
              "border-b-2": data.sectionId === selectedSection,
            })}
            onClick={() => setSelectedSection(data.sectionId)}
          >
            {data.title}
          </div>
        ))}
      </div>
      {children}
    </div>
  );
};
