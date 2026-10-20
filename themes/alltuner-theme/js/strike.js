// ABOUTME: The homepage's struck tuning fork: the All Tuner mark drawn live, replaying the Strike ident and ringing on input.
// ABOUTME: Geometry and timing match the brand repo's mark.py and ident.py; also runs the footer's sound toggle and skyline.

// ---------------------------------------------------------------- the mark (lockup SVG units, from mark.py)
const DISC_C = [47.992, 47.993]
const DISC_R = 47.99
const FORK_X = 47.353
const BOWL_Y = 54.966 // centre of the bowl curves, where the tines run into them
const BOWL_R = 20.164
const INNER = [11.77, 12.5]
const TINE_W = 8.35
const STEM_BOTTOM = 95.641
const DOT = [FORK_X, 59.776, 3.737]
const LEFT_X = FORK_X - BOWL_R
const RIGHT_X = FORK_X + BOWL_R - TINE_W
const TINE_TOP = 12.796
// Each tine is cut once, at mirrored heights: left reads short-long, right long-short.
const SEGMENTS = [
  [-1, LEFT_X, TINE_TOP, 25.176],
  [-1, LEFT_X, 34.984, BOWL_Y],
  [1, RIGHT_X, TINE_TOP, 35.686],
  [1, RIGHT_X, 45.496, BOWL_Y],
]
const TINE_LEN = BOWL_Y - TINE_TOP
// A reveal centred on the dot covers the whole disc once its radius passes the farthest disc edge.
const SWEPT = Math.hypot(DOT[0] - DISC_C[0], DOT[1] - DISC_C[1]) + DISC_R + 2
const WINE = '#5b2333'

// ---------------------------------------------------------------- timing (from ident.py)
const TAP_AT = 0.3
const HIT_AT = 0.7
const clamp01 = (x) => Math.min(1, Math.max(0, x))
const progress = (t, start, dur) => clamp01((t - start) / dur)
const easeOut = (x) => 1 - (1 - x) ** 3
const overshoot = (x) => {
  x = clamp01(x)
  const c = 2.2
  return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
}
// Visible stand-in for fork vibration: a decaying wobble after a hit.
const ring = (t, hit, amp, tau = 0.35, hz = 11) =>
  t < hit ? 0 : amp * Math.exp(-(t - hit) / tau) * Math.sin(2 * Math.PI * hz * (t - hit))

const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches
const SETTLED = { discR: SWEPT, cutout: true, bend: 0, reveal: 1, dot: 1, body: true }

function forkState(t, hits) {
  if (reducedMotion) return SETTLED
  const s = { discR: 0, cutout: false, bend: 0, reveal: progress(t, TAP_AT, 0.12), body: t >= TAP_AT }
  s.dot = t >= TAP_AT ? overshoot(progress(t, TAP_AT, 0.2)) : 0
  for (const h of hits) s.bend += ring(t, h.at, h.amp, h.tau)
  if (t >= HIT_AT) {
    // The disc spreads out from the dot and the solid fork flips into its cutout.
    s.discR = SWEPT * easeOut(progress(t, HIT_AT, 0.55))
    s.cutout = s.discR >= SWEPT - 1
  }
  return s
}

// A tine segment follows a cantilever bend, zero at the bowl.
const tineDx = (y, sign, bend) => sign * bend * ((BOWL_Y - y) / TINE_LEN) ** 2

function forkPath(s) {
  const p = new Path2D()
  if (s.body) p.rect(FORK_X - TINE_W / 2, BOWL_Y + BOWL_R - 1, TINE_W, STEM_BOTTOM + 2 - (BOWL_Y + BOWL_R - 1))
  if (s.reveal > 0) {
    for (const [sign, x, y0, y1Full] of SEGMENTS) {
      // Lower segments overlap into the bowl so separate fills don't leave an antialiased seam.
      const seam = y1Full === BOWL_Y && s.reveal >= 1 ? 0.8 : 0
      const y1 = y0 + (y1Full - y0) * s.reveal + seam
      p.moveTo(x + tineDx(y0, sign, s.bend), y0)
      p.lineTo(x + TINE_W + tineDx(y0, sign, s.bend), y0)
      p.lineTo(x + TINE_W + tineDx(y1, sign, s.bend), y1)
      p.lineTo(x + tineDx(y1, sign, s.bend), y1)
      p.closePath()
    }
  }
  if (s.dot > 0) {
    p.moveTo(DOT[0] + DOT[2] * s.dot, DOT[1])
    p.arc(DOT[0], DOT[1], DOT[2] * s.dot, 0, Math.PI * 2)
  }
  return p
}

