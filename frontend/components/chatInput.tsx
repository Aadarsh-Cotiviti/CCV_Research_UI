"use client";
import { ChevronDownIcon, SendIcon } from "lucide-react";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "./ui/input-group";
import { ChangeEventHandler, FC, KeyboardEventHandler, useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "./ui/dropdown-menu";
import { DropdownMenuTrigger } from "@radix-ui/react-dropdown-menu";
import { Spinner } from "./ui/spinner";
import { ResponsesModel } from "openai/resources/shared.mjs";
import { AVAILABLE_MODELS } from "@/lib/llm";
import { useProfileStore } from "./authComponents";
import { useChatContext } from "./chatContextProvider";

export type SubmitHandler = (content: string, model: ResponsesModel) => Promise<void>;

interface ChatInputProps {
  onSubmit: SubmitHandler;
  useIconButton?: boolean;
  canSelectModel?: boolean;
  dropdowns?: React.ReactNode;
  placeholder?: string;
  className?: React.HTMLAttributes<HTMLDivElement>["className"];
  sendText?: string;
  initialValue?: string;
  onValueChange?: (value: string) => void;
}

export const ChatInputBox: FC<ChatInputProps> = ({
  onSubmit,
  useIconButton,
  className,
  canSelectModel,
  dropdowns,
  placeholder,
  sendText,
  initialValue = "",
  onValueChange,
}) => {
  const [messageContent, setMessageContent] = useState(initialValue);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ResponsesModel>(AVAILABLE_MODELS[0]);

  useEffect(() => {
    setMessageContent(initialValue);
  }, [initialValue]);
  const onMessageContentChange: ChangeEventHandler<HTMLTextAreaElement> = (e) => {
    setMessageContent(e.target.value);
    onValueChange?.(e.target.value);
  };

  const onKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const onSend = async () => {
    setLoading(true);
    await onSubmit(messageContent, selectedModel);
    setMessageContent("");
    setLoading(false);
  };

  const Icon = loading ? Spinner : SendIcon;

  return (
    <div
      className={cn("text-left shrink-0  max-w-5xl w-full mx-auto py-5 bg-background", className)}
    >
      <InputGroup className="h-full">
        <InputGroupTextarea
          className="min-h-4"
          placeholder={placeholder}
          disabled={loading}
          value={messageContent}
          onKeyDown={onKeyDown}
          onChange={onMessageContentChange}
        />
        <InputGroupAddon className="py-2" align="block-end">
          {canSelectModel && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <InputGroupButton variant="outline">
                  {selectedModel} <ChevronDownIcon />
                </InputGroupButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuLabel>Chat Models</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {AVAILABLE_MODELS.map((model) => (
                  <DropdownMenuItem onClick={() => setSelectedModel(model)} key={model}>
                    {model}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {dropdowns}
          <InputGroupButton
            disabled={loading}
            onClick={onSend}
            variant="default"
            className="rounded ml-auto cursor-pointer"
            size="sm"
          >
            {useIconButton ? (
              <Icon />
            ) : (
              <>
                <Icon /> {sendText ? sendText : "Send"}
              </>
            )}
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
      <span className="text-muted-foreground text-xs">
        Press Enter to send, Shift+Enter for new line{" "}
      </span>
    </div>
  );
};
export const ChatInputDisplay = ({
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
