# Pull Request Checklist

Thanks for contributing! Our robots handle most of the heavy lifting — just make sure you've got the basics right.

### ✅ Before You Submit

- [ ] **I checked my file with the [Schema Validator](schema-validator.html)** — Paste your JSON into our validator tool (or upload the file). It checks for syntax errors **and** verifies all required fields are present. If it says "✅ Valid", you're good to go.
- [ ] **IDs are lowercase with underscores** — For example `fire_mage`, not `Fire Mage` or `FireMage`.

### 🖼️ If I Added or Changed an Image

- [ ] **It's a `.webp` file** — PNG and JPG are not accepted. Use a free converter like [squoosh.app](https://squoosh.app) if needed.
- [ ] **It's in the right folder** — Placed at `assets/[category]/[id].webp` (e.g. `assets/heroes/fire_mage.webp`).
- [ ] **It's within size limits** — Max **512 × 512 pixels** and under **100 KB**.

### 🤖 Don't Worry About

These are handled **automatically** by our CI pipeline when you open your PR or when it's merged:

- ~~Code formatting & linting~~ — Auto-fixed by Ruff
- ~~`last_modified` timestamps~~ — Auto-stamped on merge
- ~~Patch notes & changelogs~~ — Auto-generated on merge
- ~~Building the API~~ — Runs automatically

---

## What Did You Change?

_A sentence or two about what you added, fixed, or updated._

## Related Issues

_Link any related issues (e.g. Fixes #123), or write "None"._
