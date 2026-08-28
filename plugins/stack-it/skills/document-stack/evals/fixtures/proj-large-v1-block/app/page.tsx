import { getPage } from "@/lib/content";

export default async function Home() {
  const page = await getPage("marketing", "index");
  return <main className="bg-paper text-ink">{page.title}</main>;
}
