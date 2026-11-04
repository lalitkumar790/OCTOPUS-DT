import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "OCTOPUS-DT | Open Octopus Digital Twin",
  description: "Interactive research dashboard for an eight-arm pneumatic soft robotic octopus digital twin."
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
