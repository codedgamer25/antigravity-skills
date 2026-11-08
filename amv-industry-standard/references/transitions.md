# Transitions

Renamed from the planned `speedlines.md`: measurement showed radial speed-lines are an
occasional accent, while **black** is the primary transitional device by a wide margin.

## Black is the main instrument

```
total black          237s of 1256s  =  18.9% of runtime
distinct black runs  629
run length           median 1 frame, p90 13 frames, max 867 frames (43.4s)
runs of 1-2 frames   413   (66% of all runs)
runs ≥20 frames      41    (section breaks)
```

Three distinct uses, and they must not be conflated:

### 1. Single-frame blinks — percussion (413 occurrences)

One or two black frames dropped **inside** a held shot. At ~1 every 3 seconds these act as
a hi-hat. This is the highest-leverage, cheapest part of the whole look, and the thing most
imitations miss.

```
length     1-2 frames (0.05-0.10s)
placement  inside a shot, not at its boundary
rate       ~20/min in dense sections
```

### 2. Half-second to two-second blackouts — phrase punctuation

Between lines or fills. Dozens across the mix, e.g. 1:16.35 (0.65s), 3:59.45 (1.00s),
6:16.65 (1.25s), 9:39.40 (1.55s), 18:18.40 (1.40s).

### 3. Long blackouts — track boundaries (41 runs ≥1s)

The structural skeleton. Notable ones:

| Time | Length | Role |
|---|---|---|
| 0:00.00 | 3.70s | Cold open on black |
| 0:48.70 | 6.10s | Intro close |
| **2:08.25** | **9.50s** | Major structural break |
| 6:45.20 | 2.50s | Section change |
| 8:01.15 | 3.30s | Section change |
| 13:44.80 | 7.00s | Entry to the grey act |
| 13:56.00 | 4.85s | Stuttered — see below |
| 14:01.25 | 5.75s | Stuttered |
| 14:09.25 | 3.10s | Stuttered |
| 14:15.80 | 3.80s | Stuttered |
| **16:47.40** | **9.55s** | Major structural break |
| 20:13.05 | 43.35s | End card |

**The 13:44-14:16 passage is worth copying directly:** five long blackouts (7.0, 4.85,
5.75, 3.10, 3.80s) separated by short bursts of footage, entering the desaturated act. A
stuttered fade-to-nothing rather than a single cut. It coincides with an instrumental gap in
the transcript (no lyrics 15:06-17:12).

## Luma slams

```
1-frame luma jumps >40/255   1613  (77 per minute)
p95 / p99 jump               49.7 / 134.5 of 255
max                          253 of 255  (full black to full white in one frame)
```

Plus 202 near-solid **white** frames (spatial std <12) used as blow-out hits, against 2798
near-solid black.

Cut on brightness as well as on subject: over one violent luma transition per second on
average.

## Zoom-bursts and radial accents

Present but occasional — one clear instance is a saturated green radial zoom-burst filling
frame. Not a per-section device; treat as a rare accent on a single hit.

```
form       radial/zoom streaks from a centre point, near-full-frame
colour     taken from the outgoing scene (green observed), not a fixed palette
duration   short — a few frames, inside the strobe budget
```

## Whip pans and speed ramps

The dominant *footage-level* transition: fast directional motion smearing into the next
shot, so the cut lands mid-blur. Combined with the 20fps gate this is what makes the mix
read as violent rather than merely fast. Pair with the directional blur in
`effect-stack.md` §3.

## Priority if you only implement some of this

1. 20fps gate
2. Single-frame black blinks (§1)
3. 3-frame cutting in peaks
4. Long blackouts at section boundaries (§3)
5. Luma slams
6. Everything else
