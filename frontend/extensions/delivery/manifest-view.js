import {h,badge,empty} from '/base.js'
const stages={prepared:'待出库',sent:'已出库',acknowledged:'已签收',withdrawn:'已撤单'}
export function outgoing(handoffs,user) {
  return handoffs.map(row=>`<article class="handoff-article"><div class="seal-number">#${row.id}</div><section>
     <header><h3>${h(row.filename)}</h3>${badge(stages[row.stage])}</header><p>${h(row.name)} · ${h(row.purpose)}</p>
     <dl><dt>授权书</dt><dd>${h(row.instrument_ref)}</dd><dt>署名</dt><dd>${h(row.credit_text)}</dd>
     <dt>封套摘要</dt><dd class="handoff-digest">${h(row.seal_digest)}</dd></dl>
     ${row.receipt_ref?`<p>回执编号 ${h(row.receipt_ref)}</p>`:''}
     ${row.stage==='prepared'&&user.role==='reviewer'?`<div class="handoff-actions">
       <form data-operation="release" data-id="${row.id}"><button>核验授权并出库</button><p role="status"></p></form>
       <form data-operation="withdraw" data-id="${row.id}"><button class="quiet">撤回清单</button><p role="status"></p></form></div>`:''}
     ${row.stage==='sent'&&user.role==='operator'?`<form data-operation="receipt" data-id="${row.id}">
       <label>馆际回执<input name="receipt_ref" minlength="5" maxlength="32" required></label>
       <label>对方实测 SHA-256<input name="verified_digest" pattern="[a-f0-9]{64}" required></label><button>核对签收</button><p role="status"></p></form>`:''}</section></article>`).join('')||empty('通过质检的访问副本与同卷馆际授权可以生成交付清单。')
}
