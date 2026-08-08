### It expires after seven days

While the app is in Testing (step 2). Re-run this command if the agent has been
idle a week. Every error in the mail path ends by naming it, because every one
of them is fixed the same way.

---

## Before any of it: the two files that must never be committed

`credentials.json` and `token.json` are secrets, and FR-7.27 requires them
ignored **before the first commit** rather than after. Both are already listed
in [`.gitignore`](../.gitignore), along with `client_secret*.json`, which is the
name the console actually gives the file it hands you.

A secret pushed even once is compromised permanently. Deleting it from the
current tree does not remove it from history, and these repositories are public.
The remedy is not a revert; it is rotating the credential in the console.

See [`SECRETS.md`](SECRETS.md) for everything else this project keeps out of the
repository.
