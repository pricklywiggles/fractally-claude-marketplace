import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({ baseDirectory: import.meta.dirname });

export default [
  ...compat.extends("next/core-web-vitals", "next/typescript", "prettier"),
  {
    rules: {
      "no-restricted-imports": [
        "error",
        { patterns: [{ group: ["lucide-react"], importNamePattern: "^\\*$" }] },
      ],
    },
  },
];