// The bowl is a half annulus with an elliptical hollow, so it's filled on its own with evenodd under a clip.
function fillBowl(ctx) {
  ctx.save()
  const lower = new Path2D()
  lower.rect(0, BOWL_Y, 100, 60)
  ctx.clip(lower)
  const bowl = new Path2D()
  bowl.arc(FORK_X, BOWL_Y, BOWL_R, 0, Math.PI * 2)
  bowl.ellipse(FORK_X, BOWL_Y, INNER[0], INNER[1], 0, 0, Math.PI * 2)
  ctx.fill(bowl, 'evenodd')
  ctx.restore()
}

function fillFork(ctx, s) {
  ctx.fill(forkPath(s))
  if (s.body) fillBowl(ctx)
}

// ---------------------------------------------------------------- sound
// The Strike sound: brand.alltuner.com/ident/strike-stereo.wav trimmed to the strike
// (from 0.695 s, after the tap) and encoded as a 44 KB MP3. It is fetched and decoded
// on load, so it plays the moment the fork is clicked.
const STRIKE_SOUND = '/statics/audio/strike.mp3'
const VOLUME = 0.35
const SOUND_KEY = 'sound'

let audioCtx = null
let strikeBuffer = null

// Sound is on unless the visitor has turned it off.
function soundOn() {
  try {
    return localStorage.getItem(SOUND_KEY) !== 'off'
  } catch {
    return true
  }
}

function setSoundOn(on) {
  try {
    localStorage.setItem(SOUND_KEY, on ? 'on' : 'off')
  } catch {}
}

// Decoding with an OfflineAudioContext needs no user gesture, so it can happen before
// the first click; the decoded buffer then plays in the real AudioContext.
function loadSound() {
  strikeBuffer ??= fetch(STRIKE_SOUND)
    .then((r) => r.arrayBuffer())
    .then((b) => new OfflineAudioContext(2, 1, 48000).decodeAudioData(b))
    .catch((e) => {
      strikeBuffer = null
      throw e
    })
  return strikeBuffer
}

async function playStrike() {
  // Resume before any await, while the click still counts as the user's gesture.
  audioCtx ??= new AudioContext()
  const resumed = audioCtx.resume()
  const buffer = await loadSound()
  await resumed
  const src = audioCtx.createBufferSource()
  const gain = audioCtx.createGain()
  gain.gain.value = VOLUME
  src.buffer = buffer
  src.connect(gain).connect(audioCtx.destination)
  src.start()
}

