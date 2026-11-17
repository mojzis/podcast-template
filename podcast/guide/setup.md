# Setting up a show

There is no `podcast.toml` here yet. A show is a directory with `podcast.toml`,
`cover.png`, `episodes/` and `audio/`.

1. Create it (in the repository root, or a subdirectory such as `show/`):

   ```
   uv run podcast init . --title "My Show" --author "Your Name" --email you@example.com
   ```

2. Edit `podcast.toml`: `description`, `category`, `language`, and `base_url` —
   the https address the site will be served from, e.g.
   `https://<user>.github.io/<repo>/` for GitHub Pages.
3. Replace `cover.png` with real art: square PNG or JPEG, 1400-3000 px.
4. `uv run podcast check` until it prints no errors.
5. GitHub Pages: Settings → Pages → Source: GitHub Actions. The `pages.yml` workflow
   builds and deploys on every push to `main`.
6. Once the first episode is live, submit `<base_url>feed.xml` to Apple Podcasts
   Connect and Spotify for Creators, then add them as `[[links]]`.

Done looks like: `uv run podcast check` prints `ok` and exits 0.

Do not:
- point `base_url` at http:// — directories reject it;
- commit `public/`; the workflow builds it.

See `uv run podcast guide tune` for every config key.

next: `uv run podcast init . --title "..." --author "..." --email ...`
