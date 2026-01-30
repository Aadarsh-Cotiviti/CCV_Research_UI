"use client";
import {
  BuildingIcon,
  LucideIcon,
  MessageCircleIcon,
  PlusIcon,
  ShieldCheckIcon,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "../ui/sidebar";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "../ui/button";
import { useEffect, useRef, useState } from "react";

import { DisplayChatHistory, DisplayChatHistoryLoading } from "./NavChatHistory";
import { useProfileStore } from "../authComponents";
import Link from "next/link";
import { GeneralFeedbackDialog } from "../generalFeedback";

interface NavLinks {
  title: string;
  url: string;
  icon?: LucideIcon;
}

const navigationLinks: NavLinks[] = [
  {
    title: "Chat Research",
    url: "/chat-research",
    icon: MessageCircleIcon,
  },
  {
    title: "APC Research",
    url: "/apc-research",
    icon: BuildingIcon,
  },
];

export const AppSidebar = () => {
  const path = usePathname();
  const router = useRouter();
  const chatHistories = useProfileStore((store) => store.chatSessions);
  const loading = useProfileStore((store) => store.loading);
  const refreshChatHistory = useProfileStore((store) => store.refreshChatHistory);
  const isAdmin = useProfileStore((store) => store.userProfile?.isAdmin === true);
  const [, initialPath, chatId] = path.split("/");
  const isChatPage = initialPath === "chat-research" || initialPath === "apc-research";
  const previousChatIdRef = useRef<string | undefined>(undefined);
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);

  useEffect(() => {
    if (!isChatPage) return;
    if (chatId && chatId !== previousChatIdRef.current) {
      const currentChatExists = chatHistories.some((chat) => chat.id === chatId);

      if (!currentChatExists && !loading) {
        refreshChatHistory();
      }

      previousChatIdRef.current = chatId;
    }
  }, [chatId, chatHistories, isChatPage, loading, refreshChatHistory]);

  const onCreateNewChat = () => {
    router.push(`/${initialPath}`);
  };

  const handleChatUpdate = () => {
    refreshChatHistory();
  };

  const chatHistory = chatHistories.filter((sessions) => sessions.type === "chat");
  const apcChat = chatHistories.filter((session) => session.type === "apc");

  const chatLinks =
    initialPath === "chat-research" ? chatHistory : initialPath === "apc-research" ? apcChat : [];

  return (
    <Sidebar>
      <SidebarHeader className="justify-center items-center"></SidebarHeader>
      <SidebarContent>
        {chatId != null && isChatPage && (
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Button onClick={onCreateNewChat} variant="default" size="lg">
                    <PlusIcon /> New Chat
                  </Button>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {(isAdmin
                ? [
                    ...navigationLinks,
                    { title: "Admin", url: "/admin/feedback", icon: ShieldCheckIcon },
                  ]
                : navigationLinks
              ).map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton isActive={path.startsWith(item.url)} asChild>
                    <Link href={item.url}>
                      {item.icon && <item.icon />}
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        {loading ? (
          <DisplayChatHistoryLoading />
        ) : (
          <DisplayChatHistory
            chatHistory={chatLinks}
            chatId={chatId}
            onChatUpdate={handleChatUpdate}
          />
        )}
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenuButton onClick={() => setFeedbackDialogOpen(true)}>
          Give Feedback
        </SidebarMenuButton>
      </SidebarFooter>
      <GeneralFeedbackDialog open={feedbackDialogOpen} onOpenChange={setFeedbackDialogOpen} />
    </Sidebar>
  );
};
