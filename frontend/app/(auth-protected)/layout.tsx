import { getUserSessionFromCookie } from "@/lib/session";
import { redirect } from "next/navigation";

const AuthLayout = async ({ children }: { children: React.ReactNode }) => {
  const session = await getUserSessionFromCookie();
  if (!session) {
    redirect("/login");
  }
  return <>{children}</>;
};
export default AuthLayout;