// ---------------------------------------------------------------- the hero
function startFork(stage) {
  const canvas = stage.querySelector('canvas')
  const ctx = canvas.getContext('2d')
  const hint = document.getElementById('strike-hint')
  const clock = () => performance.now() / 1000
  const t0 = clock()
  // Every strike is a hit on the shared clock: the tines ring and, for full strikes, a ripple leaves the dot.
  const hits = [
    { at: TAP_AT, amp: 0.6, tau: 0.08, ripple: false },
    { at: HIT_AT, amp: 3.2, tau: 0.35, ripple: true },
  ]
  let width = 0
  let height = 0
  let dpr = 1
  let k = 1
  let ox = 0
  let oy = 0

  // The canvas overflows the disc-sized stage so ripples can spread behind the text around it.
  function resize() {
    dpr = Math.min(2, devicePixelRatio || 1)
    const d = stage.clientWidth
    width = Math.min(d * 2.8, innerWidth)
    height = d * 2.4
    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    k = d / (2 * DISC_R)
    ox = width / 2 - DISC_C[0] * k
    oy = height / 2 - DISC_C[1] * k
  }

  function drawRipples(t) {
    ctx.save()
    const outside = new Path2D()
    outside.rect(0, 0, width, height)
    outside.arc(ox + DISC_C[0] * k, oy + DISC_C[1] * k, DISC_R * k + 1, 0, Math.PI * 2)
    ctx.clip(outside, 'evenodd')
    ctx.strokeStyle = WINE
    for (const h of hits) {
      if (!h.ripple || t < h.at) continue
      for (let i = 0; i < 3; i++) {
        const age = t - h.at - i * 0.11
        const fade = Math.max(0, 1 - age / 1.6)
        if (age <= 0 || fade <= 0) continue
        ctx.globalAlpha = 0.22 * fade * fade
        ctx.lineWidth = Math.max(1, 1.6 * k * (1 - i * 0.25))
        ctx.beginPath()
        ctx.arc(ox + DOT[0] * k, oy + DOT[1] * k, (DISC_R * 0.6 + age * 95) * k, 0, Math.PI * 2)
        ctx.stroke()
      }
    }
    ctx.restore()
  }

  function draw(t) {
    const s = forkState(t, hits)
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, width, height)
    if (!reducedMotion) drawRipples(t)

    ctx.setTransform(dpr * k, 0, 0, dpr * k, dpr * ox, dpr * oy)
    ctx.fillStyle = WINE
    // The disc spreads out from the dot with the fork cut out of it...
    ctx.save()
    const wave = new Path2D()
    wave.arc(DOT[0], DOT[1], s.discR, 0, Math.PI * 2)
    const disc = new Path2D()
    disc.arc(DISC_C[0], DISC_C[1], DISC_R, 0, Math.PI * 2)
    ctx.clip(wave)
    ctx.fill(disc)
    ctx.globalCompositeOperation = 'destination-out'
    fillFork(ctx, s)
    ctx.restore()
    // ...while the fork is still a solid shape wherever the disc hasn't reached.
    if (!s.cutout) {
      ctx.save()
      const beyond = new Path2D()
      beyond.rect(-50, -50, 200, 200)
      beyond.arc(DOT[0], DOT[1], Math.max(0, s.discR), 0, Math.PI * 2)
      ctx.clip(beyond, 'evenodd')
      fillFork(ctx, s)
      ctx.restore()
    }
  }

  let visible = true
  let raf = 0
  function frame() {
    const t = clock() - t0
    draw(t)
    const settled = reducedMotion || (t > 2 && hits.every((h) => t - h.at > 2.2))
    raf = visible && !settled ? requestAnimationFrame(frame) : 0
  }
  const kick = () => {
    if (!raf) raf = requestAnimationFrame(frame)
  }

  function strike(amp = 3.2) {
    hits.push({ at: clock() - t0, amp, tau: 0.35, ripple: amp > 1 })
    while (hits.length > 8) hits.shift()
    if (amp > 1) {
      hint?.classList.add('strike-hint-done')
      if (soundOn()) playStrike().catch(() => {})
    }
    kick()
  }

  stage.addEventListener('click', () => strike())
  stage.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      strike()
    }
  })
  // A light touch: passing the pointer across the tines taps them without a ripple.
  let lastTap = 0
  stage.addEventListener('pointermove', (e) => {
    const r = canvas.getBoundingClientRect()
    const u = (e.clientX - r.left - ox) / k
    const v = (e.clientY - r.top - oy) / k
    const now = clock()
    const onTines = v > TINE_TOP && v < BOWL_Y && u > LEFT_X - 4 && u < RIGHT_X + TINE_W + 4
    if (onTines && now - lastTap > 0.5) {
      lastTap = now
      strike(0.7)
    }
  })

  new IntersectionObserver(([e]) => {
    visible = e.isIntersecting
    kick()
  }).observe(stage)
  addEventListener('resize', () => {
    resize()
    kick()
  })
  resize()
  kick()
  return strike
}

// ---------------------------------------------------------------- footer
function startSoundToggle(button, strike) {
  const sync = () => button.setAttribute('aria-pressed', String(soundOn()))
  button.addEventListener('click', () => {
    setSoundOn(!soundOn())
    sync()
    // Turning sound on strikes the fork, so the visitor hears what they just enabled.
    if (soundOn()) strike?.()
  })
  sync()
  if (soundOn()) loadSound().catch(() => {})
}

function startSkyline(skyline) {
  new IntersectionObserver(
    ([e], observer) => {
      if (!e.isIntersecting) return
      skyline.classList.add('skyline-drawn')
      observer.disconnect()
    },
    { threshold: 0.4 },
  ).observe(skyline)
}

const stage = document.getElementById('strike-stage')
const strike = stage ? startFork(stage) : null
const soundToggle = document.getElementById('sound-toggle')
if (soundToggle) startSoundToggle(soundToggle, strike)
const skyline = document.getElementById('skyline')
if (skyline) startSkyline(skyline)
