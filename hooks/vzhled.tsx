import type { Register } from 'claude-code'

// Mod „Pro tebe“ (Brixyy/agent-kit#31): v aplikaci Claude obarví v odpovědích agenta
//   ### <emoji> text            → barevný pruh přes celou šířku
//   <emoji> `Štítek` popis      → barevný štítek s popisem
// Barvu určuje emoji. Text odpovědi se nemění (mobil a terminál ukazují obyčejný text).

type Stav = 'hotovo' | 'potrebuji' | 'chyba' | 'info'
const STAV: Record<Stav, { emoji: string[]; text: string; bg: string }> = {
  hotovo: { emoji: ['✅', '🟢'], text: 'success', bg: 'rgba(26, 127, 55, 0.20)' },
  potrebuji: { emoji: ['👉', '🟠', '✋'], text: 'warning', bg: 'rgba(214, 162, 60, 0.24)' },
  chyba: { emoji: ['⛔', '🔴', '❌'], text: 'error', bg: 'rgba(207, 34, 46, 0.20)' },
  info: { emoji: ['💡', '🔵'], text: 'suggestion', bg: 'rgba(59, 111, 216, 0.20)' },
}
const STAVY = Object.keys(STAV) as Stav[]
const EMOJI = STAVY.flatMap(s => STAV[s].emoji).join('|')
const podle = (emoji: string): Stav => STAVY.find(s => STAV[s].emoji.includes(emoji)) ?? 'info'

const PRUH = new RegExp(String.raw`^#{1,3}\s*(${EMOJI})\s*(.+)$`, 'u')
const STITEK = new RegExp(String.raw`^(${EMOJI})\s*` + '`([^`]+)`' + String.raw`\s*(.*)$`, 'u')

type Kus =
  | { druh: 'md'; text: string }
  | { druh: 'pruh'; emoji: string; text: string }
  | { druh: 'stitek'; emoji: string; stitek: string; popis: string }

export function rozdel(text: string): Kus[] {
  const kusy: Kus[] = []
  let md: string[] = []
  const vyprazdni = () => {
    if (md.join('').trim()) kusy.push({ druh: 'md', text: md.join('\n') })
    md = []
  }
  for (const radek of text.split('\n')) {
    const r = radek.trim()
    const p = r.match(PRUH)
    const s = r.match(STITEK)
    if (p) { vyprazdni(); kusy.push({ druh: 'pruh', emoji: p[1] ?? '', text: (p[2] ?? '').trim() }) }
    else if (s) { vyprazdni(); kusy.push({ druh: 'stitek', emoji: s[1] ?? '', stitek: s[2] ?? '', popis: s[3] ?? '' }) }
    else md.push(radek)
  }
  vyprazdni()
  return kusy
}

export const register: Register = on => {
  on('ui.render', { component: 'AssistantMessage' }, ($, e, next) => {
    if (e.surface === 'terminal' || e.props.isSummary) return next(e)
    const kusy = rozdel(e.props.text)
    if (!kusy.some(k => k.druh !== 'md')) return next(e)
    const { Box, Text, Markdown } = $.ui.resolve(e)
    return (
      <Box flexDirection="column" gap={1}>
        {kusy.map((k, i) => {
          if (k.druh === 'md') return <Markdown key={`m${i}`} text={k.text} />
          const barva = STAV[podle(k.emoji)]
          if (k.druh === 'pruh')
            return (
              <Box key={`p${i}`} backgroundColor={barva.bg} paddingX={2} paddingY={1} justifyContent="center">
                <Text color={barva.text} size="heading" weight="semibold">{`${k.emoji}  ${k.text}`}</Text>
              </Box>
            )
          return (
            <Box key={`s${i}`} flexDirection="row" gap={1}>
              <Box backgroundColor={barva.bg} paddingX={1}>
                <Text color={barva.text} weight="semibold">{`${k.emoji} ${k.stitek}`}</Text>
              </Box>
              <Text>{k.popis}</Text>
            </Box>
          )
        })}
      </Box>
    )
  })
}
