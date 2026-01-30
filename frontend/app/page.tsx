import { permanentRedirect } from "next/navigation";

export default function Home() {
  permanentRedirect("/chat-research");

  return <div></div>;
}
