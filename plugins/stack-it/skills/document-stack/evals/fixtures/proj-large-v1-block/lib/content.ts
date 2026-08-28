import { readFile } from "node:fs/promises";
import path from "node:path";
import { compileMDX } from "next-mdx-remote/rsc";
import { z } from "zod";

const frontmatter = z
  .object({ title: z.string(), description: z.string(), order: z.number().optional() })
  .strict();

export async function getPage(section: string, slug: string) {
  const source = await readFile(
    path.join(process.cwd(), "content", section, `${slug}.mdx`),
    "utf8",
  );
  const { content, frontmatter: data } = await compileMDX({
    source,
    options: { parseFrontmatter: true },
  });
  return { ...frontmatter.parse(data), body: content };
}
