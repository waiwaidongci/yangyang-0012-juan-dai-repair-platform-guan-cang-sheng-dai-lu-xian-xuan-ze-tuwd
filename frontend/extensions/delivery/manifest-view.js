import {h,badge,empty} from '/base.js'
const stages={prepared:'待出库',sent:'已出库',recalling:'待召回',acknowledged:'已签收',returned:'已退回',withdrawn:'已撤单'}
const kinds={acknowledgement:'签收',return:'退回'}
const signedLabel={acknowledgement:'对方签收时间',return:'对方退回时间'}
const fmt=value=>new Date(value).toLocaleString('zh-CN',{hour12:false})

function trail(row,reissue) {
  const steps=[]
  if (row.released_at) steps.push(`<li><b>出库</b>${fmt(row.released_at)} · ${h(row.released_by)}</li>`)
  if (row.recalled_at) steps.push(`<li><b>召回</b>${fmt(row.recalled_at)} · 授权已撤回${row.revoke_note?`：${h(row.revoke_note)}`:''}</li>`)
  if (row.received_at) steps.push(`<li><b>签收</b>${fmt(row.received_at)} · 回执 ${h(row.receipt_ref)}</li>`)
  if (row.returned_at) steps.push(`<li><b>退回</b>${fmt(row.returned_at)} · 伙伴确认副本已退回</li>`)
  if (reissue) steps.push(`<li><b>补发</b>已开立清单 #${reissue.id}（${stages[reissue.stage]}）</li>`)
  return steps.length?`<ol class="handoff-trail">${steps.join('')}</ol>`:''
}

function receiptList(mine) {
  return mine.length?`<ul class="handoff-receipts">${mine.map(row=>`<li>${kinds[row.kind]}回执 ${h(row.receipt_ref)}
    · ${signedLabel[row.kind]} ${fmt(row.signed_at)} · 登记 ${h(row.recorded_by)}
    ${row.disputed?`${badge('争议','dispute')} <span class="dispute-note">${h(row.dispute_note)}</span>`:''}</li>`).join('')}</ul>`:''
}

const receiptForm=(row,refLabel,timeLabel,button,operation)=>`<form data-operation="${operation}" data-id="${row.id}" class="handoff-receipt-form">
  <label>${refLabel}<input name="receipt_ref" minlength="5" maxlength="32" pattern="[A-Z0-9-]+" required></label>
  <label>对方实测 SHA-256<input name="verified_digest" pattern="[a-f0-9]{64}" required></label>
  <label>${timeLabel}<input name="signed_at" type="datetime-local" required></label>
  <button>${button}</button><p role="status"></p></form>`

function actions(row,grants,user) {
  const forms=[]
  if (row.stage==='prepared'&&user.role==='reviewer')
    forms.push(`<div class="handoff-actions">
      <form data-operation="release" data-id="${row.id}"><button>核验授权并出库</button><p role="status"></p></form>
      <form data-operation="withdraw" data-id="${row.id}"><button class="quiet">撤回清单</button><p role="status"></p></form></div>`)
  if (user.role==='operator') {
    if (row.stage==='sent'||row.stage==='recalling')
      forms.push(receiptForm(row,'馆际回执','对方签收时间','核对签收','receipt'))
    if (row.stage==='recalling')
      forms.push(receiptForm(row,'退回回执','对方退回时间','登记退回确认','return'))
    if (row.stage==='returned') {
      const options=grants.filter(grant=>grant.reel===row.reel)
        .map(grant=>`<option value="${grant.id}">${h(grant.instrument_ref)}</option>`).join('')
      forms.push(options?`<form data-operation="reissue" data-id="${row.id}" class="handoff-receipt-form">
        <label>新馆际授权<select name="grant_id">${options}</select></label>
        <label>使用说明<input name="purpose" minlength="6" maxlength="180" value="${h(row.purpose)}" required></label>
        <button>凭新授权补发</button><p role="status"></p></form>`
        :'<p class="muted">该卷暂无可用馆际授权，登记新授权后方可补发。</p>')
    }
    if (row.stage==='acknowledged'||row.stage==='returned')
      forms.push(`<details class="late-receipt"><summary>登记晚到的签收回执</summary>
        ${receiptForm(row,'馆际回执','对方签收时间','核对签收','receipt')}</details>`)
  }
  return forms.join('')
}

export function outgoing(handoffs,receipts,grants,user) {
  return handoffs.map(row=>{
    const mine=receipts.filter(item=>item.handoff===row.id)
    const reissue=handoffs.find(other=>other.reissue_of===row.id)
    const disputed=mine.some(item=>item.disputed)
    return `<article class="handoff-article"><div class="seal-number">#${row.id}</div><section>
     <header><h3>${h(row.filename)}</h3><div class="handoff-badges">${badge(stages[row.stage])}
       ${row.grant_stage==='revoked'?badge('授权已撤回','warn'):''}${disputed?badge('争议','dispute'):''}</div></header>
     <p>${h(row.name)} · ${h(row.purpose)}${row.reissue_of?` · 补发自清单 #${row.reissue_of}`:''}</p>
     <dl><dt>授权书</dt><dd>${h(row.instrument_ref)}</dd><dt>署名</dt><dd>${h(row.credit_text)}</dd>
     <dt>封套摘要</dt><dd class="handoff-digest">${h(row.seal_digest)}</dd></dl>
     ${trail(row,reissue)}${receiptList(mine)}${actions(row,grants,user)}</section></article>`
  }).join('')||empty('通过质检的访问副本与同卷馆际授权可以生成交付清单。')
}
