"use client";
import { ButtonHTMLAttributes, createContext, Dispatch, FC, use, useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowBigLeftIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { type CptData } from "@/app/(auth-protected)/apc-research/server-actions";

interface ApcData {
  topic: string;
  selectedCpt: CptData | null;
  cptOptions: CptData[] | null;
  additionalContext: string;
  chosenModel: string;
}

interface ApcState {
  step: number;
  data: ApcData;
  setStep: Dispatch<number>;
  setData: Dispatch<ApcData>;
}

const INIT_APC_DATA = {
  topic: "",
  additionalContext: "",
  selectedCpt: null,
  cptOptions: null,
  chosenModel: "gpt-4.1",
};

const apcContext = createContext<ApcState>({
  data: INIT_APC_DATA,
  step: 0,
  setStep() {},
  setData() {},
});

export const ApcContextProvider = ({ children }: { children: React.ReactNode }) => {
  const [data, setData] = useState<ApcState["data"]>(INIT_APC_DATA);
  const [step, setStep] = useState(0);

  return (
    <apcContext.Provider value={{ data, step, setStep, setData }}>{children}</apcContext.Provider>
  );
};

export const useApcState = () => {
  const apcState = use(apcContext);
  if (apcState === undefined) throw new Error("APC context is missing!");
  return apcState;
};

export const BackStepButton = () => {
  const { setStep, step } = useApcState();

  const stepBack = () => {
    setStep(step - 1);
  };

  return (
    <Button variant="outline" size="lg" onClick={stepBack}>
      <ArrowBigLeftIcon /> Back
    </Button>
  );
};

export const NextStepButton: FC<ButtonHTMLAttributes<HTMLButtonElement>> = (props) => {
  const { setStep, step } = useApcState();

  const stepForward = () => {
    setStep(step + 1);
  };

  return (
    <Button size="lg" onClick={stepForward} {...props}>
      Next
    </Button>
  );
};

export const StartResearchButton: FC<ButtonHTMLAttributes<HTMLButtonElement>> = (props) => {
  const router = useRouter();
  const { data } = useApcState();
  const onClick = async () => {
    if (data.selectedCpt === null) return;
    const response = await fetch("/api/create-research", {
      method: "POST",
      body: JSON.stringify({
        targetCpt: data.selectedCpt,
        contextDetails: data.additionalContext,
        model: data.chosenModel,
      }),
    });

    const { id } = await response.json();
    const url = `/apc-research/${id}`;
    router.replace(url);
  };

  return (
    <Button size="lg" className="flex-1" onClick={onClick} {...props}>
      Start Research
    </Button>
  );
};
