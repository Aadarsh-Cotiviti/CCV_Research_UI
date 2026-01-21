import { ApcContextProvider } from "./components/apcContext";
import { APCPage } from "@/app/(auth-protected)/apc-research/components/apcPage";

const Page = () => {
  return (
    <ApcContextProvider>
      <APCPage />
    </ApcContextProvider>
  );
};
export default Page;
