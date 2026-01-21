"use client";

import { useApcState } from "./apcContext";
import { AdditionalContextPage, ChatBoxInputPage, SelectCPTCodePage } from "./steps";

const STEPS = [ChatBoxInputPage, SelectCPTCodePage, AdditionalContextPage];

export const APCPage = () => {
  const { step } = useApcState();

  const StepComponent = STEPS[step];

  return (
    <div className="max-w-3xl w-full mx-auto mt-[10%]">
      <StepComponent />
    </div>
  );
};
