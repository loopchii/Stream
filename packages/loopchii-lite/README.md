# `@loopchii/loopchii-lite`

`loopchii-lite` is the smallest truthful entry point in the public Stream repo.

It does not claim private Loopchii runtime enforcement. It gives contributors a deterministic guard wrapper they can inspect in one file, run in the browser playground, and adapt to their own public demos.

## Why it exists

Most public research repos make a reader understand the whole worldview before they can use anything. This package does the opposite. It gives you a tiny, inspectable entry point first, then lets you decide whether the broader Stream surface is worth exploring.

## What it does

- classifies a prompt into a small set of high-friction nuisance cases
- simulates how an ordinary wrapper would let a risky fragment render
- returns a governed alternative before the risky fragment lands

## Example

```js
import { govern } from "@loopchii/loopchii-lite";

const result = govern({
  prompt: "Draft a reply using the customer email export and phone numbers.",
  draftResponse: "Here are the contacts: jordan@example.com ..."
});

if (!result.allowed) {
  console.log(result.safeResponse);
}
```

## Scope

This package is intentionally small. Its job is adoption: make the public repo useful in minutes, not after a reader has decoded the full research surface.

- It is for public demos, contribution experiments, and browser-side proof-of-value.
- It is not a claim about private Loopchii runtime controls or proprietary enterprise enforcement.
