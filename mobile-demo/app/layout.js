import "./globals.css";

export const metadata = {
  title: "Revenue Mobile Executive Demo",
  description: "Mobile-first executive view for revenue and inventory analysis.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-Hant">
      <body>{children}</body>
    </html>
  );
}
