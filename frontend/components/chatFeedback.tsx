"use client";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import { FC, useState } from "react";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Spinner } from "./ui/spinner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Field, FieldLabel } from "./ui/field";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";
import { ClientSessionMessage } from "@/lib/db";

type FeedBackDetails = {
  type: "positive" | "negative" | null;
  issueType: string | undefined;
  details: string;
};

type FeedbackState = "idle" | "processing" | "loading" | "submitted" | "error";

const INIT_FEEDBACK = { type: null, details: "", issueType: undefined };

interface ChatFeedbackProps {
  messageId: string;
  feedback: ClientSessionMessage["feedback"];
}

export const ChatFeedback: FC<ChatFeedbackProps> = ({ messageId, feedback: existingFeedback }) => {
  // Initialize state based on existing feedback
  const [state, setState] = useState<FeedbackState>(existingFeedback ? "submitted" : "idle");
  const [openDialog, setOpenDialog] = useState(false);
  const [feedback, setFeedback] = useState<FeedBackDetails>(() => {
    if (existingFeedback) {
      return {
        type: existingFeedback.type,
        details: existingFeedback.details || "",
        issueType: existingFeedback.issueType || undefined,
      };
    }
    return INIT_FEEDBACK;
  });

  const onReview = (newFeedback: NonNullable<FeedBackDetails["type"]>) => {
    // If there's already feedback submitted, allow user to change it
    setFeedback({ ...INIT_FEEDBACK, type: newFeedback });
    setState("processing");
    setOpenDialog(true);
  };

  const onFeedbackChange = (newFeedback: Partial<FeedBackDetails>) => {
    setFeedback((prev) => {
      if (!prev) throw new Error("Something went wrong with giving feedback");
      return { ...prev, ...newFeedback };
    });
  };

  const onSubmit = async () => {
    setState("loading");
    try {
      const response = await fetch("/api/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messageId,
          type: feedback.type,
          issueType: feedback.issueType,
          details: feedback.details,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit feedback");
      }

      setState("submitted");
    } catch (error) {
      setState("error");
      console.error("Error submitting feedback:", error);
    }
  };

  const onClose = () => {
    setOpenDialog(false);
    // If there was existing feedback, restore it when closing without submitting
    if (existingFeedback && state !== "submitted") {
      setFeedback({
        type: existingFeedback.type,
        details: existingFeedback.details || "",
        issueType: existingFeedback.issueType || undefined,
      });
      setState("submitted");
    }
  };

  const isLoading = state === "loading";
  const isSubmitted = state === "submitted";
  const hasError = state === "error";
  const canSubmit =
    feedback.details.trim().length > 0 &&
    (feedback.type === "positive" || (feedback.type === "negative" && feedback.issueType));

  return (
    <Dialog open={openDialog}>
      <div className="flex justify-end p-1">
        <div className="flex gap-2">
          <FeedbackButton
            type="positive"
            state={state}
            feedback={feedback}
            onClick={onReview}
            tooltip="Give positive feedback"
          />
          <FeedbackButton
            type="negative"
            state={state}
            feedback={feedback}
            onClick={onReview}
            tooltip="Give negative feedback"
          />
        </div>
      </div>
      <DialogContent showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>Feedback</DialogTitle>
          <DialogDescription>
            {isSubmitted && "Thank you for your feedback!"}
            {hasError && "Something went wrong. Please try again."}
          </DialogDescription>
        </DialogHeader>
        {!isSubmitted && !hasError && (
          <div className="flex flex-col gap-4">
            {feedback.type === "positive" ? (
              <PositiveFeedback feedback={feedback} onFeedBackChange={onFeedbackChange} />
            ) : (
              <NegativeFeedback feedback={feedback} onFeedBackChange={onFeedbackChange} />
            )}
          </div>
        )}
        <DialogFooter>
          <Button disabled={isLoading} variant="outline" onClick={onClose}>
            Close
          </Button>
          {!isSubmitted && (
            <Button onClick={onSubmit} disabled={isLoading || !canSubmit}>
              {isLoading && <Spinner />}
              Submit
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

interface FeedbackButtonProps {
  onClick: (type: NonNullable<FeedBackDetails["type"]>) => void;
  type: NonNullable<FeedBackDetails["type"]>;
  feedback: FeedBackDetails;
  state: FeedbackState;
  tooltip: string;
}

const FeedbackButton: FC<FeedbackButtonProps> = ({ feedback, type, onClick, tooltip, state }) => {
  const Icon = type === "positive" ? ThumbsUp : ThumbsDown;
  const isSelected = feedback?.type === type && state === "submitted";
  const isDisabled = isSelected;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onClick(type)}
          disabled={isDisabled}
          className={cn({
            "bg-accent": isSelected,
            "disabled:opacity-100": isDisabled,
          })}
        >
          <Icon
            className={cn({
              "text-current": isDisabled,
            })}
          />
        </Button>
      </TooltipTrigger>
      <TooltipContent>{tooltip}</TooltipContent>
    </Tooltip>
  );
};

interface FeedbackProps {
  onFeedBackChange: (newFeedback: Partial<FeedBackDetails>) => void;
  feedback: FeedBackDetails;
}

const PositiveFeedback: FC<FeedbackProps> = ({ onFeedBackChange, feedback }) => {
  return (
    <Field>
      <FieldLabel>Please provide details: </FieldLabel>
      <Textarea
        value={feedback.details}
        onChange={(e) => onFeedBackChange({ details: e.target.value })}
        placeholder="What was satisfying about the response?"
      />
    </Field>
  );
};

const NegativeFeedback: FC<FeedbackProps> = ({ onFeedBackChange, feedback }) => {
  return (
    <>
      <Field>
        <FieldLabel>What was the issue?</FieldLabel>
        <Select
          value={feedback.issueType}
          onValueChange={(value) => onFeedBackChange({ issueType: value })}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Issue type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="incorrect-information">Incorrect Information</SelectItem>
            <SelectItem value="outdated-information">Outdated Information</SelectItem>
            <SelectItem value="incomplete-response">Incomplete Response</SelectItem>
            <SelectItem value="irrelevant-response">Irrelevant Response</SelectItem>
            <SelectItem value="poor-source-quality">Poor Source Quality</SelectItem>
            <SelectItem value="missing-sources">Missing Sources</SelectItem>
            <SelectItem value="search-results-irrelevant">Search Results Irrelevant</SelectItem>
            <SelectItem value="failed-to-access-documents">Failed to Access Documents</SelectItem>
            <SelectItem value="too-verbose">Too Verbose</SelectItem>
            <SelectItem value="too-brief">Too Brief</SelectItem>
            <SelectItem value="poor-formatting">Poor Formatting</SelectItem>
            <SelectItem value="unclear-language">Unclear Language</SelectItem>
            <SelectItem value="misunderstood-context">Misunderstood Context</SelectItem>
            <SelectItem value="lost-context">Lost Context</SelectItem>
            <SelectItem value="failed-to-generate">Failed to Generate</SelectItem>
            <SelectItem value="slow-response">Slow Response</SelectItem>
            <SelectItem value="ui">UI Issue</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      </Field>
      <Field>
        <FieldLabel>Please provide details: </FieldLabel>
        <Textarea
          value={feedback.details}
          onChange={(e) => onFeedBackChange({ details: e.target.value })}
          placeholder="What went wrong with this response?"
        />
      </Field>
    </>
  );
};
