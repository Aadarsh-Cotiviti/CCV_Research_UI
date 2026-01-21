"use client";

import { ClientUser } from "@/app/api/[[...route]]/route";
import { createUserProfileStore, UserProfileStore } from "@/stores/userProfileSlice";
import { createContext, use, useState } from "react";
import { useStore } from "zustand";

type UserProfileStoreApi = ReturnType<typeof createUserProfileStore>;

const ProfileContext = createContext<UserProfileStoreApi | undefined>(undefined);

type AuthProviderProps = {
  children: React.ReactNode;
  initProfile: ClientUser | null;
};

export const AuthProvider = ({ children, initProfile }: AuthProviderProps) => {
  const [store] = useState(() =>
    createUserProfileStore({
      userProfile: initProfile ?? null,
      chatSessions: [],
      loading: false,
    })
  );

  return <ProfileContext.Provider value={store}>{children}</ProfileContext.Provider>;
};

export const useProfileStore = <T,>(selector: (store: UserProfileStore) => T): T => {
  const ctx = use(ProfileContext);
  if (ctx === undefined) throw new Error("Provider is missing for auth");
  return useStore(ctx, selector);
};

export const ProfileDisplay = () => {
  const userProfile = useProfileStore((store) => store.userProfile);
  if (!userProfile) {
    return null;
  }
  return (
    <div>
      <div className="text-sm">{userProfile.name}</div>
      <div className="text-xs text-muted-foreground">{userProfile.email}</div>
    </div>
  );
};
