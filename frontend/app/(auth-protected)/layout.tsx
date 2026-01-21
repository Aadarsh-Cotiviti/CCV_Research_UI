import { getSessionPayloadFromCookie } from "@/lib/session";
import { redirect } from "next/navigation";

const AuthLayout = async ({ children }: { children: React.ReactNode }) => {
  const payload = await getSessionPayloadFromCookie();
  if (!payload) {
    redirect("/login");
  }
  return <>{children}</>;
};
export default AuthLayout;
