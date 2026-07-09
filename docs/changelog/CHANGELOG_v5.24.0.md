<!--
Copyright (c) 2017-2026 Juancarlo Añez (apalala@gmail.com)
SPDX-License-Identifier: BSD-4-Clause
-->

# [v5.24.0] new features + optimizations

[v5.24.0]: https://github.com/neogeny/tatsu/compare/v5.23.0...HEAD

## Changed

### Multi-bars in concurrency

* Now `parproc` streams/iterates only `Result` objects. Using the results stream for passing other information led to complicated code.

* All update notifications in crross-process update of `barz` bars go through a `packetz` queue. Now `PacketzQueue` is JSON-serializable for that purpose. The actual payload of a queue passed across tasks or processes is the path to the file-based queue.

* Synchronization through a queue is done by a `barz.BarBroker` which is opt-in for users of the library. `BarBroker` uses a daemon thread to read the queue and call `update_row()` on the `Multi`.

* `Multi.height` starts at `-1` as the magic number to preserve the line position before drawing of the first bar.

* Keeping the files for queues happeens on a per-queue basis with `Packetz(keep=True)`. The files are stored uner `./packetz/` by default. The format of the filenames is `aaaa-HH-mmmm.pkz.jsonl`, where `aaaa` is four letters representing the Unix timestamp day in base `len(strings.ascii_loweercase)`, `HH` is the UTC hour, and `mmmm` is the fraction of the hour in tenth mof millisecond. The format of the files is JSONL, with one line of flattened JSON per packet. Keeping all the files for queues may be activated by setting the `PACKETZ_KEEP` environment variable to _non-falsy_.

* Optimized `PacketzQueue.receive()` to read by line and retry if a line of JSONL was incomplete (no newline at the end).

### Other

* Changed the documentatiion theme to [Furo](https://pradyunsg.me/furo/).

## OGoPEGo

* A round of removing memory and transformation bottlenecks has **[OGoPEGo]** generating the fastest parsers among the **TatSu** family of PEG parser generators. When the CLI combines the parser speed with Go's implementation of concurrency the result feels instantaneous.

[OGoPEGo]: https://pypi.org/project/ogopego/
