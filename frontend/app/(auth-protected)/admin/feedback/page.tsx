import { getAllFeedback, getAllUsersWithAccess } from "@/lib/db";
import { getSessionPayloadFromCookie } from "@/lib/session";
import { redirect } from "next/navigation";
import AdminFeedbackClient from "./pageClient";

const AdminFeedbackPage = async () => {
  const session = await getSessionPayloadFromCookie();
  if (!session || session.isAdmin !== true) {
    redirect("/chat-research");
  }

  const [feedback, users] = await Promise.all([getAllFeedback(), getAllUsersWithAccess()]);

  return <AdminFeedbackClient feedback={feedback} users={users} />;
};

export default AdminFeedbackPage;
