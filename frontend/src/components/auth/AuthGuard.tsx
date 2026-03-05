"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, user, loadUser } = useAuthStore();

  useEffect(() => {
    if (!token) {
      router.replace("/login");
      return;
    }
    if (!user) {
      loadUser().catch(() => router.replace("/login"));
    }
  }, [token, user, loadUser, router]);

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <p className="text-gray-400">Redirecting to login...</p>
      </div>
    );
  }

  return <>{children}</>;
}
