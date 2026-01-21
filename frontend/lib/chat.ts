"use server";

import { ClientSessionMessages } from "./db";

export type ChatData = {
  sectionId: string;
  chatId: string;
  messages: ClientSessionMessages;
  title?: string;
}[];
