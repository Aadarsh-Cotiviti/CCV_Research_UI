import "server-only";
import oktajwt from "@okta/jwt-verifier";
import { getCookie, setCookie } from "hono/cookie";
import { createMiddleware } from "hono/factory";
import { getUserData } from "./db";
import { User } from "@/db/schemas";
import { SESSION_COOKIE_NAME, verifySessionToken } from "./session";

export interface OktaUserProfile {
  sub: string;
  name: string;
  email: string;
  given_name?: string;
  family_name?: string;
  preferred_username?: string;
  locale?: string;
  zoneinfo?: string;
  updated_at?: number;
  [key: string]: unknown;
}

const userInfoEndpoint = `${process.env.NEXT_PUBLIC_AUTH_OKTA_ISSUER}/v1/userinfo`;

export const fetchOktaUserProfile = async (accessToken: string): Promise<OktaUserProfile> => {
  if (!accessToken) {
    throw new Error("No access token provided");
  }
  const response = await fetch(userInfoEndpoint, {
    headers: { authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Okta userinfo error:", response.status, errorText);
    throw new Error(`Failed to fetch Okta profile (${response.status})`);
  }

  return (await response.json()) as OktaUserProfile;
};

const oktaJwtVerifier = new oktajwt({
  issuer: process.env.NEXT_PUBLIC_AUTH_OKTA_ISSUER!,
  clientId: process.env.NEXT_PUBLIC_AUTH_OKTA_ID!,
  assertClaims: {
    aud: "api://default",
  },
});

export const verifyAccessToken = async (accessToken: string | undefined) => {
  if (!accessToken) {
    throw new Error("No token provided");
  }
  try {
    const verifiedToken = await oktaJwtVerifier.verifyAccessToken(accessToken, "api://default");
    if (verifiedToken.isExpired()) {
      throw new Error("Token expired");
    }
    return verifiedToken.claims;
  } catch (err) {
    console.log(err);
    throw new Error("Invalid token");
  }
};
