import {h,badge,empty} from '/base.js'
export const scopes={internal:'馆内阅览',partner:'馆际交换',public:'公开传播'}
const stages={draft:'待签认',approved:'已签认',revoked:'已撤回'}

export function permitRows(reels,grants,reviewer) {
  return reels.map(reel=>`<section class="permit-group"><header><h2>${h(reel.recording)}</h2><span>${h(reel.code)} / ${h(reel.donation)}</span></header>
    ${grants.filter(row=>row.reel===reel.code).map(row=>`<article><div class="permit-index"><strong>${h(row.instrument_ref)}</strong>${badge(scopes[row.access_scope])} ${badge(row.stage==='approved'&&!row.usable?'超出授权日期':stages[row.stage])}</div>
    <p>${h(row.begins)} 至 ${h(row.expires)}</p><blockquote>${h(row.credit_line)}</blockquote>
    ${row.revoke_note?`<p>撤回说明 ${h(row.revoke_note)}</p>`:''}
    ${reviewer&&row.stage==='draft'?`<form data-operation="approve" data-id="${row.id}"><button>核对日期并签认</button><p role="status"></p></form>`:''}
    ${reviewer&&row.stage==='approved'?`<details><summary>撤回授权</summary><form data-operation="revoke" data-id="${row.id}"><label>撤回说明<input name="note" minlength="4" maxlength="220" required></label><button>确认撤回</button><p role="status"></p></form></details>`:''}</article>`).join('')||empty('这卷尚未登记纸本授权。')}
  </section>`).join('')
}
