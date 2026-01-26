import "server-only";

import { JWTPayload, SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { getCookie, setCookie } from "hono/cookie";
import { createMiddleware } from "hono/factory";
import { getUserData, type UserWithAccess } from "./db";

export const SESSION_COOKIE_NAME = "session";
export const SESSION_TOKEN_AUD = "cotiviti-search-session";
export const SESSION_TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7; // 7 days

type SessionKey = Uint8Array;

interface SessionTokenPayload extends JWTPayload {
  sub: string; // oktaId
  uid: string; // local user id
  role?: string | null;
  isAdmin?: boolean;
}

export interface UserAuthEnv {
  Variables: {
    user: UserWithAccess;
  };
}

const getSessionKey = (): SessionKey => {
  const secret = process.env.SESSION_JWT_SECRET;
  if (!secret) {
    throw new Error("SESSION_JWT_SECRET is not set");
  }
  return new TextEncoder().encode(secret);
};

export const createSessionToken = async (input: {
  oktaId: string;
  userId: string;
  role?: string | null;
  isAdmin?: boolean;
}) => {
  const now = Math.floor(Date.now() / 1000);
  return await new SignJWT({
    uid: input.userId,
    role: input.role ?? undefined,
    isAdmin: input.isAdmin ?? false,
  })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(input.oktaId)
    .setAudience(SESSION_TOKEN_AUD)
    .setIssuedAt(now)
    .setExpirationTime(now + SESSION_TOKEN_MAX_AGE_SECONDS)
    .sign(getSessionKey());
};

export const verifySessionToken = async (jwt: string): Promise<SessionTokenPayload> => {
  const { payload } = await jwtVerify(jwt, getSessionKey(), {
    audience: SESSION_TOKEN_AUD,
  });
  if (!payload.sub || !payload.uid) {
    throw new Error("Invalid session token claims");
  }
  const normalizedAdmin = Boolean((payload as SessionTokenPayload).isAdmin);
  return { ...(payload as SessionTokenPayload), isAdmin: normalizedAdmin };
};

export const verifySessionCookie = async () => {
  const token = (await cookies()).get(SESSION_COOKIE_NAME)?.value;
  if (!token) {
    throw new Error("Unauthorized");
  }
  return verifySessionToken(token);
};

export const getSessionPayloadFromCookie = async (): Promise<SessionTokenPayload | null> => {
  const token = (await cookies()).get(SESSION_COOKIE_NAME)?.value;
  if (!token) {
    return null;
  }
  try {
    return await verifySessionToken(token);
  } catch {
    return null;
  }
};

export const obtainUserData = createMiddleware<UserAuthEnv>(async (c, next) => {
  try {
    const sessionjwt = getCookie(c, SESSION_COOKIE_NAME);
    if (!sessionjwt) {
      return c.json({ error: "Unauthorized" }, 401);
    }
    const claims = await verifySessionToken(sessionjwt);

    const userId = claims.uid;
    if (!userId) {
      return c.json({ error: "Unauthorized" }, 401);
    }
    const user = await getUserData(userId);
    if (!user) {
      return c.json({ error: "User not found" }, 401);
    }
    console.log(`Authenticated user: ${user.email} (ID: ${userId})`);

    c.set("user", user);
    await next();
  } catch (error) {
    console.log("Auth middleware error:", error);
    setCookie(c, SESSION_COOKIE_NAME, "", {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "Lax",
      maxAge: 0,
      path: "/",
    });
    return c.json({ error: "Unauthorized" }, 401);
  }
});
