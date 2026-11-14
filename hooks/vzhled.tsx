import type { Register } from 'claude-code'

// Mod „Pro tebe“ (Brixyy/agent-kit#31): v aplikaci Claude orámuje sekce odpovědi barevnými pruhy.
//   ### <emoji> nadpis   → začátek sekce: barevný pruh přes celou šířku s nadpisem
//   obsah sekce          → beze změny, v běžném vzhledu aplikace
//   konec sekce          → pruh stejné barvy bez textu
// Sekce končí dalším nadpisem s emoji, čarou --- nebo koncem zprávy. Barvu určuje emoji.
// Uživatel 14. 11. 2026: barevné jsou jen pruhy, obsah zůstává ve formátu aplikace.
// Text odpovědi se nemění (mobil a terminál ukazují obyčejný text).

type Stav = 'hotovo' | 'potrebuji' | 'chyba' | 'info'
const STAV: Record<Stav, { emoji: string[]; text: string; bg: string }> = {
  hotovo: { emoji: ['✅', '🟢'], text: 'success', bg: 'rgba(26, 127, 55, 0.24)' },
  potrebuji: { emoji: ['👉', '🟠', '✋'], text: 'warning', bg: 'rgba(214, 162, 60, 0.28)' },
  chyba: { emoji: ['⛔', '🔴', '❌'], text: 'error', bg: 'rgba(207, 34, 46, 0.24)' },
  info: { emoji: ['💡', '🔵'], text: 'suggestion', bg: 'rgba(59, 111, 216, 0.24)' },
}
const STAVY = Object.keys(STAV) as Stav[]
const EMOJI = STAVY.flatMap(s => STAV[s].emoji).join('|')
const podle = (emoji: string): Stav => STAVY.find(s => STAV[s].emoji.includes(emoji)) ?? 'info'

const NADPIS = new RegExp(String.raw`^#{1,3}\s*(${EMOJI})\s*(.+)$`, 'u')
const CARA = /^(-{3,}|\*{3,}|_{3,})$/

type Blok = { druh: 'volny'; text: string } | { druh: 'sekce'; emoji: string; nadpis: string; text: string }

export function rozdel(text: string): Blok[] {
  const bloky: Blok[] = []
  let aktualni: Blok = { druh: 'volny', text: '' }
  let md: string[] = []
  const uzavri = () => {
    aktualni.text = md.join('\n')
    if (aktualni.druh === 'sekce' || aktualni.text.trim()) bloky.push(aktualni)
    md = []
  }
  for (const radek of text.split('\n')) {
    const r = radek.trim()
    const n = r.match(NADPIS)
    if (n) { uzavri(); aktualni = { druh: 'sekce', emoji: n[1] ?? '', nadpis: (n[2] ?? '').trim(), text: '' } }
    else if (CARA.test(r) && aktualni.druh === 'sekce') { uzavri(); aktualni = { druh: 'volny', text: '' } }
    else md.push(radek)
  }
  uzavri()
  return bloky
}

export const register: Register = on => {
  on('ui.render', { component: 'AssistantMessage' }, ($, e, next) => {
    if (e.surface === 'terminal' || e.props.isSummary) return next(e)
    const bloky = rozdel(e.props.text)
    if (!bloky.some(b => b.druh === 'sekce')) return next(e)
    const { Box, Text, Markdown } = $.ui.resolve(e)
    return (
      <Box flexDirection="column" gap={2}>
        {bloky.map((b, i) => {
          const obsah = b.text.trim() ? <Markdown key={`m${i}`} text={b.text} /> : null
          if (b.druh === 'volny') return obsah
          const barva = STAV[podle(b.emoji)]
          return (
            <Box key={`s${i}`} flexDirection="column" gap={1}>
              <Box backgroundColor={barva.bg} paddingX={2} paddingY={1} justifyContent="center">
                <Text color={barva.text} size="heading" weight="semibold">{`${b.emoji}  ${b.nadpis}`}</Text>
              </Box>
              {obsah}
              <Box backgroundColor={barva.bg} height={1} />
            </Box>
          )
        })}
      </Box>
    )
  })
}
