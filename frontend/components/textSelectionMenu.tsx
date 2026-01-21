"use client";

import { Button } from "./ui/button";
import { MessageSquareQuoteIcon, StickyNoteIcon } from "lucide-react";
import { Tooltip, TooltipTrigger, TooltipContent } from "./ui/tooltip";
import { TextSelection } from "@/hooks/useTextHighlighting";
import { createPortal } from "react-dom";
import { useEffect, useRef } from "react";

interface TextSelectionMenuProps {
  isOpen: boolean;
  position: { x: number; y: number };
  selection: TextSelection | null;
  onQuote: (text: string) => void;
  onAddToNotes: (selection: TextSelection, notes?: string) => void;
  onClose: () => void;
}

export const TextSelectionMenu = ({
  isOpen,
  position,
  selection,
  onQuote,
  onAddToNotes,
  onClose,
}: TextSelectionMenuProps) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !selection) return null;

  const handleQuote = () => {
    onQuote(selection.text);
    onClose();
  };

  const handleAddToNotes = () => {
    if (selection) {
      onAddToNotes(selection, undefined);
    }
    onClose();
  };

  const menu = (
    <>
      <div
        ref={menuRef}
        className="fixed z-50 rounded-lg shadow-lg bg-background border-accent border"
        style={{
          left: position.x,
          top: position.y,
          transform: "translate(-50%, -120%)",
        }}
      >
        <div className="flex flex-col gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon-lg" onClick={handleQuote}>
                <MessageSquareQuoteIcon />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">
              <p>Quote in reply</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon-lg" onClick={handleAddToNotes}>
                <StickyNoteIcon />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">
              <p>Highlight</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </>
  );

  return createPortal(menu, document.body);
};
