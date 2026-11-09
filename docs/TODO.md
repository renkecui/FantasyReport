# TODO

Below lists additional ideas to implement for this project

## Core

### Webpage

Create a webpage for the poject

- Each table should be displayed on the webpage
- Plan: [WEBSITE_PLAN.md](WEBSITE_PLAN.md) (static site on GitHub Pages, built by the daily run)

### Live Data and Chat Bots

Refresh the website's data during the day and let users ask chat bots about the league, using free services only

- ESPN data fetched by GitHub Actions every 15–30 minutes on game days
- Chat bots run on a Cloudflare Worker that calls Claude (the API is the only paid part)
- See Phase 6 in [WEBSITE_PLAN.md](WEBSITE_PLAN.md)

## Features to Add

### General Manager

AI generated tips on what your team is lacking, and then looks at other teams to generate ideas for fair trades

Example: Give away assists for another stat so I don't need to look at every other team to see who needs assists and can offer me something good

### Charts

Display charts show team ranking trends throughout the season

### League Password

Protect the chat bots on the website with a shared league password, so only league members can use them (and spend AI credits)

- Stats pages stay public; only the chat needs the password
- Checked by the Cloudflare Worker, stored as a Worker secret, never in the repo
- See Phase 6 in [WEBSITE_PLAN.md](WEBSITE_PLAN.md)
