import { ExternalLinkIcon } from "lucide-react";
import { Item, ItemActions, ItemContent, ItemTitle } from "./ui/item";
import { FC } from "react";
import { DocumentData } from "@/db/schemas";

export const DocumentLink: FC<{ data: DocumentData }> = ({ data }) => {
  return (
    <Item variant="outline" size="sm" asChild>
      <a href={data.url} target="_blank" rel="noopener noreferrer">
        <ItemContent>
          <ItemTitle className="flex justify-between w-full">
            <p>{data.title}</p>
          </ItemTitle>
          {/* <ItemDescription>
                    {data.relevance}% relevance
                </ItemDescription> */}
        </ItemContent>
        <ItemActions>
          <ExternalLinkIcon className="size-4 text-muted-foreground" />
        </ItemActions>
      </a>
    </Item>
  );
};
