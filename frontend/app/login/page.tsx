"use client";
import { useProfileStore } from "@/components/authComponents";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const LoginPage = () => {
  const router = useRouter();
  const loading = useProfileStore((store) => store.loading);
  const isAuthenticated = useProfileStore((store) => store.isAuthenticated);
  const login = useProfileStore((Store) => Store.login);

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/chat-research");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="absolute bg-background z-10 inset-0 left-0 right-0 flex flex-1 justify-center items-center">
      <div className="flex flex-col gap-10 p-10 border-2 rounded-md">
        <div className="font-bold text-2xl">Welcome to CCV Research AI</div>
        <Button size="lg" onClick={login} disabled={isAuthenticated() || loading}>
          Login with Okta {(isAuthenticated() || loading) && <Spinner />}
        </Button>
      </div>
    </div>
  );
};
export default LoginPage;
