# Reference

## podcast.toml, [show]

| key | required | meaning |
| --- | --- | --- |
| title | yes | show name |
| description | yes | a sentence or two; feed and home page |
| author | yes | itunes:author and owner name |
| email | yes | itunes:owner email; directories send verification mail here |
| base_url | yes | https address of the site; trailing `/` added |
| language | no, `en` | RSS language code |
| category, subcategory | no, `Technology` | Apple Podcasts category names |
| explicit | no, `false` | true or false |
| type | no, `episodic` | `episodic` or `serial` |
| subtitle | no | one line under the title |
| copyright | no | default `© <first year>-<now> <author>` |
| cover | no, `cover.png` | path from the show root |

`[[links]]` tables, each with `name` and `url`, list other places to listen.

## Episode front matter

| key | required | meaning |
| --- | --- | --- |
| title | yes | |
| published | yes | `2026-11-20` or `2026-11-20T09:00:00+01:00`; future = held back |
| readers | no | list of names; credited on the page and as podcast:person |
| summary | no | default: the first paragraph of the notes |
| season | no | whole number |
| guid | no | keep an old feed's guid when migrating |
| draft | no | `true` holds the episode back |

File names: `episodes/NNN-slug.md`, `audio/NNN-slug.mp3`,
optional `episodes/NNN-slug.transcript.md`. NNN is the episode number.

## Commands and exit codes

`uv run podcast init`, `uv run podcast new`, `uv run podcast check`,
`uv run podcast build`, `uv run podcast guide`. All take `--root` (default `.`).
Exit 0 ok, 1 failure or check errors, 2 usage or config error.

next: `uv run podcast check`
