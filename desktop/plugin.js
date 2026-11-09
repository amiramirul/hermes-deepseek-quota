/**
 * deepseek-quota — status-bar chip showing the DeepSeek account balance and the
 * estimated tokens left, so a top-up never comes as a surprise.
 *
 * The numbers come from the sibling backend (/api/plugins/deepseek-quota/balance,
 * see ../plugins/deepseek-quota/dashboard/plugin_api.py) — the API key stays
 * server-side. Hover for the detail line, click to force a fresh check.
 *
 * Folder name must equal the plugin id. Loads within seconds of landing here.
 */

import { cn, haptic, host, Tip, useQuery } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'

const ID = 'deepseek-quota'

function fmtToken(n) {
  if (n == null || !isFinite(n)) return '—'
  if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`
  if (n >= 1e6) return `${Math.round(n / 1e6)}M`
  if (n >= 1e3) return `${Math.round(n / 1e3)}k`
  return String(Math.round(n))
}

function fmtUsd(n) {
  if (n == null || !isFinite(n)) return '—'
  return `$${n.toFixed(2)}`
}

function QuotaChip({ ctx }) {
  const query = useQuery({
    queryKey: ['deepseek-quota', 'balance'],
    queryFn: () => ctx.rest('/balance'),
    refetchInterval: 60000,
    refetchOnWindowFocus: true,
    staleTime: 30000,
    retry: false
  })

  const data = query.data
  const ok = Boolean(data && data.ok)
  const balance = ok ? data.balance : null
  const pct = ok && data.peak > 0 ? Math.max(0, Math.min(1, balance / data.peak)) : 0

  const tip = ok
    ? [
        `DeepSeek: ${fmtUsd(balance)} baki`,
        `≈${fmtToken(data.tokens_left)} token tinggal`,
        `guna hari ni ${fmtUsd(data.spent_today ?? 0)}`,
        `7 hari ${fmtUsd(data.spent_7d ?? 0)}`
      ].join(' · ')
    : data && data.error
      ? `DeepSeek: ${data.error} — klik untuk cuba lagi`
      : 'DeepSeek: menyemak baki…'

  return jsx(Tip, {
    label: tip,
    children: jsx('button', {
      type: 'button',
      className: cn(
        'inline-flex h-full items-center gap-1 px-1.5 text-[0.6875rem] tabular-nums',
        'transition-colors text-(--ui-text-tertiary)',
        'hover:bg-(--chrome-action-hover) hover:text-foreground'
      ),
      onClick: () => {
        haptic('tap')
        query.refetch()
        if (ok) {
          host.notify({
            kind: balance > data.peak * 0.2 ? 'info' : 'warning',
            message: `DeepSeek ${fmtUsd(balance)} baki · ≈${fmtToken(data.tokens_left)} token · hari ni ${fmtUsd(data.spent_today ?? 0)}`
          })
        }
      },
      children: jsxs('span', {
        className: 'inline-flex items-center gap-1',
        children: [
          jsx('span', {
            className: 'inline-flex items-center',
            style: { flex: '0 0 auto' },
            children: jsx('span', {
              style: {
                position: 'relative',
                display: 'block',
                width: '32px',
                height: '4px',
                borderRadius: '999px',
                overflow: 'hidden',
                background: 'var(--ui-stroke-secondary)'
              },
              children: jsx('span', {
                style: {
                  position: 'absolute',
                  left: '0',
                  top: '0',
                  bottom: '0',
                  width: `${pct * 100}%`,
                  minWidth: '2px',
                  borderRadius: '999px',
                  background: 'var(--ui-accent)',
                  transition: 'width 500ms ease'
                }
              })
            })
          }),
          jsx('span', { children: ok ? fmtUsd(balance) : '—' })
        ]
      })
    })
  })
}

export default {
  id: ID, // must match the folder name
  name: 'DeepSeek Quota',
  register(ctx) {
    ctx.register({
      id: 'chip',
      area: 'statusBar.right',
      order: 130,
      render: () => jsx(QuotaChip, { ctx })
    })
  }
}
