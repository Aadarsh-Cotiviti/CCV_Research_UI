"use client";

import { createContext, useContext, ReactNode } from "react";
import { useTextHighlighting, TextSelection } from "@/hooks/useTextHighlighting";
import { HighlightedText } from "@/db/schemas";
import { useChatContext } from "./chatContextProvider";

interface TextHighlightingContextType {
  highlightedTexts: HighlightedText[];
  isSelectionMenuOpen: boolean;
  currentSelection: TextSelection | null;
  menuPosition: { x: number; y: number };
  saveHighlight: (selection: TextSelection, notes?: string) => Promise<HighlightedText>;
  deleteHighlight: (highlightId: string) => Promise<void>;
  updateHighlightNotes: (highlightId: string, notes: string) => Promise<HighlightedText>;
  handleTextSelection: (
    event: React.MouseEvent,
    messageContent: string,
    messageId: string,
    sessionId: string,
    sectionId?: number
  ) => void;
  clearSelection: () => void;
  quoteInChat: (text: string) => void;
  navigateToHighlight: (highlight: HighlightedText) => void;
}

const TextHighlightingContext = createContext<TextHighlightingContextType | null>(null);

interface TextHighlightingProviderProps {
  children: ReactNode;
  initHighlightedText: HighlightedText[];
  onQuoteInChat: (text: string) => void;
}

export const TextHighlightingProvider = ({
  children,
  initHighlightedText,
  onQuoteInChat,
}: TextHighlightingProviderProps) => {
  const textHighlighting = useTextHighlighting(initHighlightedText);
  const { setSelectedSection, currentSection } = useChatContext();

  const navigateToHighlight = (highlight: HighlightedText) => {
    // If the highlight belongs to a different section, switch first so the message is present
    if (highlight.sectionId && String(highlight.sectionId) !== currentSection) {
      setSelectedSection(String(highlight.sectionId));
    }

    // Find the message element and scroll to it
    const scrollToMessage = () => {
      const messageElement = document.querySelector(`[data-message-id="${highlight.messageId}"]`);
      if (messageElement) {
        messageElement.scrollIntoView({ behavior: "smooth", block: "center" });

        // Temporarily highlight the message
        messageElement.classList.add("bg-accent", "transition-colors", "duration-1000");
        setTimeout(() => {
          messageElement.classList.remove("bg-accent");
        }, 1000);
      }
    };

    // Wait a frame when switching sections so the DOM has the target message
    requestAnimationFrame(scrollToMessage);
  };

  const value: TextHighlightingContextType = {
    ...textHighlighting,
    quoteInChat: onQuoteInChat,
    navigateToHighlight,
  };

  return (
    <TextHighlightingContext.Provider value={value}>{children}</TextHighlightingContext.Provider>
  );
};

export const useTextHighlightingContext = (): TextHighlightingContextType => {
  const context = useContext(TextHighlightingContext);
  if (!context) {
    throw new Error("useTextHighlightingContext must be used within TextHighlightingProvider");
  }
  return context;
};
