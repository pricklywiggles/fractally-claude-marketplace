import { z } from "zod";

const schema = z.object({
  DATABASE_URL: z.string().url(),
  STRIPE_SECRET_KEY: z.string().min(1),
  STRIPE_WEBHOOK_SECRET: z.string().min(1),
  RESEND_API_KEY: z.string().min(1),
});

export const env = schema.parse(process.env);
