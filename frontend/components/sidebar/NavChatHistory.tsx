import { FC, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "../ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { MoreHorizontalIcon, PenIcon, TrashIcon } from "lucide-react";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ChatNavLinks } from "@/app/api/[[...route]]/_authRoutes";

interface ChatHistoryProps {
  chatHistory: ChatNavLinks[];
  chatId: string;
  onChatUpdate?: () => void;
}

export const DisplayChatHistory: FC<ChatHistoryProps> = ({ chatHistory, chatId, onChatUpdate }) => {
  const [dialogType, setDialogType] = useState<"delete" | "edit">("edit");
  const [selectedChat, setSelectedChat] = useState<ChatNavLinks | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const router = useRouter();

  const handleEditClick = (chat: ChatNavLinks) => {
    setSelectedChat(chat);
    setDialogType("edit");
    setIsDialogOpen(true);
  };

  const handleDeleteClick = (chat: ChatNavLinks) => {
    setSelectedChat(chat);
    setDialogType("delete");
    setIsDialogOpen(true);
  };

  const handleDialogClose = () => {
    setIsDialogOpen(false);
    setSelectedChat(null);
  };

  const handleChatUpdated = () => {
    handleDialogClose();
    onChatUpdate?.();
  };

  const handleChatDeleted = (deletedChatId: string) => {
    handleDialogClose();
    // If the currently viewed chat was deleted, redirect to home
    if (chatId === deletedChatId) {
      router.push("/");
    }
    onChatUpdate?.();
  };

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <SidebarGroup>
        <SidebarGroupLabel>Previous Research</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {chatHistory.map((item) => (
              <SidebarMenuItem key={item.id} className="flex items-center gap-2">
                <SidebarMenuButton isActive={chatId === item.id} asChild>
                  <Link href={item.url}>
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <SidebarMenuAction>
                      <MoreHorizontalIcon />
                    </SidebarMenuAction>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent side="right" align="start">
                    <DropdownMenuItem onClick={() => handleEditClick(item)}>
                      <PenIcon />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem variant="destructive" onClick={() => handleDeleteClick(item)}>
                      <TrashIcon />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      <DialogContent showCloseButton={false}>
        {dialogType === "edit" ? (
          <EditDialog
            chat={selectedChat}
            onChatUpdated={handleChatUpdated}
            onCancel={handleDialogClose}
          />
        ) : (
          <DeleteDialog
            chat={selectedChat}
            onChatDeleted={handleChatDeleted}
            onCancel={handleDialogClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
};

interface EditDialogProps {
  chat: ChatNavLinks | null;
  onChatUpdated: () => void;
  onCancel: () => void;
}

const EditDialog: FC<EditDialogProps> = ({ chat, onChatUpdated, onCancel }) => {
  const [newTitle, setNewTitle] = useState(chat?.title || "");
  const [isLoading, setIsLoading] = useState(false);

  const handleSave = async () => {
    if (!chat || !newTitle.trim()) return;

    setIsLoading(true);
    try {
      const response = await fetch(`/api/chat/${chat.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: newTitle.trim(),
          type: chat.type,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update chat");
      }

      onChatUpdated();
    } catch (error) {
      console.error("Error updating chat:", error);
      // You might want to show a toast notification here
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Rename Chat</DialogTitle>
        <DialogDescription>Give your chat a new name.</DialogDescription>
      </DialogHeader>
      <Input
        value={newTitle}
        onChange={(e) => setNewTitle(e.target.value)}
        placeholder="Enter new chat name"
        disabled={isLoading}
      />
      <DialogFooter>
        <Button variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button onClick={handleSave} disabled={isLoading || !newTitle.trim()}>
          {isLoading ? "Saving..." : "Save"}
        </Button>
      </DialogFooter>
    </>
  );
};

interface DeleteDialogProps {
  chat: ChatNavLinks | null;
  onChatDeleted: (chatId: string) => void;
  onCancel: () => void;
}

const DeleteDialog: FC<DeleteDialogProps> = ({ chat, onChatDeleted, onCancel }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleDelete = async () => {
    if (!chat) return;

    setIsLoading(true);
    try {
      const response = await fetch(`/api/chat/${chat.id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          type: chat.type,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to delete chat");
      }

      onChatDeleted(chat.id);
    } catch (error) {
      console.error("Error deleting chat:", error);
      // You might want to show a toast notification here
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Delete Chat</DialogTitle>
        <DialogDescription>
          Are you sure you want to delete &ldquo;{chat?.title}&rdquo;? This action cannot be undone.
        </DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button variant="destructive" onClick={handleDelete} disabled={isLoading}>
          {isLoading ? "Deleting..." : "Delete"}
        </Button>
      </DialogFooter>
    </>
  );
};

export const DisplayChatHistoryLoading = () => {
  return (
    <SidebarGroup>
      <SidebarGroupLabel>Previous Research</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          <div className="animate-pulse space-y-2">
            {[...Array(5)].map((_, index) => (
              <div key={index} className="h-6 bg-gray-500 rounded w-full"></div>
            ))}
          </div>
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
};
