import Image from "next/image";
import { SidebarTrigger } from "./ui/sidebar";
import { HeaderUser } from "./sidebar/navUser";

export const Header = () => {
  return (
    <div className="relative flex h-16 shrink-0 items-center px-3 bg-sidebar">
      <div className="flex h-full items-center gap-2">
        <SidebarTrigger className="p-2" />
        <div className="relative h-full w-32">
          <Image alt="logo" fill src="/logo.png" className="object-contain" />
        </div>
      </div>
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-semibold">CCV Research AI</span>
      </div>
      <div className="ml-auto flex items-center">
        <HeaderUser />
      </div>
    </div>
  );
};
