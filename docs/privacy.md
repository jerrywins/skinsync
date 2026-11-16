# Privacy

Designed with India's Digital Personal Data Protection Act 2023 principles in mind (notice, consent,
purpose limitation, minimisation, retention limits, erasure). This is an engineering description, not
legal advice; the operator must review it before launch.

| Data | Why | Kept for | How to delete |
|---|---|---|---|
| Email, password hash | Sign-in | Until account deletion | Settings → Privacy and data → Delete account |
| Profile, preferences | Ranking and filtering | Until changed or deleted | Edit profile; account deletion |
| Consent records | Proof of consent (policy version + time) | Until account deletion | Account deletion |
| Shelf, routines, saved results, share links | Features the user asked for | Until deleted | History, Shelf, Routines; account deletion |
| Skin photo | Analysis only | Deleted when analysis finishes; if the user ticks "keep", up to 30 days | "Delete photo now"; account deletion; hourly retention job |
| Skin analysis result | Show the user their result | Registered: until deleted. Guest: 7 days | "Delete this analysis"; account deletion |
| Label photo | OCR only | Deleted after text extraction (1 h maximum) | automatic |
| Guest comparisons / searches | Show and share results | 30 days unless saved or shared | automatic |
| Analytics events | Aggregate feature usage | Not deleted automatically (no personal data) | — |
| Audit log | Security and accountability | Kept; actor id only, no email | — |

Principles enforced in code:

* **Consent before upload**: the API rejects a skin photo without `consent=true`; registered users get a
  consent record with the policy version.
* **Minimisation**: EXIF/GPS stripped; photos re-encoded; analytics accept only allow-listed event names and
  a random session id; logs mask emails.
* **No secondary use**: there is no code path that copies images for training.
* **Erasure**: `DELETE /me` re-authenticates, deletes every stored image, then cascades through every
  personal table. Verified by `test_fr20_account_deletion_removes_everything`.
* **Private by default**: skin analyses cannot be shared (API check and database trigger).
