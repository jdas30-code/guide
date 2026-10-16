# UK guide

Daily XMLTV guide for TiviMate. A GitHub Action downloads the EPGShare01 UK
guide, renames channel IDs using `mapping.json`, and publishes
`guide.xml.gz` to GitHub Pages.

- Guide URL: `https://<github-username>.github.io/<repo-name>/guide.xml.gz`
- Rebuild now: **Actions → Build guide → Run workflow**
- Add or fix a channel: edit `mapping.json` (`"provider-id": "epgshare-id"`)
