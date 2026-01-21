import { Hono } from "hono";
import { setCookie } from "hono/cookie";
import { handle } from "hono/vercel";
import {
  createUser,
  getUserDataByOkta,
  getUserChatHistory,
  syncBootstrapAdminRole,
} from "@/lib/db";
import { app as authRoutes } from "./_authRoutes";
import { AccessToken } from "@okta/okta-auth-js";
import { fetchOktaUserProfile, verifyAccessToken } from "@/lib/oktaServer";
import { User } from "@/db/schemas";
import {
  createSessionToken,
  SESSION_COOKIE_NAME,
  SESSION_TOKEN_MAX_AGE_SECONDS,
} from "@/lib/session";

export type ClientUser = Pick<User, "email" | "name" | "role" | "isAdmin">;

export type LoginResponse = {
  chatHistory: Awaited<ReturnType<typeof getUserChatHistory>>;
  profile: ClientUser;
};

const app = new Hono().basePath("/api");

app.post("/login", async (c) => {
  const body = (await c.req.json()) as { accessTokenData?: AccessToken };
  const accessToken = body?.accessTokenData?.accessToken;
  if (!accessToken) {
    return c.json({ error: "Missing access token" }, 400);
  }

  const oktaData = await verifyAccessToken(accessToken);
  const oktaId = (oktaData.uid as string | undefined) ?? oktaData.sub;
  let user = await getUserDataByOkta(oktaId);
  if (!user) {
    const profile = await fetchOktaUserProfile(accessToken);

    user = await createUser({
      oktaId,
      email: profile.email,
      name: profile.name,
    });
  }
  const adminSyncedUser = await syncBootstrapAdminRole(user);
  if (adminSyncedUser) {
    user = adminSyncedUser;
  }
  const chats = await getUserChatHistory(user.id);

  const sessionToken = await createSessionToken({
    oktaId,
    userId: user.id,
    role: user.role,
    isAdmin: user.isAdmin,
  });

  setCookie(c, SESSION_COOKIE_NAME, sessionToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "Lax",
    maxAge: SESSION_TOKEN_MAX_AGE_SECONDS,
    path: "/",
  });
  return c.json<LoginResponse>({
    chatHistory: chats,
    profile: { role: user.role, email: user.email, name: user.name, isAdmin: user.isAdmin },
  });
});

app.post("/logout", async (c) => {
  setCookie(c, SESSION_COOKIE_NAME, "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "Lax",
    maxAge: 0,
    path: "/",
  });
  return c.json({ success: true });
});

app.route("/", authRoutes);

export const GET = handle(app);
export const POST = handle(app);
export const PUT = handle(app);
export const DELETE = handle(app);
export const PATCH = handle(app);

export type AppType = typeof app;
