"use client";

import { useState, useCallback } from "react";
import { HighlightedText, HighlightedTextInsert } from "@/db/schemas";

export interface TextSelection {
  text: string;
  startOffset: number;
  endOffset: number;
  contextBefore: string;
  contextAfter: string;
  messageId: string;
  sectionId?: number;
  sessionId: string;
}

export const useTextHighlighting = (initHighlightText: HighlightedText[] = []) => {
  const [highlightedTexts, setHighlightedTexts] = useState<HighlightedText[]>(initHighlightText);
  const [isSelectionMenuOpen, setIsSelectionMenuOpen] = useState(false);
  const [currentSelection, setCurrentSelection] = useState<TextSelection | null>(null);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });

  const saveHighlight = useCallback(
    async (selection: TextSelection, notes?: string): Promise<HighlightedText> => {
      const highlightData: Omit<HighlightedTextInsert, "userId"> = {
        messageId: selection.messageId,
        sectionId: selection.sectionId ?? null,
        sessionId: selection.sessionId,
        selectedText: selection.text,
        contextBefore: selection.contextBefore,
        contextAfter: selection.contextAfter,
        startOffset: selection.startOffset,
        endOffset: selection.endOffset,
        notes: notes || null,
      };

      const response = await fetch("/api/highlights", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(highlightData),
      });

      if (!response.ok) {
        throw new Error("Failed to save highlight");
      }

      const savedHighlight = await response.json();
      setHighlightedTexts((prev) => [...prev, savedHighlight]);
      return savedHighlight;
    },
    []
  );

  const deleteHighlight = useCallback(async (highlightId: string) => {
    const response = await fetch(`/api/highlights/${highlightId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      setHighlightedTexts((prev) => prev.filter((h) => h.id !== highlightId));
    }
  }, []);

  const updateHighlightNotes = useCallback(async (highlightId: string, notes: string) => {
    const response = await fetch(`/api/highlights/${highlightId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ notes }),
    });

    if (!response.ok) {
      throw new Error("Failed to update highlight notes");
    }

    const updatedHighlight = await response.json();
    setHighlightedTexts((prev) => prev.map((h) => (h.id === highlightId ? updatedHighlight : h)));
    return updatedHighlight;
  }, []);

  const handleTextSelection = useCallback(
    (
      event: React.MouseEvent,
      messageContent: string,
      messageId: string,
      sessionId: string,
      sectionId?: number
    ) => {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || !selection.rangeCount) {
        setIsSelectionMenuOpen(false);
        return;
      }

      const selectedText = selection.toString().trim();
      if (selectedText.length === 0) {
        setIsSelectionMenuOpen(false);
        return;
      }

      const range = selection.getRangeAt(0);
      const startOffset = range.startOffset;
      const endOffset = range.endOffset;

      // Get context around the selection
      const contextLength = 50;
      const contextBefore = messageContent.substring(
        Math.max(0, startOffset - contextLength),
        startOffset
      );
      const contextAfter = messageContent.substring(
        endOffset,
        Math.min(messageContent.length, endOffset + contextLength)
      );

      setCurrentSelection({
        text: selectedText,
        startOffset,
        endOffset,
        contextBefore,
        contextAfter,
        messageId,
        sessionId,
        sectionId,
      });

      setMenuPosition({
        x: event.clientX,
        y: event.clientY,
      });

      setIsSelectionMenuOpen(true);
    },
    []
  );

  const clearSelection = useCallback(() => {
    setIsSelectionMenuOpen(false);
    setCurrentSelection(null);
    if (window.getSelection) {
      window.getSelection()?.removeAllRanges();
    }
  }, []);

  return {
    highlightedTexts,
    isSelectionMenuOpen,
    currentSelection,
    menuPosition,
    saveHighlight,
    deleteHighlight,
    updateHighlightNotes,
    handleTextSelection,
    clearSelection,
  };
};
