import { Suspense } from "react";
import ArchitectChat from "@/components/ArchitectChat";

export default function Home() {
  return (
    <Suspense>
      <ArchitectChat />
    </Suspense>
  );
}
