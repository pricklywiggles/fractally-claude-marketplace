import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ContactForm } from "./ContactForm";

describe("ContactForm", () => {
  it("renders the name field", () => {
    render(<ContactForm />);
    expect(screen.getByPlaceholderText("Name")).toBeTruthy();
  });
});
