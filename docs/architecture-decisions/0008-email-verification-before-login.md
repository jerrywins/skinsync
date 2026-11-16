# ADR 0008: Verify email before first sign-in

**Status:** Accepted. **Date:** 2026-11-04

Signing users in immediately after sign-up revealed whether an email was already registered (an existing
address could not be signed in). Sign-up now always answers "check your email", and sign-in requires a
verified address. Guest results are claimed at first sign-in with claim tokens kept in the browser tab.
