CREATE TABLE `chats` (
	`id` text PRIMARY KEY NOT NULL,
	`created_at` integer DEFAULT (strftime('%s','now') * 1000) NOT NULL
);
--> statement-breakpoint
CREATE TABLE `general_feedback` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`category` text,
	`subject` text NOT NULL,
	`details` text NOT NULL,
	`created_at` integer DEFAULT (strftime('%s','now') * 1000) NOT NULL,
	FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_general_feedback_user_id` ON `general_feedback` (`user_id`);--> statement-breakpoint
CREATE TABLE `highlighted_text` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`session_id` text NOT NULL,
	`message_id` text NOT NULL,
	`section_id` integer,
	`selected_text` text NOT NULL,
	`context_before` text,
	`context_after` text,
	`start_offset` integer NOT NULL,
	`end_offset` integer NOT NULL,
	`notes` text,
	`created_at` integer DEFAULT (strftime('%s','now') * 1000) NOT NULL,
	FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`message_id`) REFERENCES `messages`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`section_id`) REFERENCES `sections`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_highlighted_text_user_id` ON `highlighted_text` (`user_id`);--> statement-breakpoint
CREATE INDEX `idx_highlighted_text_session_id` ON `highlighted_text` (`session_id`);--> statement-breakpoint
CREATE INDEX `idx_highlighted_text_message_id` ON `highlighted_text` (`message_id`);--> statement-breakpoint
CREATE TABLE `message_feedback` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`type` text NOT NULL,
	`issue_type` text,
	`details` text,
	`created_at` integer DEFAULT (strftime('%s','now') * 1000) NOT NULL,
	FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_feedbacks_user_id` ON `message_feedback` (`user_id`);--> statement-breakpoint
CREATE TABLE `messages` (
	`id` text PRIMARY KEY NOT NULL,
	`chat_id` text NOT NULL,
	`role` text NOT NULL,
	`content` text NOT NULL,
	`model_used` text,
	`documents` text,
	`created_at` integer DEFAULT (strftime('%s','now') * 1000) NOT NULL,
	`feedback_id` text,
	FOREIGN KEY (`chat_id`) REFERENCES `chats`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`feedback_id`) REFERENCES `message_feedback`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_messages_chat_id` ON `messages` (`chat_id`);--> statement-breakpoint
CREATE TABLE `sections` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`session_id` text NOT NULL,
	`chat_id` text NOT NULL,
	`title` text NOT NULL,
	`created_at` integer DEFAULT (strftime('%s','now') * 1000) NOT NULL,
	FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`chat_id`) REFERENCES `chats`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_sections_session_id` ON `sections` (`session_id`);--> statement-breakpoint
CREATE INDEX `idx_sections_chat_id` ON `sections` (`chat_id`);--> statement-breakpoint
CREATE TABLE `sessions` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`type` text DEFAULT 'chat' NOT NULL,
	`topic` text NOT NULL,
	`notes` text,
	`created_at` integer DEFAULT (strftime('%s','now') * 1000) NOT NULL,
	FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_sessions_user_id` ON `sessions` (`user_id`);--> statement-breakpoint
CREATE INDEX `idx_sessions_type` ON `sessions` (`type`);--> statement-breakpoint
CREATE TABLE `users` (
	`id` text PRIMARY KEY NOT NULL,
	`okta_id` text NOT NULL,
	`email` text NOT NULL,
	`name` text NOT NULL,
	`role` text DEFAULT 'other',
	`is_admin` integer DEFAULT false NOT NULL,
	`created_at` integer DEFAULT (strftime('%s','now') * 1000) NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `users_okta_id_unique` ON `users` (`okta_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `users_email_unique` ON `users` (`email`);--> statement-breakpoint
CREATE INDEX `idx_users_okta_id` ON `users` (`okta_id`);