"use client";

import { ChevronDownIcon, ChevronsUpDownIcon, CogIcon, LogOutIcon } from "lucide-react";
import { useProfileStore } from "../authComponents";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "../ui/sidebar";
import { PersonaSettings } from "../personaSettings";
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

const UserMenuDropdown = ({
  trigger,
  onOpenSettings,
  onLogout,
}: {
  trigger: ReactNode;
  onOpenSettings: () => void;
  onLogout: () => void;
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>{trigger}</DropdownMenuTrigger>
      <DropdownMenuContent className="w-56">
        <DropdownMenuItem onClick={onOpenSettings}>
          <CogIcon />
          Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onLogout}>
          <LogOutIcon />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const NavUser = () => {
  const logout = useProfileStore((store) => store.logout);
  const userProfile = useProfileStore((store) => store.userProfile);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  if (!userProfile) {
    return null;
  }

  const initial = userProfile.name.at(0) ?? "";

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <UserMenuDropdown
            onOpenSettings={() => setIsSettingsOpen(true)}
            onLogout={logout}
            trigger={
              <SidebarMenuButton size="lg">
                <div className="flex items-center gap-2">
                  <span className="size-8 flex items-center justify-center rounded-lg bg-muted">
                    {initial}
                  </span>
                  <div className="grid text-left leading-tight">
                    <span className="truncate font-medium text-sm">{userProfile.name}</span>
                    <span className="truncate text-xs">{userProfile.email}</span>
                  </div>
                </div>
                <ChevronsUpDownIcon className="ml-auto size-4" />
              </SidebarMenuButton>
            }
          />
        </SidebarMenuItem>
      </SidebarMenu>

      <PersonaSettings isOpen={isSettingsOpen} onOpenChange={setIsSettingsOpen} />
    </>
  );
};

export const HeaderUser = () => {
  const logout = useProfileStore((store) => store.logout);
  const userProfile = useProfileStore((store) => store.userProfile);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  if (!userProfile) {
    return null;
  }

  const initial = userProfile.name.at(0) ?? "";

  return (
    <>
      <UserMenuDropdown
        onOpenSettings={() => setIsSettingsOpen(true)}
        onLogout={logout}
        trigger={
          <button
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium shadow-sm",
              "hover:bg-background/80"
            )}
          >
            <span className="flex size-9 items-center justify-center rounded-lg bg-muted text-sm font-semibold">
              {initial}
            </span>
            <div className="hidden sm:grid text-left leading-tight">
              <span className="truncate text-sm font-medium">{userProfile.name}</span>
              <span className="truncate text-xs text-muted-foreground">{userProfile.email}</span>
            </div>
            <ChevronDownIcon className="ml-1 size-4 text-muted-foreground" />
          </button>
        }
      />

      <PersonaSettings isOpen={isSettingsOpen} onOpenChange={setIsSettingsOpen} />
    </>
  );
};
