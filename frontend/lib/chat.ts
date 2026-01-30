"use server";

import { ClientSessionMessages } from "./db";

export type ChatData = {
  sectionId: string;
  messages: Promise<ClientSessionMessages> | ClientSessionMessages;
  title?: string;
}[];
