"use client";

import {
  ChangeEventHandler,
  createContext,
  Dispatch,
  SetStateAction,
  use,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Button } from "./ui/button";
import { PenIcon, StickyNoteIcon, XIcon, HighlighterIcon, Trash2Icon } from "lucide-react";
import { Textarea } from "./ui/textarea";
import { useTextHighlightingContext } from "./textHighlightingProvider";
import { HighlightedText } from "@/db/schemas";
import { useParams } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Field, FieldLabel } from "./ui/field";
import { cn } from "@/lib/utils";

interface NotePadContext {
  isOpen: boolean;
  content: string;
  setIsOpen: Dispatch<boolean>;
  setContent: Dispatch<SetStateAction<string>>;
}

const NotePadContext = createContext<NotePadContext | null>(null);

export const useNotePad = () => {
  const ctx = use(NotePadContext);
  if (ctx === null) throw new Error("Provider is missing for notepad");
  return ctx;
};

interface NotePadWrapperProps {
  children: React.ReactNode;
  initNotes: string;
}

export const NotePadWrapper = ({ children, initNotes }: NotePadWrapperProps) => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [isOpen, setIsOpen] = useState(false);
  const [content, setContent] = useState<string>(initNotes);
  const [sidebarWidth, setSidebarWidth] = useState(360);
  const draggingRef = useRef(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);
  const MIN_WIDTH = 280;
  const MAX_WIDTH = 520;
  const previousUserSelectRef = useRef<string | null>(null);

  // Auto-save notes to backend with debouncing
  useEffect(() => {
    if (!sessionId) return;

    const timeoutId = setTimeout(async () => {
      try {
        await fetch(`/api/notes/${sessionId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ notes: content }),
        });
      } catch (error) {
        console.error("Failed to save notes:", error);
      }
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [content, sessionId]);

  const onChange: ChangeEventHandler<HTMLTextAreaElement> = (e) => {
    setContent(e.target.value);
  };

  const onCloseNotes = () => {
    setIsOpen(false);
  };

  const toggleNotePad = () => {
    setIsOpen(!isOpen);
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!draggingRef.current) return;
    const delta = startXRef.current - e.clientX; // drag left to expand
    const next = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidthRef.current + delta));
    setSidebarWidth(next);
  }, []);

  const handleMouseUp = useCallback(
    function onMouseUp() {
      draggingRef.current = false;
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      if (previousUserSelectRef.current !== null) {
        document.body.style.userSelect = previousUserSelectRef.current;
        previousUserSelectRef.current = null;
      }
    },
    [handleMouseMove],
  );

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    draggingRef.current = true;
    startXRef.current = e.clientX;
    startWidthRef.current = sidebarWidth;
    previousUserSelectRef.current = document.body.style.userSelect;
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  };

  const spacerWidth = isOpen ? sidebarWidth : 12; // keep room so overlay never covers content

  return (
    <div className="relative flex size-full">
      <div className="relative flex-1 min-w-0 size-full flex flex-col overflow-hidden">
        {!isOpen && (
          <Button className="absolute top-4 right-4" onClick={toggleNotePad} variant="ghost">
            <PenIcon /> Open Notes
          </Button>
        )}
        {children}
      </div>

      {!isOpen && (
        <button
          type="button"
          onClick={toggleNotePad}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full rounded-l-md bg-card/90 border border-border px-2 py-3 shadow-md hover:bg-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          aria-label="Open notes"
        >
          <div className="w-1 h-10 mx-auto bg-border rounded-full" />
        </button>
      )}

      <div
        style={{ width: spacerWidth, flex: "0 0 auto" }}
        className="transition-all"
        aria-hidden
      />

      <div
        className={cn(
          "absolute inset-y-0 right-0 flex flex-col border-l border-border bg-card/90 shadow-lg backdrop-blur-sm transition-all duration-200 ease-out overflow-hidden",
          isOpen
            ? "translate-x-0 opacity-100 pointer-events-auto"
            : "translate-x-full opacity-0 pointer-events-none",
        )}
        style={{ width: sidebarWidth }}
      >
        <div
          className="absolute left-0 top-0 bottom-0 w-2 cursor-col-resize group"
          onMouseDown={handleMouseDown}
        >
          <div className="mx-auto h-full w-0.5 group-hover:bg-accent transition-colors" />
        </div>

        <div className="flex-1 overflow-hidden">
          <NotePadContent onChange={onChange} onCloseNotes={onCloseNotes} content={content} />
        </div>
      </div>
    </div>
  );
};

interface NotePadContentProps {
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  onCloseNotes: () => void;
  content: string;
}

const NotePadContent = ({ onChange, onCloseNotes, content }: NotePadContentProps) => {
  const { highlightedTexts, navigateToHighlight, deleteHighlight, updateHighlightNotes } =
    useTextHighlightingContext();
  const [editingHighlight, setEditingHighlight] = useState<HighlightedText | null>(null);
  const [editNotes, setEditNotes] = useState("");
  const [deletingHighlightId, setDeletingHighlightId] = useState<string | null>(null);
  const [localHighlightNotes, setLocalHighlightNotes] = useState<Record<string, string>>({});
  const savedNotesRef = useRef<Record<string, string>>({});

  // Initialize local notes state when highlights are loaded
  const initialNotesMap = useMemo(() => {
    const notesMap: Record<string, string> = {};
    highlightedTexts.forEach((highlight) => {
      notesMap[highlight.id] = highlight.notes || "";
    });
    return notesMap;
  }, [highlightedTexts]);

  // Update local state and ref when initial map changes
  useEffect(() => {
    setLocalHighlightNotes((prev) => {
      // Only update if there are actual changes to avoid unnecessary re-renders
      const hasChanges =
        Object.keys(initialNotesMap).some((id) => initialNotesMap[id] !== prev[id]) ||
        Object.keys(prev).length !== Object.keys(initialNotesMap).length;

      if (hasChanges) {
        savedNotesRef.current = initialNotesMap;
        return initialNotesMap;
      }
      return prev;
    });
  }, [initialNotesMap]);

  useEffect(() => {
    const timeoutIds: NodeJS.Timeout[] = [];

    Object.entries(localHighlightNotes).forEach(([highlightId, notes]) => {
      // Only update if the notes have actually changed from what was last saved
      if (savedNotesRef.current[highlightId] !== notes) {
        const timeoutId = setTimeout(async () => {
          await updateHighlightNotes(highlightId, notes);
          // Update the saved notes reference after successful save
          savedNotesRef.current = {
            ...savedNotesRef.current,
            [highlightId]: notes,
          };
        }, 1000);
        timeoutIds.push(timeoutId);
      }
    });

    return () => timeoutIds.forEach((id) => clearTimeout(id));
  }, [localHighlightNotes, updateHighlightNotes]);

  const handleHighlightClick = (highlight: HighlightedText) => {
    navigateToHighlight(highlight);
  };

  const handleDeleteHighlight = async (e: React.MouseEvent, highlightId: string) => {
    e.stopPropagation();
    setDeletingHighlightId(highlightId);
  };

  const confirmDelete = async () => {
    if (deletingHighlightId) {
      await deleteHighlight(deletingHighlightId);
      setDeletingHighlightId(null);
    }
  };

  const cancelDelete = () => {
    setDeletingHighlightId(null);
  };

  const filteredHighlights = useMemo(() => highlightedTexts, [highlightedTexts]);

  const handleSaveNotes = async () => {
    if (editingHighlight) {
      await updateHighlightNotes(editingHighlight.id, editNotes);
      setEditingHighlight(null);
      setEditNotes("");
    }
  };

  const handleCancelEdit = () => {
    setEditingHighlight(null);
    setEditNotes("");
  };

  return (
    <div className="h-full flex flex-col bg-sidebar">
      <div className="flex items-center gap-2 font-medium px-3 py-3 border-b">
        <StickyNoteIcon /> Notes
        <span className="text-xs font-normal text-muted-foreground bg-accent/40 rounded-full px-2 py-0.5">
          Autosaves
        </span>
        <Button className="ml-auto" variant="ghost" size="icon-lg" onClick={onCloseNotes}>
          <XIcon />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-0">
        <div className="space-y-2">
          <div className="px-3 pt-2 pb-1 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
            <PenIcon className="size-4" /> General Notes
          </div>
          <div className="px-3 pb-2">
            <Textarea
              className="resize-none w-full border-0 bg-transparent px-1 py-1 min-h-[110px] focus-visible:ring-1 focus-visible:ring-offset-0"
              onChange={onChange}
              value={content}
              placeholder="Capture takeaways or next steps..."
            />
          </div>

          <div className="px-3 pt-1 pb-0 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
            <HighlighterIcon className="size-4" /> Highlights
          </div>

          {filteredHighlights.map((highlight) => (
            <div key={highlight.id} className="px-3 py-2">
              <div className="flex items-start gap-2">
                <div className="h-full w-1 rounded-sm bg-accent" aria-hidden />
                <button
                  type="button"
                  className="flex-1 text-left flex items-start gap-2 hover:bg-accent/20 rounded-sm px-2 py-1 transition-colors"
                  onClick={() => handleHighlightClick(highlight)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm leading-relaxed font-medium">
                      &quot;{highlight.selectedText}&quot;
                    </p>
                  </div>
                </button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => handleDeleteHighlight(e, highlight.id)}
                  className="size-7 hover:bg-destructive/10 hover:text-destructive"
                >
                  <Trash2Icon className="size-3" />
                </Button>
              </div>
              <Textarea
                value={localHighlightNotes[highlight.id] || ""}
                onChange={(e) =>
                  setLocalHighlightNotes((prev) => ({
                    ...prev,
                    [highlight.id]: e.target.value,
                  }))
                }
                placeholder="Why this matters or what to revisit..."
                className="w-full border-0 bg-transparent px-3 py-2 min-h-[90px] focus-visible:ring-0 focus-visible:ring-offset-0 resize-none"
              />
            </div>
          ))}

          {filteredHighlights.length === 0 && (content?.length ?? 0) === 0 && (
            <div className="py-4 text-center text-muted-foreground">
              <HighlighterIcon className="mx-auto size-8 mb-2 opacity-30" />
              <p className="text-sm font-medium">No notes or highlights yet</p>
              <p className="text-xs mt-1">
                Type notes or select text in AI responses to create highlights
              </p>
            </div>
          )}
        </div>
      </div>

      <Dialog open={!!editingHighlight} onOpenChange={(open) => !open && handleCancelEdit()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Note to Highlight</DialogTitle>
            <DialogDescription>Add or update your note for this highlight</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="p-3 bg-accent/50 rounded border-l-4 border-accent-foreground">
              <p className="text-sm italic leading-relaxed">
                &quot;{editingHighlight?.selectedText}&quot;
              </p>
            </div>
            <Field>
              <FieldLabel>Your Note</FieldLabel>
              <Textarea
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                placeholder="Write your thoughts about this highlight..."
                rows={6}
                className="resize-none"
              />
            </Field>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCancelEdit}>
              Cancel
            </Button>
            <Button onClick={handleSaveNotes}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!deletingHighlightId} onOpenChange={(open) => !open && cancelDelete()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Highlight</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this highlight? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={cancelDelete}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export const NotePadProvider = ({ children }: { children: React.ReactNode }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [content, setContent] = useState("");
  return (
    <NotePadContext value={{ isOpen, setIsOpen, content, setContent }}>{children}</NotePadContext>
  );
};
