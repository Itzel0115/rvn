import { IBM_Plex_Sans, Noto_Sans_TC } from "next/font/google";

import "./globals.css";

const uiFont = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ui",
});

const tcFont = Noto_Sans_TC({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-tc",
});

export const metadata = {
  title: "Revenue Intelligence Console",
  description: "Enterprise-grade revenue and inventory analysis workspace with agent-assisted charting.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-Hant">
      <body className={`${uiFont.variable} ${tcFont.variable}`}>{children}</body>
    </html>
  );
}
