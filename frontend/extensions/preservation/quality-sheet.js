import {h,badge,empty} from '/base.js'
export const kinds={master:'保存母版',access:'访问副本'}
const stages={queued:'待核验',accepted:'质检通过',failed:'需重制'}

export function results(checks,reviewer) {
  return checks.map(row=>`<article class="audio-qc"><header><h3>${h(row.filename)}</h3>${badge(stages[row.stage])}</header>
    <p>${h(row.reel)} / 工序卡 #${row.card} · ${kinds[row.kind]}</p>
    <div class="audio-measures"><b>${h(row.sample_rate)} Hz</b><span>${h(row.channels)} 声道</span><span>${h(row.duration_seconds)} s</span><span>${row.clipped_frames} 削波帧</span></div>
    ${row.failed_rules.length?`<ul>${row.failed_rules.map(reason=>`<li>${h(reason)}</li>`).join('')}</ul>`:''}
    <details><summary>文件校验</summary><dl><dt>登记 SHA-256</dt><dd>${h(row.expected_digest)}</dd><dt>实测 SHA-256</dt><dd>${h(row.measured_digest)}</dd></dl></details>
    ${reviewer&&row.stage==='queued'?`<form data-operation="verify" data-id="${row.id}"><button>应用入档质检规则</button><p role="status"></p></form>`:''}</article>`).join('')||empty('工序卡签发后可登记首个待验派生件。')
}
