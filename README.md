# fa-toolkit

A growing suite of open-source tools built by an AA flight attendant, for AA flight attendants.

Every tool here is written in plain Python, requires no special software beyond a Python install, and is designed to be useful on a layover laptop or a jump seat phone.

---

## Tools

| Tool | Description | Status |
|------|-------------|--------|
| [Pay Calculator](tools/pay_calculator/) | Estimates trip pay based on the 2024 APFA CBA - flight pay, boarding, per diem, rigs, position premiums, monthly estimate | Available |
| [fapaay](https://fapaay.com) ([source](tools/web/)) | Browser-based single-trip pay estimator. No install, works on any phone. | Beta |

More tools planned. See [CHANGELOG.md](CHANGELOG.md) for roadmap.

---

## No AA login, ever

Every tool in this repo works entirely from numbers you type in yourself - credit hours, TAFB, legs, whatever your trip paperwork shows. Nothing here logs into HSS, PBS, or any other AA system on your behalf, holds your AA credentials, or pulls your schedule automatically. There's no account, no session, no token - nothing AA could revoke even if it wanted to, because there's nothing to revoke.

That's a deliberate design choice, not an oversight. Any tool that *does* import or sync your schedule automatically has to authenticate as you to do it, one way or another - and that's exactly the kind of access AA has moved to shut down before. This suite stays on the safe side of that line by design, permanently.

---

## Requirements

Python 3.6 or newer. No pip installs. No dependencies outside the standard library.

---

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by American Airlines or the Association of Professional Flight Attendants (APFA). All tools are built and maintained independently.

Contract data is sourced from publicly available APFA CBA documents. All calculations are estimates for informational purposes only. Nothing here constitutes legal, tax, financial, or payroll advice. Always verify your pay against your official pay statement, and for anything contractual, reference the actual CBA or consult your local APFA representative.

The author assumes no liability for errors, omissions, or decisions made based on output from these tools.

---

*Built layover by layover.*
