# news-image-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/jmjuve/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/jmjuve/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A program that draws Friday 20 November 2026's world news as a
newspaper front page — a single 1024x1024 PNG.

The lead story is Russia's overnight ballistic-missile attack on Kyiv:
missile trails and explosions over the night skyline, fires burning,
and a span of a Dnipro bridge torn away, under the headline
"KYIV'S BRIDGES HIT". Below it, three mini-stories in equal columns:
Asian markets tumbling ("MARKETS TUMBLE" — Taiwan down 5%, Nikkei
-4.8%), Cyclone Akvan making landfall on India's east coast
("CYCLONE AKVAN HITS INDIA"), and Kamala Harris meeting Emmanuel
Macron in Paris ("HARRIS MEETS MACRON").

## How it works

`main.py` is pure Python 3 standard library — no PIL, no network, no
external assets. It draws every shape and letter with code onto an RGB
raster (a hand-built single-stroke capital font, flat vector shapes) and
encodes a deterministic PNG with zlib level 9 and no ancillary chunks.
Fixed palette, fixed geometry, no time, no randomness: two runs produce
byte-identical output.

## Run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024x1024, under 1 MiB).

## License

MIT — see [LICENSE](LICENSE).
