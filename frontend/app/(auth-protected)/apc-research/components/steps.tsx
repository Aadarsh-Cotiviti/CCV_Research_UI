"use client";
import { ChatInputBox, SubmitHandler } from "../../../../components/chatInput";
import { Field, FieldLabel } from "../../../../components/ui/field";
import {
  Item,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemTitle,
} from "../../../../components/ui/item";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../../components/ui/select";
import { Textarea } from "../../../../components/ui/textarea";
import { BackStepButton, NextStepButton, StartResearchButton, useApcState } from "./apcContext";
import { FC } from "react";
import type { CptData } from "@/app/(auth-protected)/apc-research/server-actions";
import { AVAILABLE_MODELS } from "@/lib/llm";

export const ChatBoxInputPage = () => {
  const { setStep, step, setData, data: prevData } = useApcState();
  const onSubmitChat: SubmitHandler = async (topic, model) => {
    const resp = await fetch("/api/cpt-codes", {
      method: "POST",
      body: JSON.stringify({
        topic,
        model,
      }),
    });
    const data = (await resp.json()) as CptData[];
    setStep(step + 1);
    setData({
      ...prevData,
      cptOptions: data,
      additionalContext: `Related to ${topic}`,
    });
  };

  return (
    <div className="flex-1 flex flex-col items-center gap-4">
      <h3 className="text-3xl w-fit font-medium text-center">APC Target Code Research</h3>
      <h2 className="text-lg w-fit text-center">Enter Topic and Generate CPT Codes</h2>
      <div className="flex w-full h-34">
        <ChatInputBox
          onSubmit={onSubmitChat}
          placeholder="e.g., Bronchial Biopsy, Knee Replacement, Cardiac Catheterization"
          canSelectModel
          sendText="Generate"
        />
      </div>
    </div>
  );
};

export const SelectCPTCodePage = () => {
  const { setData, data } = useApcState();

  const onItemClick = (newData: CptData) => {
    setData({ ...data, selectedCpt: newData });
  };

  return (
    <div className="border p-4 rounded">
      <h2 className="text-2xl mb-4">Select a CPT Code</h2>
      <p className="text-muted-foreground mb-2">Choose CPT code relevant to your research</p>
      <ItemGroup className="gap-4">
        {data.cptOptions?.map((cptData) => (
          <CPTDataDisplay
            key={cptData.code}
            data={cptData}
            onClick={onItemClick}
            selected={cptData.code === data.selectedCpt?.code}
          />
        ))}
      </ItemGroup>
      <div className="w-full flex gap-4 justify-end mt-6">
        <BackStepButton />
        <NextStepButton disabled={data.selectedCpt === null} />
      </div>
    </div>
  );
};

interface CPTDataDisplay {
  data: CptData;
  onClick: (data: CptData) => void;
  selected: boolean;
}

const CPTDataDisplay: FC<CPTDataDisplay> = ({ data, onClick, selected }) => {
  return (
    <Item
      onClick={() => onClick(data)}
      className="cursor-pointer"
      variant={selected ? "muted" : "outline"}
    >
      <div className="p-2 bg-accent rounded">{data.code}</div>
      <ItemContent>
        <ItemTitle>{data.title}</ItemTitle>
        <ItemDescription>{data.description}</ItemDescription>
      </ItemContent>
    </Item>
  );
};

export const AdditionalContextPage = () => {
  const { data, setData } = useApcState();
  return (
    <div className="grid gap-4 w-full p-4 border rounded">
      <Field>
        <FieldLabel>Additional Context</FieldLabel>
        <Textarea
          value={data.additionalContext}
          onChange={(e) => setData({ ...data, additionalContext: e.target.value })}
        />
      </Field>
      <Field>
        <FieldLabel>Analysis Model</FieldLabel>
        <Select
          value={data.chosenModel}
          onValueChange={(value) => setData({ ...data, chosenModel: value })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {AVAILABLE_MODELS.map((model) => (
              <SelectItem key={model} value={model}>
                {model}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Field>
      <div className="w-full flex gap-4 justify-end mt-6">
        <BackStepButton />
        <StartResearchButton />
      </div>
    </div>
  );
};
