# `loopchii-wasm-core`

This crate is the public micro-kernel scaffold for the Stream adoption demo.

It is intentionally narrow:

- classify a prompt into a small set of risky nuisance categories
- return a deterministic governed decision
- compile cleanly into a browser-consumable WASM target when you want a local demo that does not depend on a Python process

## Suggested build

```bash
wasm-pack build loopchii-wasm-core --target web --out-dir pkg
```

The public browser surface currently mirrors the same logic through the JS package in `packages/loopchii-lite/`. This crate is the harder boundary for contributors who want a Rust/WASM path without exposing any private Loopchii runtime internals.
