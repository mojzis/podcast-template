# Publishing an episode

1. Start it — this picks the next number and writes a draft:

   ```
   uv run podcast new "Episode title"
   ```

   It prints the markdown file and where the mp3 must go.
2. Write show notes in the markdown body; the first paragraph is the summary apps show.
   Fill `readers: [Name, Name]`. Optional: a transcript in
   `episodes/<slug>.transcript.md` (the script you read is fine).
3. Record and save the audio as `audio/<slug>.mp3` — mono, 64-96 kbit/s keeps a
   30-minute episode under 20 MB.
4. Set `published:` to the release date and remove `draft: true`. A future date holds
   the episode back until a build runs on or after that day.
5. Check, then preview:

   ```
   uv run podcast check
   uv run podcast build --out public
   python -m http.server -d public
   ```

6. Commit the markdown and the mp3, push to `main`; the Pages workflow publishes.

An episode missing from the site is *held back*: `uv run podcast check` says why
(draft, scheduled, or no audio).

Do not:
- renumber or rename a published episode: its URL is its guid, and apps would
  list it again as new. If you must, set `guid:` to the old URL first;
- edit audio of a published episode in place without need — apps cache it.

next: `uv run podcast check`
