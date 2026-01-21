import { AuthState, UserClaims } from "@okta/okta-auth-js";
import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { authClient } from "@/lib/okta";
import type { ChatNavLinks } from "@/app/api/[[...route]]/_authRoutes";
import type { ClientUser, LoginResponse } from "@/app/api/[[...route]]/route";
import type { UserRole } from "@/db/schemas";

export type UserProfileWithRole = UserClaims & {
  role?: UserRole;
  isAdmin?: boolean;
};

export interface UserProfileState {
  chatSessions: ChatNavLinks[];
  userProfile: ClientUser | null;
  loading: boolean;
}

export interface UserProfileActions {
  addChats: (chat: ChatNavLinks[]) => void;
  setChatSessions: (chats: ChatNavLinks[]) => void;
  setAuthState: (auth: AuthState) => void;
  authenticate: () => Promise<boolean>;
  updateUserRole: (role: UserRole) => Promise<void>;
  refreshChatHistory: () => Promise<void>;
  setLoading: (loading: boolean) => void;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: () => boolean;
  hasPrivilegedRole: (role: UserRole) => boolean;
}

export type UserProfileStore = UserProfileState & UserProfileActions;

const defaultState: UserProfileState = {
  userProfile: null,
  chatSessions: [],
  loading: false,
};

export const createUserProfileStore = (initState: UserProfileState = defaultState) => {
  return create<UserProfileStore>()(
    devtools((set, getState) => ({
      ...initState,
      addChats(chats) {
        set((state) => ({ chatSessions: [...state.chatSessions, ...chats] }));
      },
      setChatSessions(chats) {
        set({ chatSessions: [...chats] });
      },
      async authenticate() {
        set({ loading: true });
        try {
          const { tokens } = await authClient.token.parseFromUrl();
          // Fetch user profile with role from backend
          const loginResp = await fetch("/api/login", {
            method: "POST",
            body: JSON.stringify({ accessTokenData: tokens.accessToken }),
          });

          if (loginResp.ok) {
            const { chatHistory, profile } = (await loginResp.json()) as LoginResponse;

            set({
              userProfile: profile ?? null,
              chatSessions: chatHistory,
              loading: false,
            });
            return true;
          } else {
            set({ loading: false });
          }
          return false;
        } catch (error) {
          console.error("Error fetching user data:", error);
          set({ loading: false });
        }
      },
      login: async () => {
        set({ loading: true });
        await authClient.signInWithRedirect();
      },
      async refreshChatHistory() {
        set({ loading: true });
        try {
          const response = await fetch("/api/chat-history");
          if (response.ok) {
            const chatHistory = await response.json();
            set({ chatSessions: chatHistory, loading: false });
          } else {
            set({ loading: false });
          }
        } catch (error) {
          console.error("Error refreshing chat history:", error);
          set({ loading: false });
        }
      },
      setLoading(loading) {
        set({ loading });
      },
      logout: async () => {
        await authClient.signOut();
      },
      isAuthenticated: () => {
        return getState().userProfile !== null;
      },
      async updateUserRole(role) {
        set({ loading: true });
        try {
          const response = await fetch("/api/user/role", {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ role }),
          });

          if (response.ok) {
            set((state) => ({
              userProfile: state.userProfile ? { ...state.userProfile, role } : null,
              loading: false,
            }));
          } else {
            console.error("Failed to update user role");
            set({ loading: false });
          }
        } catch (error) {
          console.error("Error updating user role:", error);
          set({ loading: false });
        }
      },
      hasPrivilegedRole: (role) => {
        const profile = getState().userProfile;
        return profile?.isAdmin;
      },
    }))
  );
};
