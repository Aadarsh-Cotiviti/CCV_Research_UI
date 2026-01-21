"use client";
import { ArrowUpIcon } from "lucide-react";
import { PanelHeader } from "./panelHeader";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "./ui/input-group";
import { FC } from "react";
import { useChatContext } from "./chatContextProvider";
import { cn } from "@/lib/utils";
import { Message } from "@/db/schemas";

export const ChatBox: FC = ({}) => {
  const { currentMessages } = useChatContext();

  return (
    <div className="h-svh bg-card flex flex-col">
      <PanelHeader title="Chat" subTitle="Iterate and refine your search" />
      <div className="flex-1 flex flex-col p-4 gap-4">
        {currentMessages.map((msg) => (
          <MessageTypes key={msg.id} message={msg} />
        ))}
      </div>
      <div className="flex flex-col gap-2 border-0 border-t p-4">
        <InputGroup className="">
          <InputGroupTextarea placeholder="Ask another question" className="min-h-8 " />
          <InputGroupAddon align="inline-end" className=" self-end">
            <InputGroupButton variant="default" className="rounded cursor-pointer" size="icon-sm">
              <ArrowUpIcon />
            </InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
      </div>
    </div>
  );
};

interface MessageProps {
  message: Message;
}

const MessageTypes: FC<MessageProps> = ({ message }) => {
  const { role, content, createdAt } = message;

  const isAssistant = role === "assistant";
  return (
    <div
      className={cn("w-full flex flex-col", {
        "items-start": isAssistant,
        "items-end": !isAssistant,
      })}
    >
      <div
        className={cn("max-w-[85%]  p-4 rounded-lg outline-2", {
          "bg-muted cursor-pointer rounded-tl-xs": isAssistant,
          "bg-primary text-primary-foreground rounded-tr-xs": !isAssistant,
        })}
      >
        {content}
      </div>
      <div
        className={cn("text-muted-foreground text-sm", {
          "text-end": !isAssistant,
        })}
      >
        {new Date(createdAt ?? 0).toLocaleTimeString(undefined, {
          hour: "numeric",
          minute: "numeric",
        })}
      </div>
    </div>
  );
};
