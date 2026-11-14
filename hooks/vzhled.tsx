import type { Register } from 'claude-code'

// Mod „Pro tebe“ (Brixyy/agent-kit#31): v aplikaci Claude kreslí odpověď agenta jako barevné sekce.
//   ### <emoji> nadpis          → začátek sekce: barevný pruh přes celou šířku
//   <emoji> `Štítek` popis      → řádek sekce přes celou šířku se štítkem
//   ostatní text                → obsah sekce
// Sekce končí dalším nadpisem s emoji, čarou --- nebo koncem zprávy; uzavře ji pruh stejné barvy bez textu.
// Barvu určuje emoji. Text odpovědi se nemění (mobil a terminál ukazují obyčejný text).

type Stav = 'hotovo' | 'potrebuji' | 'chyba' | 'info'
const STAV: Record<Stav, { emoji: string[]; text: string; bg: string; svetle: string }> = {
  hotovo: { emoji: ['✅', '🟢'], text: 'success', bg: 'rgba(26, 127, 55, 0.28)', svetle: 'rgba(26, 127, 55, 0.09)' },
  potrebuji: { emoji: ['👉', '🟠', '✋'], text: 'warning', bg: 'rgba(214, 162, 60, 0.32)', svetle: 'rgba(214, 162, 60, 0.10)' },
  chyba: { emoji: ['⛔', '🔴', '❌'], text: 'error', bg: 'rgba(207, 34, 46, 0.28)', svetle: 'rgba(207, 34, 46, 0.09)' },
  info: { emoji: ['💡', '🔵'], text: 'suggestion', bg: 'rgba(59, 111, 216, 0.28)', svetle: 'rgba(59, 111, 216, 0.09)' },
}
const STAVY = Object.keys(STAV) as Stav[]
const EMOJI = STAVY.flatMap(s => STAV[s].emoji).join('|')
const podle = (emoji: string): Stav => STAVY.find(s => STAV[s].emoji.includes(emoji)) ?? 'info'

const NADPIS = new RegExp(String.raw`^#{1,3}\s*(${EMOJI})\s*(.+)$`, 'u')
const STITEK = new RegExp(String.raw`^(${EMOJI})\s*` + '`([^`]+)`' + String.raw`\s*(.*)$`, 'u')
const CARA = /^(-{3,}|\*{3,}|_{3,})$/

type Radek = { druh: 'md'; text: string } | { druh: 'stitek'; emoji: string; stitek: string; popis: string }
type Blok = { druh: 'volny'; radky: Radek[] } | { druh: 'sekce'; emoji: string; nadpis: string; radky: Radek[] }

export function rozdel(text: string): Blok[] {
  const bloky: Blok[] = []
  let aktualni: Blok = { druh: 'volny', radky: [] }
  let md: string[] = []
  const vyprazdniMd = () => {
    if (md.join('').trim()) aktualni.radky.push({ druh: 'md', text: md.join('\n') })
    md = []
  }
  const uzavri = () => {
    vyprazdniMd()
    if (aktualni.druh === 'sekce' || aktualni.radky.length > 0) bloky.push(aktualni)
  }
  for (const radek of text.split('\n')) {
    const r = radek.trim()
    const n = r.match(NADPIS)
    const s = r.match(STITEK)
    if (n) { uzavri(); aktualni = { druh: 'sekce', emoji: n[1] ?? '', nadpis: (n[2] ?? '').trim(), radky: [] } }
    else if (CARA.test(r)) { uzavri(); aktualni = { druh: 'volny', radky: [] } }
    else if (s) { vyprazdniMd(); aktualni.radky.push({ druh: 'stitek', emoji: s[1] ?? '', stitek: s[2] ?? '', popis: s[3] ?? '' }) }
    else md.push(radek)
  }
  uzavri()
  return bloky
}

export const register: Register = on => {
  on('ui.render', { component: 'AssistantMessage' }, ($, e, next) => {
    if (e.surface === 'terminal' || e.props.isSummary) return next(e)
    const bloky = rozdel(e.props.text)
    const maNeco = bloky.some(b => b.druh === 'sekce' || b.radky.some(r => r.druh === 'stitek'))
    if (!maNeco) return next(e)
    const { Box, Text, Markdown } = $.ui.resolve(e)

    const radky = (seznam: Radek[], klic: string) =>
      seznam.map((r, i) => {
        if (r.druh === 'md') return <Box key={`${klic}m${i}`} paddingX={2}><Markdown text={r.text} /></Box>
        const barva = STAV[podle(r.emoji)]
        return (
          <Box key={`${klic}s${i}`} flexDirection="row" gap={1} alignItems="center" backgroundColor={barva.svetle} paddingX={2} paddingY={1}>
            <Box backgroundColor={barva.bg} paddingX={1}>
              <Text color={barva.text} weight="semibold">{`${r.emoji} ${r.stitek}`}</Text>
            </Box>
            <Text>{r.popis}</Text>
          </Box>
        )
      })

    return (
      <Box flexDirection="column" gap={2}>
        {bloky.map((b, i) => {
          const klic = `b${i}`
          if (b.druh === 'volny') return <Box key={klic} flexDirection="column" gap={1}>{radky(b.radky, klic)}</Box>
          const barva = STAV[podle(b.emoji)]
          return (
            <Box key={klic} flexDirection="column" gap={1}>
              <Box backgroundColor={barva.bg} paddingX={2} paddingY={1} justifyContent="center">
                <Text color={barva.text} size="heading" weight="semibold">{`${b.emoji}  ${b.nadpis}`}</Text>
              </Box>
              {radky(b.radky, klic)}
              <Box backgroundColor={barva.bg} height={1} />
            </Box>
          )
        })}
      </Box>
    )
  })
}
