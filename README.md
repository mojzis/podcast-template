# podcast-template

A podcast as a static site. Markdown show notes and mp3 files go in; an RSS feed that
Apple Podcasts and Spotify accept, plus a small website, come out. GitHub Pages hosts
it for free.

```bash
uv run podcast guide
```

## Start a podcast from this template

1. **Use this template** on GitHub, clone your new repo, `uv sync`.
2. Edit `podcast.toml`: title, description, author, email, and `base_url`
   (`https://<user>.github.io/<repo>/`). Replace `cover.png` with square art,
   1400–3000 px.
3. Settings → Pages → Source: **GitHub Actions**.
4. `uv run podcast check` until it is clean, then push.

## Publish an episode

```bash
uv run podcast new "Episode title"
```

This writes `episodes/NNN-episode-title.md` as a draft and tells you where the mp3
goes (`audio/NNN-episode-title.mp3`). Write the show notes, list who reads it in
`readers:`, drop in the recording, remove `draft: true`, push. A `published:` date in
the future holds the episode back until that day (the Pages workflow also runs daily).

Optional: `episodes/NNN-episode-title.transcript.md` — shown on the episode page and
linked from the feed as a `podcast:transcript`.

Preview locally:

```bash
uv run podcast build --out public
```

```bash
python -m http.server -d public
```

## Listing the show

When the first episode is live, submit `<base_url>feed.xml` to
[Apple Podcasts Connect](https://podcastsconnect.apple.com) and
[Spotify for Creators](https://creators.spotify.com), then add both as `[[links]]` in
`podcast.toml` so the site links to them.

## Audio files

Audio lives in plain git, not Git LFS: every Pages build checks out all audio, and LFS
would count each build against its 1 GB/month bandwidth. Export mono mp3 at
64–96 kbit/s; a 30-minute episode is then 15–20 MB. `podcast check` fails on files over
GitHub's 100 MB limit. A GitHub Pages site may be up to 1 GB, which is roughly 50 hours
at those settings.

## Using it as a library

A project that makes episodes from other data can depend on this package and call
`podcast.build.build_site(show_dir, out_dir, now=...)` to render a show into a
sub-directory of its own site.

## Development

See [CLAUDE.md](CLAUDE.md): `uv run poe check` runs everything CI runs.
