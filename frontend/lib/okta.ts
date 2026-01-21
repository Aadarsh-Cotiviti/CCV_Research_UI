import { OktaAuth, OktaAuthOptions } from "@okta/okta-auth-js";

const config: OktaAuthOptions = {
  issuer: process.env.NEXT_PUBLIC_AUTH_OKTA_ISSUER!,
  clientId: process.env.NEXT_PUBLIC_AUTH_OKTA_ID!,
  redirectUri: process.env.NEXT_PUBLIC_BASE_URL!,
  postLogoutRedirectUri: process.env.NEXT_PUBLIC_POST_LOGOUT!,
  pkce: true,
  scopes: ["openid", "profile", "email"],
};

export const authClient = new OktaAuth(config);
