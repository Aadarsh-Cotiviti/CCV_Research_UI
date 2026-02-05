import { ChatInputBox, SubmitHandler } from "@/components/chatInput";
import { Item, ItemContent, ItemMedia, ItemTitle } from "@/components/ui/item";
import type { MessageInsert } from "@/db/schemas";
import { createChatSession } from "@/lib/db";
import { getSessionToken } from "@/lib/session";
import { SearchIcon } from "lucide-react";
import { redirect } from "next/navigation";
import { FC } from "react";

const Page = () => {
  const onSubmit: SubmitHandler = async (input, model) => {
    "use server";
    const jwtUserData = await getSessionToken();
    const messages: Omit<MessageInsert, "sectionId">[] = [
      {
        role: "system",
        content: "You are a helpful assistant with the persona of a CCV Researcher.",
      },
      {
        role: "user",
        modelUsed: model,
        content: input,
      },
    ];
    const session = await createChatSession(jwtUserData.uid, messages);
    redirect(`/chat-research/${session.id}`);
  };

  return (
    <div className="flex-1">
      <div className="flex flex-col items-center gap-4 max-w-3xl text-center mx-auto mt-[10%] mb-4 ">
        <h3 className="text-3xl w-fit font-medium">Start New Research</h3>
        <div className="h-34 flex w-full">
          <ChatInputBox onSubmit={onSubmit} placeholder="Search" canSelectModel />
        </div>
      </div>
      {/* <div className="flex flex-col justify-center items-center w-full gap-3">
        <StarterPrompt prompt="Prompt 1" />
        <StarterPrompt prompt="Prompt 2" />
        <StarterPrompt prompt="Prompt 3" />
      </div> */}
    </div>
  );
};

interface StarterProps {
  prompt: string;
}

const StarterPrompt: FC<StarterProps> = ({ prompt }) => {
  return (
    <Item variant="outline" className="w-full max-w-lg cursor-pointer">
      <ItemMedia>
        <SearchIcon />
      </ItemMedia>
      <ItemContent>
        <ItemTitle>{prompt}</ItemTitle>
      </ItemContent>
    </Item>
  );
};

export default Page;
