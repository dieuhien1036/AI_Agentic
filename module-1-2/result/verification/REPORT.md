# Verification report — does `CLAUDE.md`/`AGENTS.md` actually do anything?

Same prompt (`verification_prompt.md`), same starting repo, one variable changed: whether
`CLAUDE.md`/`AGENTS.md` were present. Full transcripts: [run_with.md](run_with.md),
[run_without.md](run_without.md).

Short answer: yes — five observable differences, every one traceable to a specific line.
If these two runs had come out identical, that would have meant the context files were
decoration; they aren't.

## Difference 1 — URL shape

| | With | Without |
|---|---|---|
| URL | `GET /orders/count?user_id=` | `GET /orders/count/{user_id}` |

The with-file run mirrors the *existing* `GET /orders` list endpoint, which already takes
`user_id` as a query parameter. The without-file run picked a generic REST-ish path-param
shape that is internally inconsistent with the sibling endpoint two lines above it in the
same file.

**Traced to:** `CLAUDE.md` / `AGENTS.md` §7 "Examples", which spells out this *exact*
endpoint (`GET /orders/count`, `user_id` handled the same way as `list_orders`) as a worked
example — the agent had a concrete template to match instead of inventing a shape from
first principles.

## Difference 2 — Return type

| | With | Without |
|---|---|---|
| Return type | `OrderCountResponse` (Pydantic model, `response_model=` set) | bare `dict` (`{"count": n}`), no model, no `response_model` |

**Traced to:** `CLAUDE.md` / `AGENTS.md` §3 "Conventions": *"All request/response models
are Pydantic v2"* and *"Public types ... live in `app/types.py`"*. Without that rule
stated, reusing FastAPI's ability to serialize a raw dict is the path of least resistance,
and nothing in the code alone signals that every other handler in the file goes through a
named model.

## Difference 3 — Where the new type lives

| | With | Without |
|---|---|---|
| New type | `OrderCountResponse` added to `app/types.py` | no new type created at all |

This is really a consequence of Difference 2, but worth calling out on its own: the
without-file run didn't just skip the *convention* of using `app/types.py` — it skipped
having a named response type at all, because nothing prompted it to reify "the shape of
this response" as a first-class thing.

**Traced to:** `CLAUDE.md` / `AGENTS.md` §3, the line *"Public types — anything that
crosses a module boundary — live in `app/types.py`"*, plus the §7 example showing
`OrderCountResponse` defined there.

## Difference 4 — Where the logic lives

| | With | Without |
|---|---|---|
| Logic | New `count_orders_for_user()` in `app/orders/repository.py`, doing a real `SELECT COUNT(*)`; the route only calls it | Route handler calls the existing `list_orders_for_user()` and does `len(rows)` inline — no repository change, and it fetches every row (including the JSON `items` payload) just to discard it |

This is the most consequential difference: not just style, but a real (if minor at small
scale) performance regression in the without-file version, and a rule violation
independent of performance.

**Traced to:** `CLAUDE.md` / `AGENTS.md` §3: *"Route handlers never contain business
logic... delegate to a function in the same module (or a sibling repository module)"* and
§4 "Do not": *"Do not put business logic in a route handler — delegate it."* With that rule
absent, reusing an already-existing function inline is the locally-obvious shortcut; the
"write a proper repository function that actually implements COUNT" move isn't something
the model reaches for on its own from the code alone.

## Difference 5 — Which build command it reached for

| | With | Without |
|---|---|---|
| Command | `make lint && make test` | `pytest -q` |

Both failed in this sandbox (no `make`/`uv`/`pytest` installed — an environment limitation,
not a behavioral difference), but *which command each run reached for first* is exactly the
signal Step 4 is designed to surface, and it differs cleanly.

**Traced to:** `CLAUDE.md` / `AGENTS.md` §2 "Build & test": *"Always use the `Makefile`
targets — do not invoke `pytest`/`ruff`/`mypy` directly unless a target does not exist for
what you need."* Without that instruction, the without-file run defaulted to the tool it
knows generically (`pytest`) rather than checking the repo's own `Makefile`, even though
that file is sitting in the repo root either way — the context file is what turned "a
Makefile exists" into "use the Makefile."

## What this shows

Every difference maps to a line that exists in `CLAUDE.md`/`AGENTS.md` and not in the
without-file run's available context. None of the five differences came from the model
"knowing less" in some vague sense — each one is exactly the gap the corresponding rule
was written to close. That's the point of Step 4: a context file you can't point to a
specific behavior and back to a specific line for isn't doing anything real; this one is.
