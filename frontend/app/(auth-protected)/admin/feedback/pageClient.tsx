"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import type { getAllFeedback, UserWithAccess } from "@/lib/db";

interface AdminFeedbackClientProps {
  feedback: Awaited<ReturnType<typeof getAllFeedback>>;
  users: UserWithAccess[];
}

const formatDate = (value?: number | string | Date | null) => {
  if (!value) return "–";
  const date = typeof value === "number" || typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "–";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
};

const buildSessionLink = (
  sessionId?: string | null,
  sessionType?: string | null
): string | null => {
  if (!sessionId) return null;
  if (sessionType === "apc") return `/apc-research/${sessionId}`;
  return `/chat-research/${sessionId}`;
};

const StatCard = ({ label, value }: { label: string; value: string | number }) => (
  <div className="rounded-lg border bg-card p-4 shadow-sm">
    <div className="text-xs uppercase text-muted-foreground">{label}</div>
    <div className="text-2xl font-semibold">{value}</div>
  </div>
);

const AdminFeedbackClient = ({ feedback, users }: AdminFeedbackClientProps) => {
  const [messageFeedback, setMessageFeedback] = useState(feedback.messageFeedback);
  const [generalFeedback, setGeneralFeedback] = useState(feedback.generalFeedback);
  const [userList, setUserList] = useState(users);
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const adminCount = useMemo(() => userList.filter((user) => user.isAdmin).length, [userList]);

  const handleToggleAdmin = async (userId: string) => {
    const target = userList.find((user) => user.id === userId);
    if (!target) return;
    const nextIsAdmin = !target.isAdmin;

    setSavingUserId(userId);
    setError(null);
    try {
      const response = await fetch(`/api/admin/users/${userId}/roles`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ isAdmin: nextIsAdmin }),
      });

      if (!response.ok) {
        throw new Error(`Failed to update admin access (${response.status})`);
      }

      const data = (await response.json()) as { isAdmin: boolean };
      setUserList((prev) =>
        prev.map((user) => (user.id === userId ? { ...user, isAdmin: data.isAdmin } : user))
      );
    } catch (err) {
      console.error(err);
      setError("Unable to update admin role right now.");
    } finally {
      setSavingUserId(null);
    }
  };

  const refreshFeedback = async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const response = await fetch("/api/admin/feedback");
      if (!response.ok) {
        throw new Error(`Failed to refresh feedback (${response.status})`);
      }
      const data = (await response.json()) as Awaited<ReturnType<typeof getAllFeedback>>;
      setMessageFeedback(data.messageFeedback);
      setGeneralFeedback(data.generalFeedback);
    } catch (err) {
      console.error(err);
      setError("Unable to refresh feedback data.");
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-8 overflow-auto p-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-xs uppercase text-muted-foreground">Admin</p>
          <h1 className="text-2xl font-semibold">Feedback & Access</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={refreshFeedback} disabled={isRefreshing}>
            {isRefreshing ? "Refreshing..." : "Refresh feedback"}
          </Button>
        </div>
      </div>

      {error ? <div className="text-sm text-destructive">{error}</div> : null}

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">User access</h2>
          <span className="text-xs text-muted-foreground">
            Toggle admin without changing their primary role
          </span>
        </div>
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/30">
              <tr>
                <th className="px-3 py-2 text-left">Name</th>
                <th className="px-3 py-2 text-left">Email</th>
                <th className="px-3 py-2 text-left">Primary role</th>
                <th className="px-3 py-2 text-left">Admin access</th>
                <th className="px-3 py-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {userList.map((user) => {
                const isAdmin = user.isAdmin;
                return (
                  <tr key={user.id} className="border-t">
                    <td className="px-3 py-2 font-medium">{user.name}</td>
                    <td className="px-3 py-2">{user.email}</td>
                    <td className="px-3 py-2">{user.role ?? "–"}</td>
                    <td className="px-3 py-2">{isAdmin ? "Admin" : "Standard"}</td>
                    <td className="px-3 py-2">
                      <Button
                        size="sm"
                        variant={isAdmin ? "secondary" : "outline"}
                        onClick={() => handleToggleAdmin(user.id)}
                        disabled={savingUserId === user.id}
                      >
                        {savingUserId === user.id
                          ? "Saving..."
                          : isAdmin
                          ? "Remove admin"
                          : "Make admin"}
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Message feedback</h2>
          <span className="text-xs text-muted-foreground">
            Positive/negative votes attached to chats
          </span>
        </div>
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/30">
              <tr>
                <th className="px-3 py-2 text-left">Submitted</th>
                <th className="px-3 py-2 text-left">User</th>
                <th className="px-3 py-2 text-left">Type</th>
                <th className="px-3 py-2 text-left">Issue</th>
                <th className="px-3 py-2 text-left">Details</th>
                <th className="px-3 py-2 text-left">Message</th>
                <th className="px-3 py-2 text-left">Session</th>
              </tr>
            </thead>
            <tbody>
              {messageFeedback.length === 0 ? (
                <tr>
                  <td className="px-3 py-4 text-center text-muted-foreground" colSpan={7}>
                    No message feedback yet.
                  </td>
                </tr>
              ) : (
                messageFeedback.map((item) => {
                  const link = buildSessionLink(item.sessionId, item.sessionType);
                  return (
                    <tr key={item.id} className="border-t align-top">
                      <td className="px-3 py-2 whitespace-nowrap">{formatDate(item.createdAt)}</td>
                      <td className="px-3 py-2">
                        <div className="font-medium">{item.userName ?? "Unknown"}</div>
                        <div className="text-xs text-muted-foreground">{item.userEmail ?? "–"}</div>
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`rounded-full px-2 py-1 text-xs font-semibold ${
                            item.type === "positive"
                              ? "bg-emerald-500/10 text-emerald-500"
                              : "bg-amber-500/10 text-amber-600"
                          }`}
                        >
                          {item.type}
                        </span>
                      </td>
                      <td className="px-3 py-2">{item.issueType ?? "–"}</td>
                      <td className="px-3 py-2 max-w-[260px] text-sm leading-relaxed">
                        {item.details ?? "–"}
                      </td>
                      <td className="px-3 py-2 max-w-[260px] text-sm leading-relaxed">
                        {item.messageContent ?? "(message removed)"}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {link ? (
                          <Link className="text-primary underline" href={link}>
                            Open
                          </Link>
                        ) : (
                          "–"
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">General feedback</h2>
          <span className="text-xs text-muted-foreground">
            Freeform feedback not tied to a message
          </span>
        </div>
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/30">
              <tr>
                <th className="px-3 py-2 text-left">Submitted</th>
                <th className="px-3 py-2 text-left">User</th>
                <th className="px-3 py-2 text-left">Category</th>
                <th className="px-3 py-2 text-left">Subject</th>
                <th className="px-3 py-2 text-left">Details</th>
              </tr>
            </thead>
            <tbody>
              {generalFeedback.length === 0 ? (
                <tr>
                  <td className="px-3 py-4 text-center text-muted-foreground" colSpan={5}>
                    No general feedback yet.
                  </td>
                </tr>
              ) : (
                generalFeedback.map((item) => (
                  <tr key={item.id} className="border-t align-top">
                    <td className="px-3 py-2 whitespace-nowrap">{formatDate(item.createdAt)}</td>
                    <td className="px-3 py-2">
                      <div className="font-medium">{item.userName ?? "Unknown"}</div>
                      <div className="text-xs text-muted-foreground">{item.userEmail ?? "–"}</div>
                    </td>
                    <td className="px-3 py-2">{item.category ?? "–"}</td>
                    <td className="px-3 py-2 font-medium">{item.subject}</td>
                    <td className="px-3 py-2 max-w-[360px] text-sm leading-relaxed">
                      {item.details}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default AdminFeedbackClient;
