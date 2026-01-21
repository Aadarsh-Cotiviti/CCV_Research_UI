"use client";

import { useProfileStore } from "@/components/authComponents";
import { Spinner } from "@/components/ui/spinner";
import { FC, useEffect } from "react";
import { useRouter } from "next/navigation";

const OktaCallbackPage: FC = () => {
  const authenticate = useProfileStore((store) => store.authenticate);
  const router = useRouter();
  useEffect(() => {
    const processAuth = async () => {
      const success = await authenticate();

      if (success) {
        router.replace("/chat-research");
      } else {
        router.replace("/login");
      }
    };
    processAuth();
  }, [authenticate, router]);
  return (
    <div className="absolute bg-background z-10 left-0 top-0 inset-0 flex flex-col justify-center items-center gap-4">
      Processing authentication...
      <Spinner className="size-10" />
    </div>
  );
};

export default OktaCallbackPage;
