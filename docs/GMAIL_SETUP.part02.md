**Done when:** the scopes table lists that one entry, and
[`infra/gmail_auth.py`](../src/cop_agent/infra/gmail_auth.py) is still the only
file in the package containing a scope string — which
`test_only_the_send_scope_appears_anywhere_in_the_source` checks by reading the
source tree on every CI run.

### What the narrow scope actually buys

`token.json` lives on a laptop and grants exactly what the scope says. Assume it
leaks — a stray commit, a shared screen, a backup:

| Granted | What the leaked file does |
|---|---|
| `gmail.send` | sends mail as the account. Bad, loud, recoverable. |
| `+ gmail.readonly` | hands over years of correspondence. Silent, permanent. |

The second row is why FR-7.25 calls this the difference between a weapon and a
nearly harmless tool. Same file, same carelessness, entirely different day.

### Asking narrowly is not the same as receiving narrowly

Google returns the scopes **granted**, not the scopes requested. If the same
OAuth client was ever authorized more broadly, the grant can come back as the
union — and a token we did not ask for the power of is still a token that has
it.

`check_granted()` refuses such a token instead of trimming the list. Trimming
would describe the credential as narrow while the file on disk stayed wide, and
the file is what an attacker gets; it does not read our variables. The remedy is
to revoke at <https://myaccount.google.com/permissions> and authorize again.

---

## Step 4 — an OAuth Client ID of type **Desktop app**

**Do this:**

1. **APIs & Services → Credentials → Create credentials → OAuth client ID**.
2. Application type: **Desktop app**. Not *Web application*. Name it whatever
   you like.
3. **Download JSON** and save it in the repository root as `credentials.json`.
4. Confirm git is ignoring it *before* your next commit:

   ```bash
   git check-ignore -v credentials.json
   ```

   Silence means it is **not** ignored — stop and fix `.gitignore` first.

**Done when:** `credentials.json` sits in the repository root, the command above
names the `.gitignore` line that covers it, and `git status` does not mention it.

### Desktop app, and why the wrong choice hurts later

Every client type downloads as a file called `credentials.json` and they all
look plausible inside. The difference is one key: a Desktop client wraps its
fields in `"installed"`, a Web client in `"web"`.

Hand `InstalledAppFlow` a Web client and it proceeds normally — browser opens,
consent appears, you approve — and then dies at the redirect with

```
Error 400: redirect_uri_mismatch
```

which names a URI nobody configured. The natural response is an hour of adding
`http://localhost` to authorised redirect URIs in the console, and none of it
works, because the client is simply the wrong type.
[`infra/credentials.py`](../src/cop_agent/infra/credentials.py) says so at load
time instead.

### The check, not the promise

`.gitignore` containing a line and git actually ignoring a file are two
different facts. A pattern can be shadowed by a later negation, and a file that
is **already tracked** stays tracked no matter what the ignore file says.

`TestGitReallyIgnoresTheSecrets` asks git itself, in this repository, on every
CI run — `check-ignore` for each secret filename and `ls-files` to prove none is
tracked. It also asserts the rules are not *too* broad: a match log must stay
visible, since it is the evidence the Replay App verifies.

FR-7.27 is worth restating for the reason behind it. A secret pushed once is
compromised permanently: it stays in history, these repositories are public, and
the remedy is rotating the credential in the console rather than a revert.

---

## Step 5 — the first authorization flow

**Do this, once, from the repository root:**

```bash
python -m cop_agent.infra.authorize
```

A browser opens. Approve the consent screen — including the
**"Google hasn't verified this app"** interstitial, via *Advanced → Go to … (unsafe)*,
which is expected for an app in Testing. The command then writes `token_cop.json`
with mode `600`.

**Done when:** `token_cop.json` exists, a second run refreshes without asking again,
and `git check-ignore -v token_cop.json` names the `.gitignore` line covering it.

### The token file is named per agent on purpose

Not `token.json` in both repositories. The two agents authorize separately and
their credentials are not interchangeable — but two files with the same name in
sibling directories are an invitation to copy one across to skip the flow.
[`infra/token_store.py`](../src/cop_agent/infra/token_store.py) refuses a token
minted for a different `client_id` and says that copying is the usual cause.

Override with `GMAIL_TOKEN_PATH` if you want it somewhere else.

### What the command refuses, and why each refusal exists

| Refused | Because |
|---|---|
| an **over-scoped** grant | Google returns the scopes *granted*, which can exceed those requested if this client was ever authorized more broadly. Refused rather than trimmed — the file on disk is what an attacker gets, and it does not read our variables. |
| a grant with **no refresh token** | usable for an hour, then dead at whatever moment that hour ends. Google omits it when the client has been authorized before, so it appears exactly when somebody re-runs the flow to fix something else. Revoke at <https://myaccount.google.com/permissions> and run again. |
| a token from **another client** | it might work, and it is not ours. Usually a file copied between the two agents. |

Nothing is written when a grant is refused. Checking after the flow is not too
late: the file is what matters, and it does not get created.

The credentials file is checked **before** the browser opens, so nobody
approves a consent screen for a client that was never going to work.

### Sharing with a teammate

`credentials.json` identifies the **application**, so the same file works for
everyone on the team — hand it over directly. It is gitignored, so it is *not*
in a clone; a teammate who clones the repository gets no credentials at all.
They also need their address on the **Test Users** list from step 2.

`token_cop.json` is **personal**. Each person runs the flow for themselves.
